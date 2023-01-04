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

"""Tests for ban lists"""

from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress
from bs4 import BeautifulSoup

from postorius.tests.utils import ViewTestCase


class ListBansTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        # Create domain `example.com` in Mailman
        self.domain = self.mm_client.create_domain('example.com')
        self.m_list = self.domain.create_list('test_list')
        self.test_user = User.objects.create_user(
            'test_user', 'test_user@example.com', 'pwd'
        )
        self.test_superuser = User.objects.create_superuser(
            'test_superuser', 'test_superuser@example.com', 'pwd'
        )
        for user in (self.test_user, self.test_superuser):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        self.client.login(username='test_superuser', password='pwd')
        self.url = reverse('list_bans', args=['test_list.example.com'])
        self.bans_list = self.m_list.bans

    def test_login_redirect_for_anonymous(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_no_access_for_basic_user(self):
        self.client.logout()
        self.client.login(username='test_user', password='pwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_for_superuser(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_create_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('addban_form' in response.context)
        soup = BeautifulSoup(response.content, 'html.parser')
        tag_input = soup.find(
            'input',
            {
                'class': 'form-control',
                'id': 'id_email',
                'name': 'email',
                'type': 'text',
            },
        )
        self.assertIsNotNone(tag_input)
        tag_button = soup.find(
            'button',
            {
                'class': 'btn btn-primary',
                'name': 'add',
                'type': 'submit',
            },
        )
        self.assertIsNotNone(tag_button)

    def test_context_contains_delete_forms(self):
        banned = ['banned{}@example.com'.format(i) for i in range(1, 10)]
        for ban in banned:
            self.bans_list.add(ban)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        for ban in banned:
            self.assertIsNotNone(
                soup.find(
                    'input',
                    {
                        'name': 'email',
                        'type': 'hidden',
                        'value': ban,
                    },
                )
            )
        self.assertEqual(
            len(
                soup.find_all(
                    'button',
                    {
                        'class': 'btn btn-danger btn-xs',
                        'name': 'del',
                        'type': 'submit',
                    },
                )
            ),
            9,
        )

    def test_add_ban(self):
        response = self.client.post(
            self.url,
            {
                'email': 'banned@example.com',
                'add': True,
            },
        )
        self.assertRedirects(response, self.url)
        self.assertIn('banned@example.com', self.bans_list)
        self.assertHasSuccessMessage(response)

        self.bans_list.remove('banned@example.com')

    def test_del_ban(self):
        self.bans_list.add('banned@example.com')
        self.assertIn('banned@example.com', self.bans_list)
        response = self.client.post(
            self.url,
            {
                'email': 'banned@example.com',
                'del': True,
            },
        )
        self.assertRedirects(response, self.url)
        self.assertNotIn('banned@example.com', self.bans_list)
        self.assertHasSuccessMessage(response)

    def test_del_unknown_ban(self):
        self.assertNotIn('banned@example.com', self.bans_list)
        response = self.client.post(
            self.url,
            {
                'email': 'banned@example.com',
                'del': True,
            },
        )
        self.assertRedirects(response, self.url)
        message = self.assertHasErrorMessage(response)
        self.assertIn('is not banned', message)

    def test_add_ban_duplicate(self):
        self.bans_list.add('banned@example.com')
        self.assertIn('banned@example.com', self.bans_list)
        response = self.client.post(
            self.url,
            {
                'email': 'banned@example.com',
                'add': True,
            },
        )
        self.assertRedirects(response, self.url)
        message = self.assertHasErrorMessage(response)
        self.assertIn('is already banned', message)

        self.bans_list.remove('banned@example.com')


class GlobalBansTest(ListBansTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('global_bans')
        self.bans_list = self.mm_client.bans
