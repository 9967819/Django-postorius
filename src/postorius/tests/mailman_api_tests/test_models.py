# -*- coding: utf-8 -*-
# Copyright (C) 2012-2021 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.contrib.auth.models import User
from django.test import override_settings

from allauth.account.models import EmailAddress

from postorius.models import (
    MailmanApiError, MailmanListManager, MailmanUserManager)
from postorius.tests.utils import ViewTestCase


class ModelTest(ViewTestCase):
    """Tests for the list index page."""

    def setUp(self):
        super(ModelTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')

    @override_settings(AUTOCREATE_MAILMAN_USER=False)
    def test_mailman_user_not_created_when_flag_is_off(self):
        user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass')
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True)
        with self.assertRaises(HTTPError):
            self.mm_client.get_user('test@example.com')

    @override_settings(AUTOCREATE_MAILMAN_USER=True)
    def test_mailman_user_created_when_flag_is_on(self):
        user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass')
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True)
        mm_user = self.mm_client.get_user('test@example.com')
        self.assertEqual(str(mm_user.addresses[0]), 'test@example.com')

    @override_settings(AUTOCREATE_MAILMAN_USER=True)
    @patch('postorius.models.MailmanUser')
    def test_core_not_reachable(self, mock_model):
        # Fail Gracefully if the Core is not reachable when
        # creating the user account.
        mock_model.objects.create_from_django.side_effect = MailmanApiError
        # User creation should succeed without any error, even though there
        # is no MailmanUser. However, this error should be logged.
        with patch('postorius.models.logger') as log:
            User.objects.create_user('testuser, test@example.com', 'testpass')
            errmsg = 'Mailman Core API is not reachable.'
            log.error.assert_called_with(errmsg)
        # There should be no user in Mailman with this address.
        with self.assertRaises(HTTPError):
            self.mm_client.get_user('test@example.com')


class TestMailmanListManager(ViewTestCase):

    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.domain2 = self.mm_client.create_domain('most-desirable.org')
        self.foo_list = self.domain.create_list('foo')
        self.bar_list = self.domain.create_list('bar')
        self.baz_list = self.domain2.create_list('baz')
        self.list_manager = MailmanListManager()

    def test_get_all_mailinglists(self):
        lists = self.list_manager.all()
        # This should return all the 2 mailing lists that we have.
        self.assertEqual(len(lists), 3)
        self.assertEqual(
            [x.fqdn_listname for x in lists],
            ['bar@example.com', 'baz@most-desirable.org', 'foo@example.com'])

    def test_get_by_mail_host(self):
        lists = self.list_manager.by_mail_host('example.com')
        self.assertEqual(len(lists), 2)
        self.assertEqual(
            [x.fqdn_listname for x in lists],
            ['bar@example.com', 'foo@example.com'])

    def test_get_single_mailinglist(self):
        mlist = self.list_manager.get('baz@most-desirable.org')
        self.assertIsNotNone(mlist)
        self.assertEqual(str(mlist), str(self.baz_list))


class TestMailmanUserManager(ViewTestCase):

    @override_settings(AUTOCREATE_MAILMAN_USER=False)
    def setUp(self):
        super().setUp()
        self.user_manager = MailmanUserManager()
        self.bob = User.objects.create(
            email='bob@example.com', username='bob', first_name="Bob")
        self.alice = User.objects.create(
            email='alice@example.com', username='alice', first_name='Alice')

    def test_create_from_django_works(self):
        mm_user = self.user_manager.create_from_django(self.bob)
        self.assertIsNotNone(mm_user)
        self.assertEqual(len(mm_user.addresses), 1)

    def test_create_from_django_sets_all_attributes(self):
        mm_user = self.user_manager.create_from_django(self.bob)
        self.assertIsNotNone(mm_user)
        self.assertEqual(mm_user.display_name, 'Bob')
        self.assertEqual([str(x) for x in list(mm_user.addresses)],
                         ['bob@example.com'])

    def test_get_or_create_from_django(self):
        self.user_manager.create_from_django = MagicMock(name='create')
        muser = self.user_manager.get_or_create_from_django(self.bob)
        self.assertIsNotNone(muser)
        self.user_manager.create_from_django.assert_called_once()
        # This was a non-existent user so it was created for us. Now, let's try
        # with an existing user.
        user = self.user_manager.create(email=self.bob.email, password=None)
        self.assertIsNotNone(user)
        # Now we reset the mock and see that create_from_django isn't called
        # anymore.
        self.user_manager.create_from_django.reset_mock()
        muser = self.user_manager.get_or_create_from_django(self.bob)
        self.user_manager.create_from_django.assert_not_called()
