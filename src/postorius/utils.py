# -*- coding: utf-8 -*-
# Copyright (C) 1998-2021 by the Free Software Foundation, Inc.
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

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext as _

from allauth.account.models import EmailAddress
from mailmanclient import Client


logger = logging.getLogger(__name__)


def render_api_error(request):
    """Renders an error template.
    Use if MailmanApiError is catched.
    """
    return render(request, 'postorius/errors/generic.html',
                  {'error': _('Mailman REST API not available. Please start Mailman core.')},   # noqa: E501
                  status=503)


def render_client_error(request, error):
    return render(request, 'postorius/errors/generic.html',
                  {'error': str(error)},
                  status=error.code)


def get_mailman_client():
    # easier to patch during unit tests
    client = Client(
        '%s/3.1' %
        settings.MAILMAN_REST_API_URL,
        settings.MAILMAN_REST_API_USER,
        settings.MAILMAN_REST_API_PASS)
    return client


def with_empty_choice(choices):
    """Add an empty Choice for unset values in dropdown."""
    return [(None, '-----')] + list(choices)


def set_preferred(user, mm_user):
    """Set preferred address in Mailman Core.

    :param user: The Django user mode to set preferred address.
    :param mm_user: The Mailman User object to set preferred address for.
    """
    client = get_mailman_client()
    primary_email = EmailAddress.objects.get_primary(user)
    if primary_email is not None and primary_email.verified:
        # First, make sure that the email address is verified in Core,
        # otherwise, we can't set it as a primary address.
        addr = client.get_address(primary_email.email)
        if not addr.verified_on:
            addr.verify()
        mm_user.preferred_address = primary_email.email
        return primary_email.email
    return None


def get_member_or_nonmember(mlist, email):
    """Return either a Member or a Non-member with `email` in mlist.

    :param mlist: MailingList object to get membership for.
    :param email: Email address of the member or nonmember.
    :returns: Member if found otherwise None.
    """
    try:
        member = mlist.get_member(email)
    except ValueError:
        # Not a Member, try getting non-member.
        try:
            member = mlist.get_nonmember(email)
        except ValueError:
            member = None
    return member


LANGUAGES = (
    ('ar', 'Arabic'),
    ('ast', 'Asturian'),
    ('ca', 'Catalan'),
    ('cs', 'Czech'),
    ('da', 'Danish'),
    ('de', 'German'),
    ('el', 'Greek'),
    ('es', 'Spanish'),
    ('et', 'Estonian'),
    ('eu', 'Euskara'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('gl', 'Galician'),
    ('he', 'Hebrew'),
    ('hr', 'Croatian'),
    ('hu', 'Hungarian'),
    ('ia', 'Interlingua'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('lt', 'Lithuanian'),
    ('nl', 'Dutch'),
    ('no', 'Norwegian'),
    ('pl', 'Polish'),
    ('pt', 'Protuguese'),
    ('pt_BR', 'Protuguese (Brazil)'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('sk', 'Slovak'),
    ('sl', 'Slovenian'),
    ('sr', 'Serbian'),
    ('sv', 'Swedish'),
    ('tr', 'Turkish'),
    ('uk', 'Ukrainian'),
    ('vi', 'Vietnamese'),
    ('zh_CN', 'Chinese'),
    ('zh_TW', 'Chinese (Taiwan)'),
    ('en', 'English (USA)'),
)
