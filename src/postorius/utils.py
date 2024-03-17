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

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress
from django_mailman3.lib import mailman


logger = logging.getLogger(__name__)


def render_api_error(request):
    """Renders an error template.
    Use if MailmanApiError is catched.
    """
    return render(
        request,
        'postorius/errors/generic.html',
        {
            'error': _(
                'Mailman REST API not available. Please start Mailman core.'
            )
        },  # noqa: E501
        status=503,
    )


def render_client_error(request, error):
    return render(
        request,
        'postorius/errors/generic.html',
        {'error': str(error)},
        status=error.code,
    )


def get_mailman_client():
    """A proxy for django_mailman3.lib.mailman.get_mailman_client."""
    return mailman.get_mailman_client()


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


def get_django_user(mm_user, addresses=None):
    """Given a Mailman user, return a Django User if One exists.

    There is no direct way to fetch that, but we can iterate on Users's Email
    Addresses and see if Django knows any one of them. If we find one, just
    return the user associated with that Address.

    Ideally, the email addresses should be *all* synchronized with Core, but
    just in case they aren't, we iterate over all the addresses.

    :param mm_user: Mailman User object.
    :param addresses: user.addresses for the above mailman objects. It is
        passed in just so that we can avoid an API call to Core to get them. It
        is optional since we can just fetch them here if need be.
    :returns: Django user if found, None otherwise.
    """
    if addresses is None:
        addresses = mm_user.addresses or []
    django_email = None
    for addr in addresses:
        try:
            django_email = EmailAddress.objects.get(email=addr.email)
        except EmailAddress.DoesNotExist:
            continue
        else:
            break

    if django_email is None:
        # If none of the user's emails are registered in Django, that means
        # they don't have a user account.
        return None
    return django_email.user


def filter_memberships_by_roles(memberships, roles):
    """Given a list of roles, filter the memberships with those roles.

    :param memberships: A list of Member objects.
    :type memberships: List[mailmanclient.restobjects.Member]
    :param roles: A list of roles.
    :type roles: List[str]
    :returns: A list of memberships filtered by roles.
    :rtype: List[mailmanclient.restobjects.Member]
    """
    return [member for member in memberships if member.role in roles]


LANGUAGES = [
    ('ar', 'Arabic'),
    ('ast', 'Asturian'),
    ('bg', 'Bulgarian'),
    ('ca', 'Catalan'),
    ('zh_CN', 'Chinese'),
    ('zh_TW', 'Chinese (Taiwan)'),
    ('hr', 'Croatian'),
    ('cs', 'Czech'),
    ('da', 'Danish'),
    ('nl', 'Dutch'),
    ('en', 'English (USA)'),
    ('et', 'Estonian'),
    ('eu', 'Euskara'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('gl', 'Galician'),
    ('de', 'German'),
    ('el', 'Greek'),
    ('he', 'Hebrew'),
    ('hu', 'Hungarian'),
    ('ia', 'Interlingua'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('lt', 'Lithuanian'),
    ('no', 'Norwegian'),
    ('pl', 'Polish'),
    ('pt', 'Portuguese'),
    ('pt_BR', 'Portuguese (Brazil)'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('sr', 'Serbian'),
    ('sk', 'Slovak'),
    ('sl', 'Slovenian'),
    ('es', 'Spanish'),
    ('sv', 'Swedish'),
    ('tr', 'Turkish'),
    ('uk', 'Ukrainian'),
    ('vi', 'Vietnamese'),
]
