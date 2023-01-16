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


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from postorius.auth.utils import set_domain_access_props, set_list_access_props
from postorius.models import List


class ListOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to allow access to only List owners."""

    raise_exception = True

    def test_func(self):
        user = self.request.user
        mlist_id = self.kwargs['list_id']
        mlist = List.objects.get_or_404(mlist_id)
        if user.is_superuser:
            return True
        set_list_access_props(user, mlist, moderator=False)
        return user.is_list_owner


class ListModeratorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to allow access to only List Moderators."""

    raise_exception = True

    def test_func(self):
        user = self.request.user
        mlist_id = self.kwargs['list_id']
        if user.is_superuser:
            return True
        set_list_access_props(user, mlist_id)
        return user.is_list_owner or user.is_list_moderator


class UserShowListMembersMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to allow listing of members depending on list settings and
    user role."""

    raise_exception = True

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        mlist_id = self.kwargs['list_id']
        set_list_access_props(user, mlist_id)
        return user.show_list_members


class DomainOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to allow access to only Domain Owner."""

    raise_exception = True

    def test_func(self):
        user = self.request.user
        domain = self.kwargs['domain']
        if user.is_superuser:
            return True
        set_domain_access_props(user, domain)
        return user.is_domain_owner


class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to allow access to only Django Superusers."""

    def test_func(self):
        return self.request.user.is_superuser
