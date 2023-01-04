# -*- coding: utf-8 -*-
# Copyright (C) 2016-2023 by the Free Software Foundation, Inc.
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

"""Tests for delete lists"""
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.models import MailDomain

from postorius.tests.utils import ViewTestCase


class ListDeleteTest(ViewTestCase):
    def setUp(self):
        super(ListDeleteTest, self).setUp()
        # Create domain `example.com` in Mailman
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('test_list')
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass'
        )
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        self.owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'testpass'
        )
        self.moderator = User.objects.create_user(
            'testmoderator', 'moderator@example.com', 'testpass'
        )
        for user in (self.user, self.superuser, self.owner, self.moderator):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        self.foo_list.add_owner('owner@example.com')
        self.foo_list.add_moderator('moderator@example.com')
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.url = reverse('list_delete', args=['test_list.example.com'])

    def test_access_anonymous(self):
        # Anonymous users users can't delete lists
        self.assertRedirectsToLogin(self.url)

    def test_access_basic_user(self):
        # Basic users can't delete lists
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_moderators(self):
        # Moderators can't delete lists
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_delete_confirm(self):
        # The user should be ask to confirm domain deletion on GET requests
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mm_client.lists), 1)

    def test_list_delete(self):
        # The domain should be deleted
        self.client.login(username='testowner', password='testpass')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('list_index'))
        self.assertEqual(len(self.mm_client.lists), 0)
