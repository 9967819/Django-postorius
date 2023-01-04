# -*- coding: utf-8 -*-
# Copyright (C) 2021-2023 by the Free Software Foundation, Inc.
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
from django import template


register = template.Library()


@register.filter
def user_display(user):
    """Return a User's formatted display_name and email."""
    addresses = user.addresses
    if user.display_name is not None and user.display_name != '':
        if len(addresses) > 0:
            # We can't use email.utils.formataddr because it will return an
            # RFC2047 encoded display name part for non-ascii.  We don't need
            # to decide about quoting the display name as we aren't using this
            # as an RFC5322 address.
            return '{} <{}>'.format(user.display_name, addresses[0].email)
        else:
            return user.display_name
    if len(addresses) > 0:
        return addresses[0].email
    return 'None'
