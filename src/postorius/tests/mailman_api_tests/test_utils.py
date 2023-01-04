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
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase
from postorius.utils import get_django_user


class TestUtils(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.mm_client.create_user('aperson@example.com', 'xxx')

    def test_get_django_user_nonexistent(self):
        self.assertIsNone(get_django_user(self.user))

    def test_get_django_user_exists(self):
        user = User.objects.create_user(
            username='testuser', password='testpas'
        )
        EmailAddress.objects.create(user=user, email='aperson@example.com')
        dj_user = get_django_user(self.user)
        self.assertIsNotNone(dj_user)
        self.assertEqual(dj_user, user)
