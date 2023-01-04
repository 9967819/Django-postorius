# -*- coding: utf-8 -*-
# Copyright (C) 2018-2023 by the Free Software Foundation, Inc.
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
#

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_safe
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from postorius.auth.mixins import DomainOwnerMixin, ListOwnerMixin
from postorius.forms.list_forms import TemplateUpdateForm
from postorius.models import Domain, EmailTemplate, List


def _clean_with_no_strip(field, data):
    """Clean Django's CharField field without strip=True.

    :param field: Instance of the Charfield.
    :param data: The un-cleaned data from the form.
    :returns: Cleaned data.
    """
    field.strip = False
    return field.clean(data)


class ListContextMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['list'] = List.objects.get_or_404(
            fqdn_listname=self.kwargs['list_id']
        )
        return context


class ListTemplateIndexView(ListOwnerMixin, ListContextMixin, ListView):

    model = EmailTemplate
    template_name = 'postorius/lists/template_list.html'

    def get_queryset(self):
        return EmailTemplate.objects.filter(identifier=self.kwargs['list_id'])


class ListTemplateCreateView(ListOwnerMixin, ListContextMixin, CreateView):

    template_name = 'postorius/lists/template_add.html'
    model = EmailTemplate
    fields = ['name', 'data']

    def get_success_url(self):
        return reverse('list_template_list', args=(self.kwargs['list_id'],))

    def form_valid(self, form):
        formdata = form.cleaned_data
        formdata['data'] = _clean_with_no_strip(
            form.fields['data'], form.data['data']
        )
        formdata['identifier'] = self.kwargs['list_id']
        formdata['context'] = 'list'
        email_template = EmailTemplate(**formdata)
        # Try to save the model. Some of the unique constraints that we have
        # depend on the mailing_list attribute added above. So, even though
        # we check for form validity, the save can fail.
        try:
            email_template.save()
        except IntegrityError as e:
            form.add_error('name', str(e))
            form.add_error(
                'name',
                'You already have this template set. '
                'Use edit instead of creating a new one.',
            )
            return self.form_invalid(form)
        return redirect(self.get_success_url())


class ListTemplateUpdateView(ListOwnerMixin, ListContextMixin, UpdateView):

    template_name = 'postorius/lists/template_update.html'
    model = EmailTemplate
    form_class = TemplateUpdateForm

    def get_success_url(self):
        return reverse('list_template_list', args=(self.kwargs['list_id'],))


class ListTemplateDeleteView(ListOwnerMixin, ListContextMixin, DeleteView):

    template_name = 'postorius/lists/template_delete.html'
    model = EmailTemplate

    def get_success_url(self):
        return reverse('list_template_list', args=(self.kwargs['list_id'],))


class DomainContextMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['domain'] = Domain.objects.get_or_404(
            mail_host=self.kwargs['domain']
        )
        return context


class DomainTemplateIndexView(DomainOwnerMixin, DomainContextMixin, ListView):

    model = EmailTemplate
    template_name = 'postorius/domain/template_index.html'
    header = 'Index'

    def get_queryset(self):
        return EmailTemplate.objects.filter(identifier=self.kwargs['domain'])


class DomainTemplateCreateView(
    DomainOwnerMixin, DomainContextMixin, CreateView
):

    model = EmailTemplate
    template_name = 'postorius/domain/template_add.html'
    fields = ['name', 'data']
    header = 'New Template'

    def get_success_url(self):
        return reverse('domain_template_list', args=(self.kwargs['domain'],))

    def form_valid(self, form):
        formdata = form.cleaned_data
        formdata['data'] = _clean_with_no_strip(
            form.fields['data'], form.data['data']
        )
        formdata['identifier'] = self.kwargs['domain']
        formdata['context'] = 'domain'
        template = EmailTemplate(**formdata)
        # Try to save the model. Some of the unique constraints that we have
        # depend on the mailing_list attribute added above. So, even though we
        # check for form validity, the save can fail.
        try:
            template.save()
        except IntegrityError as e:
            form.add_error('name', str(e))
            form.add_error(
                'name',
                'You already have this template set.'
                'Use edit instead of creating a new one.',
            )
            return self.form_invalid(form)
        return redirect(self.get_success_url())


class DomainTemplateUpdateView(
    DomainOwnerMixin, DomainContextMixin, UpdateView
):

    model = EmailTemplate
    template_name = 'postorius/domain/template_add.html'
    form_class = TemplateUpdateForm
    header = 'Edit Template'

    def get_success_url(self):
        return reverse('domain_template_list', args=(self.kwargs['domain'],))


class DomainTemplateDeleteView(
    DomainOwnerMixin, DomainContextMixin, DeleteView
):

    template_name = 'postorius/domain/template_delete.html'
    model = EmailTemplate

    def get_success_url(self):
        return reverse('domain_template_list', args=(self.kwargs['domain'],))


@require_safe
def get_template_data(request, context, identifier, name):
    # At this point, the request should be authenticated and it's method should
    # be GET. We just need to find the correct template and return it's
    # content, if it exists, return a 404 otherwise.
    if context not in ('list', 'domain'):
        return HttpResponseBadRequest(
            'context should be either "list" or "domain"'
        )
    data = dict(name=name, identifier=identifier, context=context)
    # Depending on the context, populate the right identifier.
    try:
        template = EmailTemplate.objects.get(**data)
    except EmailTemplate.DoesNotExist:
        raise Http404('Template is not defined.')
    except MultipleObjectsReturned:
        raise HttpResponseBadRequest('Multiple Templates exist')

    content_type = 'text/plain'
    if settings.DEFAULT_CHARSET:
        content_type += '; charset=' + settings.DEFAULT_CHARSET
    return HttpResponse(template.data, content_type=content_type)
