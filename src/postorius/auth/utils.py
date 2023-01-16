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

"""
Authentication and authorization-related utilities.
"""

from allauth.account.models import EmailAddress

from postorius.models import Domain, List


ALL_ROSTER = ['owner', 'moderator', 'member', 'nomember']


def user_is_in_list_roster(user, mailing_list, roster):
    """Checks if a user is in a MailingList roster.

    :param user: User to check access permissions for.
    :type user: django.contrib.auth.model.User
    :param mailing_list: MailingList to check permissions for.
    :type mailing_list: postorius.models.List
    :param roster: Access permissions required.
    :type roster: str
    """
    if not user.is_authenticated:
        return False
    addresses = set(
        email.lower()
        for email in EmailAddress.objects.filter(
            user=user, verified=True
        ).values_list('email', flat=True)
    )
    if roster not in ALL_ROSTER:
        raise ValueError(f'{roster} is a valid List Roster.')

    roster_addresses = set(
        [
            member.email.lower()
            for member in mailing_list.get_roster(roster, fields=['email'])
        ]
    )
    if addresses & roster_addresses:
        return True  # At least one address is in the roster
    return False


def set_list_access_props(user, mlist, owner=True, moderator=True):
    """Update user's access permissions of a MailingList.

    :param user: The user to check permissions for.
    :type user: django.contrib.auth.model.User
    :param mlist: MailingList to check permissions for.
    :type mlist: postorius.models.List
    :param owner: Set is_list_owner.
    :type owner: bool
    :param moderator: Set is_list_moderator.
    :type moderator: bool
    """
    # If given a mailinglist id, get the List object instead.
    if isinstance(mlist, str):
        mlist = List.objects.get_or_404(mlist)
    # If not already set, check if the user is in list ownership roster.
    if (not hasattr(user, 'is_list_owner')) and owner:
        user.is_list_owner = user_is_in_list_roster(user, mlist, 'owner')
    # Calculate combined status for superusers and list owners
    user.is_poweruser = user.is_superuser or user.is_list_owner
    # If not already set, check if the user is in list moderator roster.
    if not hasattr(user, 'is_list_moderator') and moderator:
        user.is_list_moderator = user_is_in_list_roster(
            user, mlist, 'moderator'
        )
    if not hasattr(user, 'show_list_members'):
        member_roster_visibility = mlist.settings['member_roster_visibility']
        if user.is_superuser or user.is_list_owner:
            user.show_list_members = True
        else:
            is_list_moderator = (
                user.is_list_moderator
                if hasattr(user, 'is_list_moderator')
                else user_is_in_list_roster(user, mlist, 'moderator')
            )
            user.show_list_members = (
                member_roster_visibility == 'moderators' and is_list_moderator
            ) or (
                member_roster_visibility == 'members'
                and (
                    is_list_moderator
                    or user_is_in_list_roster(user, mlist, 'member')
                )
            )


def set_domain_access_props(user, domain):
    """Update user's access permissions for a domain.

    :param user: The user to check permissions for.
    :type user: django.contrib.auth.model.User
    :param domain: Domain to check permissions for.
    :type domain: postorius.models.Domain
    """
    # TODO: This is very slow as it involves first iterating over every domain
    # owner and then each of their addresses. Create an API in Core to
    # facilitate this.
    if isinstance(domain, str):
        domain = Domain.objects.get_or_404(domain)
    owner_addresses = []
    for owner in domain.owners:
        owner_addresses.extend(owner.addresses)
    owner_addresses = set([each.email for each in owner_addresses])
    user_addresses = set(
        EmailAddress.objects.filter(user=user, verified=True).values_list(
            'email', flat=True
        )
    )
    user.is_domain_owner = owner_addresses & user_addresses
