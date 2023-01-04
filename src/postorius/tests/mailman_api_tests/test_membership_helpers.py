# -*- coding: utf-8 -*-
# Copyright (C) 2017-2023 by the Free Software Foundation, Inc.
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
from mailmanclient import MailingList

from postorius.models import Mailman404Error
from postorius.templatetags.membership_helpers import (
    get_list,
    user_is_list_moderator,
    user_is_list_owner,
)
from postorius.tests.utils import ViewTestCase


class TestMembershipHelpers(ViewTestCase):
    def setUp(self):
        super(TestMembershipHelpers, self).setUp()
        # Create a domain.
        self.domain = self.mm_client.create_domain('example.com')
        self.mlist = self.domain.create_list('test_list')
        self.test_user = User.objects.create_user(
            'test_user', 'test_user@example.com', 'pwd'
        )
        self.test_superuser = User.objects.create_superuser(
            'test_superuser', 'test_superuser@example.com', 'pwd'
        )
        self.test_owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'testpass'
        )
        self.test_moderator = User.objects.create_user(
            'testmoderator', 'moderator@example.com', 'testpass'
        )
        for user in (
            self.test_user,
            self.test_superuser,
            self.test_owner,
            self.test_moderator,
        ):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        self.mlist.add_owner(self.test_owner.email)
        self.mlist.add_moderator(self.test_moderator.email)

    def tearDown(self):
        self.domain.delete()
        for user in (
            self.test_user,
            self.test_superuser,
            self.test_owner,
            self.test_moderator,
        ):
            user.delete()

    def test_get_list(self):
        # Given the list's posting address, get_list should return the
        # MailingList object.
        mlist = get_list('test_list@example.com')
        self.assertTrue(isinstance(mlist, MailingList))
        self.assertEqual(mlist.fqdn_listname, 'test_list@example.com')
        # Given a list's fqdn, it should be possible to get the mlist too.
        mlist = get_list('test_list.example.com')
        self.assertTrue(isinstance(mlist, MailingList))
        self.assertEqual(mlist.fqdn_listname, 'test_list@example.com')
        # Given a MailingList object, make sure it is returned back.
        res = get_list(mlist)
        self.assertTrue(res is mlist)
        # Given wrong MailingList identifier should raise proper error.
        # TODO (maxking): Ideally, this should raise a validation error, given
        # that the MailingList identifier is wrong. However, given the error
        # propagation right now, it doesn't seem to be possible.
        with self.assertRaises(Mailman404Error):
            mlist = get_list('example.com')

    def test_user_is_list_owner(self):
        # First, it should return false as the user is not a list owner.
        self.assertFalse(user_is_list_owner(self.test_user, self.mlist))
        # It should return True for the list owner.
        self.assertTrue(user_is_list_owner(self.test_owner, self.mlist))
        # It should return False for the list moderator.
        self.assertFalse(user_is_list_owner(self.test_moderator, self.mlist))
        # Now let's add the test_user as an owner of the list.
        self.mlist.add_owner(self.test_user.email)
        self.assertTrue(user_is_list_owner(self.test_user, self.mlist))

    def test_user_is_list_moderator(self):
        # First, it should return false as the user is not a list moderator.
        self.assertFalse(user_is_list_moderator(self.test_user, self.mlist))
        # It should return False for the list owner.
        self.assertFalse(user_is_list_moderator(self.test_owner, self.mlist))
        # It should return False for the list moderator.
        self.assertTrue(
            user_is_list_moderator(self.test_moderator, self.mlist)
        )
        # Now let's add the test_user as an owner of the list.
        self.mlist.add_moderator(self.test_user.email)
        self.assertTrue(user_is_list_moderator(self.test_user, self.mlist))
