# -*- coding: utf-8 -*-
# Copyright (C) 2012-2023 by the Free Software Foundation, Inc.
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


from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase


class ListCreationTest(ViewTestCase):
    """Tests for the new list page."""

    def setUp(self):
        super(ListCreationTest, self).setUp()
        self.user = User.objects.create_user('user', 'user@example.com', 'pwd')
        self.superuser = User.objects.create_superuser(
            'su', 'su@example.com', 'pwd'
        )
        for user in (self.user, self.superuser):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        self.domain = self.mm_client.create_domain('example.com')

    def test_permission_denied(self):
        self.client.login(username='user', password='pwd')
        response = self.client.get(reverse('list_new'))
        self.assertEqual(response.status_code, 403)

    def test_duplicate_listname_validation(self):
        # First, let's create a mailing list.
        self.domain.create_list('foo')
        self.client.login(username='su', password='pwd')
        post_data = {
            'listname': 'foo',
            'mail_host': 'example.com',
            'list_owner': 'owner@example.com',
            'advertised': 'True',
            'list_style': 'legacy-default',
            'description': 'A new list.',
        }
        response = self.client.post(reverse('list_new'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mailing List already exists')
        # Make sure this is the list create form and not just error page.
        self.assertContains(response, 'Create a new list')

    def test_new_list_created_with_owner(self):
        self.client.login(username='su', password='pwd')
        post_data = {
            'listname': 'a_new_list',
            'mail_host': 'example.com',
            'list_owner': 'owner@example.com',
            'advertised': 'True',
            'list_style': 'legacy-default',
            'description': 'A new list.',
        }
        response = self.client.post(reverse('list_new'), post_data)
        self.assertEqual(response.status_code, 302)
        # self.assertHasSuccessMessage(response)
        a_new_list = self.mm_client.get_list('a_new_list@example.com')
        self.assertEqual(a_new_list.fqdn_listname, 'a_new_list@example.com')
        owner_emails = [owner.email for owner in a_new_list.owners]
        self.assertEqual(owner_emails, ['owner@example.com'])

    def test_listname_validation(self):
        self.client.login(username='su', password='pwd')
        post_data = {
            'listname': 'a new list',
            'mail_host': 'example.com',
            'list_owner': 'owner@example.com',
            'advertised': 'True',
            'list_style': 'legacy-default',
            'description': 'A new list.',
        }
        response = self.client.post(reverse('list_new'), post_data)
        self.assertEqual(response.status_code, 200)
        # self.assertHasErrorMessage(response)
        self.assertContains(response, 'Please enter a valid listname')
