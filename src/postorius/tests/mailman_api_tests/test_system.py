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

from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase


class TestSystemInformationPage(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        EmailAddress.objects.create(
            user=self.superuser, email='su@example.com', verified=True
        )

    def test_system_info(self):
        response = self.client.get(reverse('system_information'))
        # Logged-out users shouldn't be able to get this information.
        self.assertEqual(response.status_code, 302)
        # Superuser should have access to this information.
        self.assertTrue(
            self.client.login(username='testsu', password='testpass')
        )
        response = self.client.get(reverse('system_information'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mailman Core API Version', response.content)
        self.assertIn(b'Mailman Core Version', response.content)

    def test_list_queue_info(self):
        # Test the values inthe queue.
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('system_information'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('queues', response.context)
        self.mm_client.create_domain('example.com').create_list('somelist')
        badq = self.mm_client.queues.get('bad')
        badq.inject(
            'somelist.example.com',
            'From: abhilash@example.com\nTo:somelist@example.com\n\n Hello',
        )
        response = self.client.get(reverse('system_information'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('queues', response.context)
        queues = response.context.get('queues')
        self.assertEqual(queues['bad'], 1)
