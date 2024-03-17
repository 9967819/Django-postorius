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

import logging
from urllib.error import HTTPError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from django_mailman3.lib.mailman import get_mailman_client
from django_mailman3.models import MailDomain
from django_mailman3.signals import domain_created, domain_deleted

from postorius.auth.decorators import superuser_required
from postorius.forms.domain_forms import (
    DomainEditForm,
    DomainForm,
    DomainOwnerForm,
)
from postorius.models import Domain, Mailman404Error


log = logging.getLogger(__name__)


@login_required
@superuser_required
def domain_index(request):
    existing_domains = Domain.objects.all()
    for domain in existing_domains:
        try:
            web_host = MailDomain.objects.get(mail_domain=domain.mail_host)
        except MailDomain.DoesNotExist:
            site = Site.objects.get_current(request)
            web_host = MailDomain.objects.create(
                site=site, mail_domain=domain.mail_host
            )
        domain.site = web_host.site
    return render(
        request,
        'postorius/domain/index.html',
        {
            'domains': existing_domains,
        },
    )


@login_required
@superuser_required
def domain_new(request):
    form_initial = {'site': Site.objects.get_current(request)}
    if request.method == 'POST':
        form = DomainForm(request.POST, initial=form_initial)
        if form.is_valid():
            domain = Domain(
                mail_host=form.cleaned_data['mail_host'],
                description=form.cleaned_data['description'],
                alias_domain=form.cleaned_data['alias_domain'],
                owner=request.user.email,
            )
            try:
                domain.save()
            except HTTPError as e:
                form.add_error('mail_host', e.reason)
            else:
                messages.success(request, _('New Domain registered'))
                MailDomain.objects.get_or_create(
                    site=form.cleaned_data['site'],
                    mail_domain=form.cleaned_data['mail_host'],
                )
                domain_created.send(
                    sender=Domain, mail_host=form.cleaned_data['mail_host']
                )
                return redirect('domain_index')
    else:
        form = DomainForm(initial=form_initial)
    return render(request, 'postorius/domain/new.html', {'form': form})


@login_required
@superuser_required
def domain_edit(request, domain):
    try:
        domain_obj = Domain.objects.get(mail_host=domain)
    except Mailman404Error:
        raise Http404('Domain does not exist')
    if request.method == 'POST':
        form = DomainEditForm(request.POST)
        if form.is_valid():
            domain_obj.description = form.cleaned_data['description']
            domain_obj.alias_domain = form.cleaned_data['alias_domain']
            try:
                web_host = MailDomain.objects.get(mail_domain=domain)
            except MailDomain.DoesNotExist:
                web_host = MailDomain.objects.create(
                    site=form.cleaned_data['site'], mail_domain=domain
                )
            else:
                web_host.site = form.cleaned_data['site']
                web_host.save()
            try:
                domain_obj.save()
            except HTTPError as e:
                messages.error(request, e)
                return redirect('domain_edit', domain=domain)
            else:
                messages.success(request, _('Domain %s updated') % domain)
                return redirect('domain_index')
        else:
            messages.error(request, _('Please check the errors below'))
    else:
        form_initial = {
            'description': domain_obj.description,
            'alias_domain': domain_obj.alias_domain,
            'site': MailDomain.objects.get(mail_domain=domain).site,
        }
        form = DomainEditForm(initial=form_initial)

    return render(
        request, 'postorius/domain/edit.html', {'domain': domain, 'form': form}
    )


@login_required
@superuser_required
def domain_delete(request, domain):
    """Deletes a domain but asks for confirmation first."""
    domain_obj = Domain.objects.get(mail_host=domain)
    if request.method == 'POST':
        try:
            domain_obj.delete()
            MailDomain.objects.filter(mail_domain=domain).delete()
            messages.success(
                request, _('The domain %s has been deleted.' % domain)
            )
            domain_deleted.send(sender=Domain, mail_host=domain)
            return redirect('domain_index')
        except HTTPError as e:
            messages.error(
                request, _('The domain could not be deleted: %s' % e.msg)
            )
            return redirect('domain_index')
    domain_lists_page = domain_obj.get_list_page(count=10)
    return render(
        request,
        'postorius/domain/confirm_delete.html',
        {'domain': domain_obj, 'lists': domain_lists_page},
    )


@login_required
@superuser_required
def domain_owners(request, domain):
    domain_obj = Domain.objects.get(mail_host=domain)
    if request.method == 'POST':
        form = DomainOwnerForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            domain_obj.add_owner(email)
            messages.success(
                request,
                _('Added {} as an owner for {}').format(
                    email, domain_obj.mail_host
                ),
            )
            return redirect('domain_index')
    else:
        form = DomainOwnerForm()
    return render(
        request,
        'postorius/domain/owners.html',
        {'domain': domain_obj, 'form': form},
    )


@require_POST
@login_required
@superuser_required
def remove_owners(request, domain, user_id):
    domain_obj = Domain.objects.get(mail_host=domain)
    # Since there is no way to remove one single owner, we do the only possible
    # thing, remove all owners and add the rest back.
    client = get_mailman_client()
    try:
        remove_email = client.get_user(user_id).addresses[0].email
        all_owners_emails = [
            owner.addresses[0].email for owner in domain_obj.owners
        ]
    except (KeyError, ValueError) as e:
        # We get KeyError if the user has no address due to [0].
        log.error('Unable to delete owner: %s', str(e))
        raise Http404(str(e))
    if remove_email in all_owners_emails:
        all_owners_emails.remove(remove_email)
    else:
        messages.error(
            _('{} is not an owner for {}').format(
                remove_email, domain_obj.mail_host
            )
        )
        return redirect('domain_index')
    domain_obj.remove_all_owners()
    for owner in all_owners_emails:
        domain_obj.add_owner(owner)
    messages.success(
        request,
        _('Removed {} as an owner for {}').format(
            remove_email, domain_obj.mail_host
        ),
    )
    return redirect('domain_index')
