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
from enum import Enum
from urllib.error import HTTPError
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.http import Http404
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from mailmanclient import MailmanConnectionError

from postorius.template_list import TEMPLATES_LIST
from postorius.utils import LANGUAGES, get_mailman_client


logger = logging.getLogger(__name__)

_email_template_help_text = _(
    'Note: Do not add any secret content in templates as they are '
    'publicly accessible.\n'
    'You can use these variables in the templates. \n'
    '$hyperkitty_url: Permalink to archived message in Hyperkitty '
    ' - only in list:member:regular:footer and list:member:regular:header\n'
    '$listname: Name of the Mailing List e.g. ant@example.com \n'
    '$list_id: The List-ID header e.g. ant.example.com \n'
    '$display_name: Display name of the mailing list e.g. Ant \n'
    '$short_listname: Local part of the listname e.g. ant \n'
    '$domain: The domain part of the listname e.g. example.com \n'
    "$description: The mailing list's short description text \n"
    "$info: The mailing list's longer descriptive text \n"
    '$request_email: The email address for -request address \n'
    '$owner_email: The email address for -owner address \n'
    '$site_email: The email address to reach the owners of the site \n'
    "$language: The two letter language code for list's preferred language "
    'e.g. fr, en, de \n'
    'Some templates accept additional variables. See '
    '<a href="https://docs.mailman3.org/projects/mailman/en/latest/src/mailman/rest/docs/templates.html#templated-texts">this doc</a> \n'  # noqa: E501
)


class SubscriptionMode(Enum):
    """Valid values for Member.subscription_mode"""

    as_address = 'as_address'
    as_user = 'as_user'


class MemberRole(Enum):
    """List of roles a Member resource can have.

    The primary purpose of this enum right now is only to add the
    role values to translations. At some point, we want to use MemberRole.owner
    in all the places we are using the literal role as string.
    """

    owner = _('owner')
    member = _('member')
    nonmember = _('nonmember')
    moderator = _('moderator')


class MailmanApiError(Exception):
    """Raised if the API is not available."""

    pass


class Mailman404Error(Exception):
    """Proxy exception. Raised if the API returns 404."""

    pass


class MailmanRestManager(object):
    """Manager class to give a model class CRUD access to the API.
    Returns objects (or lists of objects) retrieved from the API.
    """

    def __init__(self, resource_name, resource_name_plural, cls_name=None):
        self.resource_name = resource_name
        self.resource_name_plural = resource_name_plural

    def all(self):
        try:
            return getattr(get_mailman_client(), self.resource_name_plural)
        except AttributeError:
            raise MailmanApiError
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def get(self, *args, **kwargs):
        try:
            method = getattr(get_mailman_client(), 'get_' + self.resource_name)
            return method(*args, **kwargs)
        except AttributeError as e:
            raise MailmanApiError(e)
        except HTTPError as e:
            if e.code == 404:
                raise Mailman404Error('Mailman resource could not be found.')
            else:
                raise
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def get_or_404(self, *args, **kwargs):
        """Similar to `self.get` but raises standard Django 404 error."""
        try:
            return self.get(*args, **kwargs)
        except Mailman404Error:
            raise Http404
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def create(self, *args, **kwargs):
        try:
            method = getattr(
                get_mailman_client(), 'create_' + self.resource_name
            )
            return method(*args, **kwargs)
        except AttributeError as e:
            raise MailmanApiError(e)
        except HTTPError as e:
            if e.code == 409:
                raise MailmanApiError
            else:
                raise
        except MailmanConnectionError:
            raise MailmanApiError

    def delete(self):
        """Not implemented since the objects returned from the API
        have a `delete` method of their own.
        """
        pass


class MailmanListManager(MailmanRestManager):
    def __init__(self):
        super(MailmanListManager, self).__init__('list', 'lists')

    def all(self, advertised=False):
        try:
            method = getattr(
                get_mailman_client(), 'get_' + self.resource_name_plural
            )
            return method(advertised=advertised)
        except AttributeError:
            raise MailmanApiError
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def by_mail_host(self, mail_host, advertised=False):
        objects = self.all(advertised)
        host_objects = []
        for obj in objects:
            if obj.mail_host == mail_host:
                host_objects.append(obj)
        return host_objects


class MailmanUserManager(MailmanRestManager):
    def __init__(self):
        super(MailmanUserManager, self).__init__('user', 'users')


class MailmanRestModel(object):
    """Simple REST Model class to make REST API calls Django style."""

    MailmanApiError = MailmanApiError
    DoesNotExist = Mailman404Error

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def save(self):
        """Proxy function for `objects.create`.
        (REST API uses `create`, while Django uses `save`.)
        """
        self.objects.create(*self.args, **self.kwargs)


class Domain(MailmanRestModel):
    """Domain model class."""

    objects = MailmanRestManager('domain', 'domains')


class List(MailmanRestModel):
    """List model class."""

    objects = MailmanListManager()


class MailmanUser(MailmanRestModel):
    """MailmanUser model class."""

    objects = MailmanUserManager()


class Member(MailmanRestModel):
    """Member model class."""

    objects = MailmanRestManager('member', 'members')


class Style(MailmanRestModel):
    """ """

    objects = MailmanRestManager(None, 'styles')


TEMPLATE_CONTEXT_CHOICES = (
    ('site', 'Site Wide'),
    ('domain', 'Domain Wide'),
    ('list', 'MailingList Wide'),
)


class EmailTemplate(models.Model):
    """A Template represents contents of partial or complete emails sent out by
    Mailman Core on various events or when an action is required. Headers and
    Footers on emails for decorations are also repsented as templates.
    """

    # Ease differentiating the various Mailman templates by providing the
    # template file's name (key) prepended in square brackets to the
    # template's purpose (value).
    _templates_list_choices = [
        (t[0], format_lazy('[{key}] - {value}', key=t[0], value=t[1]))
        for t in TEMPLATES_LIST
    ]

    name = models.CharField(
        max_length=100,
        choices=_templates_list_choices,
        help_text=_('Choose the template you want to customize.'),
    )
    data = models.TextField(
        help_text=_email_template_help_text,
        blank=True,
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGES,
        help_text=_(
            "Language for the template, this should be the list's preferred language."  # noqa: E501
        ),
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    context = models.CharField(max_length=50, choices=TEMPLATE_CONTEXT_CHOICES)
    identifier = models.CharField(blank=True, max_length=100)

    class Meta:
        unique_together = ('name', 'identifier', 'language')

    def __str__(self):
        return '<EmailTemplate {0} for {1}>'.format(self.name, self.context)

    @property
    def description(self):
        """Return the long description of template that is human readable."""
        return dict(TEMPLATES_LIST)[self.name]

    @property
    def api_url(self):
        """API url is the remote url that Core can use to fetch templates"""
        base_url = getattr(settings, 'POSTORIUS_TEMPLATE_BASE_URL', None)
        if not base_url:
            raise ImproperlyConfigured(
                'Setting "POSTORIUS_TEMPLATE_BASE_URL" is not configured.'
            )
        resource_url = reverse(
            'rest_template',
            kwargs=dict(
                context=self.context,
                identifier=self.identifier,
                name=self.name,
            ),
        )
        return urljoin(base_url, resource_url)

    def _get_context_obj(self):
        if self.context == 'list':
            obj = List.objects.get_or_404(fqdn_listname=self.identifier)
        elif self.context == 'domain':
            obj = Domain.objects.get_or_404(mail_host=self.identifier)
        elif self.context == 'site':
            obj = get_mailman_client()
        else:
            obj = None
        return obj

    def _update_core(self, deleted=False):
        obj = self._get_context_obj()
        if obj is None:
            return

        if deleted:
            # POST'ing an empty string will delete this record in Core.
            api_url = ''
        else:
            # Use the API endpoint of self that Core can use to fetch this.
            api_url = self.api_url
        obj.set_template(self.name, api_url)


@receiver(post_save, sender=EmailTemplate)
def update_core_post_update(sender, **kwargs):
    kwargs['instance']._update_core()


@receiver(post_delete, sender=EmailTemplate)
def update_core_post_delete(sender, **kwargs):
    kwargs['instance']._update_core(deleted=True)
