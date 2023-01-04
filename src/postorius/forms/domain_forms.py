# -*- coding: utf-8 -*-
# Copyright (C) 2012-2023 by the Free Software Foundation, Inc.
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


from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from postorius.forms.fields import SiteModelChoiceField


def _get_web_host_help():
    # Using a function is necessary, otherwise reverse() will be called before
    # URLConfs are loaded.
    return _(
        'The domain from which you want the web UI to be served from. '
        'This can be same or different from the Mail Host. '
        'You can edit the list of available web hosts <a href="%s">here</a>.'
    ) % reverse('admin:sites_site_changelist')


class DomainForm(forms.Form):
    """
    Form to add a domain.
    """

    mail_host = forms.CharField(
        label=_('Mail Host'),
        error_messages={
            'required': _('Please enter a domain name'),
            'invalid': _('Please enter a valid domain name.'),
        },
        required=True,
        help_text=_(
            'The domain for your mailing lists. For example when you want '
            'lists like testing@example.com, enter example.com here.'
        ),
    )
    description = forms.CharField(label=_('Description'), required=False)
    alias_domain = forms.CharField(
        label=_('Alias Domain'),
        error_messages={
            'invalid': _('Please enter a valid domain name or nothing.')
        },
        required=False,
        help_text=_('Normally empty.  Used only for unusual Postfix configs.'),
    )
    site = SiteModelChoiceField(
        label=_('Web Host'),
        error_messages={
            'required': _('Please enter a domain name'),
            'invalid': _('Please enter a valid domain name.'),
        },
        required=True,
        queryset=Site.objects.order_by('name').all(),
        initial=lambda: Site.objects.get_current(),
        help_text=_get_web_host_help,
    )

    def clean_mail_host(self):
        mail_host = self.cleaned_data['mail_host']
        try:
            validate_email('mail@' + mail_host)
        except ValidationError:
            raise forms.ValidationError(_('Please enter a valid domain name'))
        return mail_host

    def clean_alias_domain(self):
        alias_domain = self.cleaned_data['alias_domain']
        if alias_domain != '':
            try:
                validate_email('mail@' + alias_domain)
            except ValidationError:
                raise forms.ValidationError(
                    _('Please enter a valid domain name or nothing.')
                )
        return alias_domain


class DomainEditForm(DomainForm):
    """
    Form to edit domains
    separte from the DomainForm, so that the mail_host can't be changed.
    """

    mail_host = None


class DomainOwnerForm(forms.Form):
    """Form to add a owner for a domain."""

    email = forms.EmailField(
        label=_("Owner's Email"),
        required=True,
    )
