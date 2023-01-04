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
from django.urls import reverse

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase


class TestListJoinLeave(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass'
        )
        self.user2 = User.objects.create_user(
            'testuser2', 'test2@example.com', 'test2pass'
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        EmailAddress.objects.create(
            user=self.user2,
            email=self.user2.email,
            verified=True,
            primary=True,
        )

    def test_unsubscribe_pending_verification(self):
        """Test that unsubscription waiting verification shows right message"""
        self.foo_list.subscribe(
            'test@example.com',
            pre_approved=True,
            pre_verified=True,
            pre_confirmed=True,
        )
        self.foo_list.settings['unsubscription_policy'] = 'moderate'
        self.foo_list.settings.save()
        # now, first make sure that the list summary page shows the unsubscribe
        # button.
        self.client.force_login(user=self.user)
        res = self.client.get(
            reverse('list_summary', args=[self.foo_list.list_id])
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Unsubscribe')
        response = self.client.post(
            reverse('list_unsubscribe', args=[self.foo_list.list_id]),
            data={'email': 'test@example.com'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Your unsubscription request has been submitted and is waiting for'
            ' moderator approval.',
        )
        self.assertEqual(len(self.foo_list.unsubscription_requests), 1)
        # Re-trying tine same thing should return a pending error.
        response = self.client.post(
            reverse('list_unsubscribe', args=[self.foo_list.list_id]),
            data={'email': 'test@example.com'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'You have a pending unsubscription request waiting for'
            ' moderator approval.',
        )

    def test_unsubscribe_self_only(self):
        """Test that a user can unsubscribe themselves, but not other users"""
        for address in ['test@example.com', 'test2@example.com']:
            self.foo_list.subscribe(
                address,
                pre_approved=True,
                pre_verified=True,
                pre_confirmed=True,
            )
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse('list_unsubscribe', args=[self.foo_list.list_id]),
            data={'email': 'test@example.com'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'test@example.com has been ' 'unsubscribed from this list.',
        )
        # They should no longer be a member
        self.assertRaises(
            ValueError, lambda: self.foo_list.get_member('test@example.com')
        )
        # Now have user test try to unsubscribe user test2
        response = self.client.post(
            reverse('list_unsubscribe', args=[self.foo_list.list_id]),
            data={'email': 'test2@example.com'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You can only unsubscribe yourself.')
        # Should still be a member
        self.assertIsNotNone(self.foo_list.get_member('test2@example.com'))

    def test_subscribe_to_lists(self):
        self.client.force_login(self.user)
        res = self.client.post(
            reverse('list_subscribe', args=[self.foo_list.list_id]),
            data={
                'subscriber': 'test@example.com',
                'delivery_mode': 'plaintext_digests',
                'delivery_status': 'by_user',
            },
        )
        self.assertEqual(res.status_code, 302)
        self.assertHasSuccessMessage(res)
        member = self.foo_list.get_member('test@example.com')
        self.assertEqual(member.delivery_mode, 'plaintext_digests')
        self.assertEqual(member.preferences['delivery_status'], 'by_user')
