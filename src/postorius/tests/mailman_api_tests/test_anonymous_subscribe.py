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

from django.urls import reverse

from postorius.tests.utils import ViewTestCase


class AnonymousSubscribeTest(ViewTestCase):
    """Tests for anonymous subscribe page."""

    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')

    def test_anonymous_subscribe(self):
        url = reverse('list_anonymous_subscribe', args=('foo.example.com',))
        response = self.client.post(url, dict(email='aperson@example.com'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse('list_summary', args=('foo.example.com',))
        )
        # 302 responses have no context, hence we can't check the actual
        # success message.
        response = self.client.post(
            url, dict(email='bperson@example.com'), follow=True
        )
        success_msg = list(response.context.get('messages'))[0]
        self.assertEqual(success_msg.tags, 'success')
        self.assertEqual(
            success_msg.message,
            'Please check your inbox for further instructions',
        )
        # Make sure that there are two pending requests in Mailing List.
        self.assertEqual(len(self.foo_list.requests), 2)
        for req in self.foo_list.requests:
            self.assertEqual(req['token_owner'], 'subscriber')
            self.assertEqual(req['list_id'], 'foo.example.com')

    def test_anonymous_subscribe_get(self):
        # Issue 185
        # Test that anonymous subscribe with a GET doesn't raise a 500 error.
        url = reverse('list_anonymous_subscribe', args=('foo.example.com',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
