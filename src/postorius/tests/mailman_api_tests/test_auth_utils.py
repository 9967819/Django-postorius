# -*- coding: utf-8 -*-
# Copyright (C) 2020-2023 by the Free Software Foundation, Inc.
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


from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from postorius.auth.utils import user_is_in_list_roster
from postorius.tests.utils import ViewTestCase


class AuthTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.mlist = self.domain.create_list('authlist')
        self.user1 = User.objects.create_user(
            'aperson', 'aperson@example.com', 'pass'
        )
        EmailAddress.objects.create(
            user=self.user1, email=self.user1.email, verified=True
        )
        self.user2 = User.objects.create_user(
            'bperson', 'BPERSON@example.com', 'pass'
        )
        EmailAddress.objects.create(
            user=self.user2, email=self.user2.email, verified=True
        )
        self.mlist.subscribe(
            'APERSON@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        self.mlist.subscribe(
            'bperson@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )

    def test_user_in_roster_case_sensitivity(self):
        # Test that if Core stores the email adddress with Upper case letters
        # and Postorius stores it in lower case, the matching works.
        self.assertTrue(
            user_is_in_list_roster(self.user1, self.mlist, 'member')
        )

        self.assertTrue(
            user_is_in_list_roster(self.user2, self.mlist, 'member')
        )
