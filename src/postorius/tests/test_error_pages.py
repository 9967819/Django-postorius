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
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from mailmanclient import Client


def server_error(requset):
    raise Exception()


class TestUtils(TestCase):
    def test_404_page(self):
        response = self.client.get('/postorius/not-here', follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertTrue('<h1>Page not found</h1>' in str(response.content))
        self.assertTrue(
            '<div class="alert alert-danger">' in str(response.content)
        )

    @patch.object(Client, 'get_list')
    def test_403_page(self, mock_get_list):
        user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass'
        )
        self.client.force_login(user)
        response = self.client.get(
            '/postorius/lists/foolist.example.org/settings/', follow=True
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue('<h1>Forbidden</h1>' in str(response.content))
        self.assertTrue(
            '<div class="alert alert-danger">' in str(response.content)
        )

    def test_500_page(self):
        su = User.objects.create_superuser(
            'su', 'test@example.com', 'testpass'
        )
        self.client.force_login(su)
        response = self.client.get('/500', follow=True)
        self.assertEqual(response.status_code, 500)
        self.assertTrue(b'<h1>Server error</h1>' in response.content)
