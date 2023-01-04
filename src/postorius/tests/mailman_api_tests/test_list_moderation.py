# -*- coding: utf-8 -*-
# Copyright (C) 2019-2023 by the Free Software Foundation, Inc.
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

import time

from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase


class HeldMessageTest(ViewTestCase):
    """Test view for Held message"""

    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.superuser = User.objects.create_superuser(
            'su', 'su@example.com', 'pwd'
        )
        EmailAddress.objects.create(
            user=self.superuser, email=self.superuser.email, verified=True
        )
        self.client.login(username='su', password='pwd')

    def _wait_for_processing(self, queue):
        while True:
            if len(queue.files) == 0:
                break
            time.sleep(0.1)

    def _wait_for_held_message(self, mlist):
        # Wait for the message to land in held queue.
        while True:
            all_held = mlist.held
            if len(all_held) > 0:
                break
            time.sleep(0.1)

    def test_accept_held_messages(self):
        # Test that held messages are visible.
        mlist = self.domain.create_list('test-1')
        test_msg = """\
From: aperson@example.com
To: test-1@example.com
Subject: This is a test message
Message-ID: <test-msg@id>

This is a test message.

"""
        inque = self.mm_client.queues['in']
        inque.inject('test-1.example.com', test_msg)
        # Wait for the message to be formatted.
        self._wait_for_processing(inque)
        # Wait for message to land in held message queue.
        self._wait_for_held_message(mlist)
        # Check that there is a held message.
        self.assertEqual(len(mlist.held), 1)
        held_message = mlist.held[0]
        # Test that a held message is accepted when POST'ing.
        response = self.client.post(
            reverse('moderate_held_message', args=('test-1.example.com',)),
            {
                'msgid': held_message.request_id,
                'accept': True,
                'moderation_choice': 'no-action',
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_accept_held_message_moderate_member(self):
        # Test that we can moderate a member and accept a message at the same
        # time.
        mlist = self.domain.create_list('test-2')
        # Set default action to be hold for member's post.
        mlist.settings['default_member_action'] = 'hold'
        mlist.settings.save()
        # Subscribe this user.
        mlist.subscribe(
            'aperson@example.com', pre_verified=True, pre_confirmed=True
        )
        test_msg = """\
From: aperson@example.com
To: test-2@example.com
Subject: This is a test message
Message-ID: <test-msg@id>

This is a test message.

"""
        inque = self.mm_client.queues['in']
        inque.inject('test-2.example.com', test_msg)
        # Wait for the message to be formatted.
        self._wait_for_processing(inque)
        # Wait for message to land in held message queue.
        self._wait_for_held_message(mlist)
        # Check that there is a held message.
        self.assertEqual(len(mlist.held), 1)
        held_message = mlist.held[0]
        # Test that a held message is accepted when POST'ing.
        response = self.client.post(
            reverse('moderate_held_message', args=('test-2.example.com',)),
            {
                'msgid': held_message.request_id,
                'accept': True,
                'moderation_choice': 'defer',
            },
        )
        self.assertEqual(response.status_code, 302)
        member = mlist.get_member('aperson@example.com')
        self.assertEqual(member.moderation_action, 'defer')

    def test_moderate_held_message_missing(self):
        self.domain.create_list('test-3')
        response = self.client.post(
            reverse('moderate_held_message', args=('test-3.example.com',)),
            {'msgid': '12345', 'accept': True, 'moderation_choice': 'defer'},
        )

        self.assertHasErrorMessage(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, '/postorius/lists/test-3.example.com/held_messages'
        )

    def test_reject_held_message_with_reason(self):
        mlist = self.domain.create_list('test-2')
        test_msg = """\
From: aperson@example.com
To: test-2@example.com
Subject: This is a test message
Message-ID: <test-msg@id>

This is a test message.

"""
        inque = self.mm_client.queues['in']
        inque.inject('test-2.example.com', test_msg)
        # Wait for the message to be formatted.
        self._wait_for_processing(inque)
        # Wait for message to land in held message queue.
        self._wait_for_held_message(mlist)
        # Check that there is a held message.
        self.assertEqual(len(mlist.held), 1)
        held_message = mlist.held[0]
        # Test that a held message is rejected when POST'ing.
        response = self.client.post(
            reverse('moderate_held_message', args=('test-2.example.com',)),
            {
                'msgid': held_message.request_id,
                'reject': True,
                'reason': 'Wrong mailing list',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mlist.held), 0)

    def test_moderate_held_message_set_moderation_for_nonmember(self):
        mlist = self.domain.create_list('test-3')
        test_msg = """\
From: aperson@example.com
To: test-3@example.com
Subject: This is a test message
Message-ID: <test-msg@id>

This is a test message.

"""
        inque = self.mm_client.queues['in']
        inque.inject('test-3.example.com', test_msg)
        # Wait for the message to be formatted.
        self._wait_for_processing(inque)
        # Wait for message to land in held message queue.
        self._wait_for_held_message(mlist)
        # Check that there is a held message.
        self.assertEqual(len(mlist.held), 1)
        held_message = mlist.held[0]
        # Test that a held message is rejected when POST'ing.
        response = self.client.post(
            reverse('moderate_held_message', args=('test-3.example.com',)),
            {
                'msgid': held_message.request_id,
                'reject': True,
                'reason': 'Wrong mailing list',
                'moderation_choice': 'hold',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response, count=2)
        self.assertEqual(len(mlist.held), 0)
        nonmember = mlist.get_nonmember('aperson@example.com')
        self.assertEqual(nonmember.moderation_action, 'hold')

    def test_moderate_held_message_set_moderation_for_member(self):
        mlist = self.domain.create_list('test-4')
        member = mlist.subscribe(
            'aperson@example.com',
            pre_verified=True,
            pre_approved=True,
            pre_confirmed=True,
        )
        mlist.settings['default_member_action'] = 'hold'
        mlist.settings.save()
        self.assertIsNotNone(member)
        test_msg = """\
From: aperson@example.com
To: test-4@example.com
Subject: This is a test message
Message-ID: <test-msg1234@id>

This is a test message.
"""
        inque = self.mm_client.queues['in']
        inque.inject('test-4.example.com', test_msg)
        # Wait for the message to be formatted.
        self._wait_for_processing(inque)
        # Wait for message to land in held message queue.
        self._wait_for_held_message(mlist)
        # Check that there is a held message.
        self.assertEqual(len(mlist.held), 1)
        held_message = mlist.held[0]
        # Test that a held message is rejected when POST'ing.
        response = self.client.post(
            reverse('moderate_held_message', args=('test-4.example.com',)),
            {
                'msgid': held_message.request_id,
                'reject': True,
                'reason': 'Wrong mailing list',
                'moderation_choice': 'defer',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response, count=2)
        self.assertEqual(len(mlist.held), 0)
        member = mlist.get_member('aperson@example.com')
        self.assertEqual(member.moderation_action, 'defer')


class TestConfirmToken(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.mlist = self.domain.create_list('mylist')
        settings = self.mlist.settings
        settings['subscription_policy'] = 'confirm'
        settings.save()

    def tearDown(self):
        self.mlist.delete()
        self.domain.delete()

    def test_confirm_token(self):
        # Test that we can first get a token page to confirm.
        token = self.mlist.subscribe('aperson@example.com', 'Anne Петрова')
        self.assertIsNotNone(token.get('token'))
        resp = self.client.get(
            reverse('confirm_token', args=(self.mlist.list_id,))
            + '?token={}'.format(token.get('token'))
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            'Confirm subscription of Anne Петрова'
            in resp.content.decode('utf-8')
        )
        self.assertTrue(token.get('token') in resp.content.decode('utf-8'))
        # Now, let's confirm the token.
        with self.assertRaises(ValueError):
            self.mlist.get_member('aperson@example.com')
        resp = self.client.post(
            reverse('confirm_token', args=(self.mlist.list_id,)),
            data={'token': token.get('token')},
        )
        self.assertTrue(resp.status_code, 301)
        member = self.mlist.get_member('aperson@example.com')
        self.assertIsNotNone(member)

    def test_invalid_expired_token(self):
        resp = self.client.get(
            reverse('confirm_token', args=(self.mlist.list_id,))
            + '?token=badtoken'
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(b'Token expired or invalid' in resp.content)

    def test_moderator_token(self):
        # Set the subscription policy to moderate for confirmation from mod.
        settings = self.mlist.settings
        settings['subscription_policy'] = 'moderate'
        settings.save()
        # Subscribe to generate a mod approval req.
        token = self.mlist.subscribe(
            'aperson@example.com', 'Anne Person', pre_verified=True
        )
        self.assertIsNotNone(token.get('token'))
        token = self.mlist.get_request(token.get('token'))
        self.assertEqual(token['token_owner'], 'moderator')
        resp = self.client.get(
            reverse('confirm_token', args=(self.mlist.list_id,))
            + '?token={}'.format(token.get('token'))
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.url,
            '/postorius/lists/mylist.example.com/subscription_requests',
        )
