# -*- coding: utf-8 -*-
# Copyright (C) 1998-2023 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.


from urllib.error import HTTPError

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from django_mailman3.lib.mailman import get_mailman_client
from django_mailman3.lib.paginator import paginate

from postorius.auth.utils import set_list_access_props
from postorius.forms import AddBanForm
from postorius.models import List


class MailmanClientMixin(object):

    """Adds a mailmanclient.Client instance."""

    def client(self):
        if getattr(self, '_client', None) is None:
            self._client = get_mailman_client()
        return self._client


class MailingListView(TemplateView, MailmanClientMixin):

    """A generic view for everything based on a mailman.client
    list object.

    Sets self.mailing_list to list object if list_id is in **kwargs.
    """

    def get(self, request, *args, **kwargs):
        # This should be overridden by the subclass.
        return HttpResponse(status=405)

    def post(self, request, *args, **kwargs):
        # This should be overridden by the subclass.
        return HttpResponse(status=405)

    def _get_list(self, list_id, page):
        return List.objects.get_or_404(fqdn_listname=list_id)

    def dispatch(self, request, *args, **kwargs):
        # get the list object.
        if 'list_id' in kwargs:
            self.mailing_list = self._get_list(
                kwargs['list_id'], int(kwargs.get('page', 1))
            )
            set_list_access_props(request.user, self.mailing_list)
        # set the template
        if 'template' in kwargs:
            self.template = kwargs['template']
        return super(MailingListView, self).dispatch(request, *args, **kwargs)

    def _has_pending_unsub_req(self, email):
        """Check if there is a pending unsubscription request for email."""
        for req in self.mailing_list.get_requests(
            token_owner='moderator', request_type='unsubscription'
        ):
            if req.get('email') == email:
                return req
        return False


def bans_view(request, template, list_id=None):
    """Ban or unban email addresses.

    This is a reusable view which works for both global and list specific bans.
    Whether a MailingList ban is updated or a Global one depends on list_id
    being passed in.

    :list_id: MailingList Id if this is a List ban, None otherwise.

    """
    if list_id:
        m_list = List.objects.get_or_404(fqdn_listname=list_id)
        url = reverse('list_bans', args=[list_id])
        ban_list = m_list.bans
    else:
        ban_list = get_mailman_client().bans
        url = reverse('global_bans')
        m_list = None

    # Process form submission.
    if request.method == 'POST':
        if 'add' in request.POST:
            addban_form = AddBanForm(request.POST)
            if addban_form.is_valid():
                try:
                    ban_list.add(addban_form.cleaned_data['email'])
                    messages.success(
                        request,
                        _('The email {} has been banned.').format(
                            addban_form.cleaned_data['email']
                        ),
                    )
                except HTTPError as e:
                    messages.error(
                        request, _('An error occurred: %s') % e.reason
                    )
                except ValueError as e:
                    messages.error(request, _('Invalid data: %s') % e)
                return redirect(url)
        elif 'del' in request.POST:
            try:
                ban_list.remove(request.POST['email'])
                messages.success(
                    request,
                    _('The email {} has been un-banned').format(
                        request.POST['email']
                    ),
                )
            except HTTPError as e:
                messages.error(request, _('An error occurred: %s') % e.reason)
            except ValueError as e:
                messages.error(request, _('Invalid data: %s') % e)
            return redirect(url)
    else:
        addban_form = AddBanForm(initial=request.GET)
    banned_addresses = paginate(
        list(ban_list), request.GET.get('page'), request.GET.get('count')
    )

    context = {
        'addban_form': addban_form,
        'banned_addresses': banned_addresses,
    }

    if list_id:
        context['list'] = m_list

    return render(request, template, context)
