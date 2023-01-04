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


from unittest import expectedFailure
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.lib.mailman import get_mailman_user

from postorius.models import SubscriptionMode
from postorius.tests.utils import ViewTestCase


class TestSubscription(ViewTestCase):
    """Tests subscription to lists"""

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.open_list = self.domain.create_list('open_list')
        # Set subscription policy to open
        settings = self.open_list.settings
        settings['subscription_policy'] = 'open'
        settings.save()
        self.mod_list = self.domain.create_list('moderate_subs')
        # Set subscription policy to moderate
        settings = self.mod_list.settings
        settings['subscription_policy'] = 'moderate'
        settings.save()
        # Create django user.
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'pwd'
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True
        )
        EmailAddress.objects.create(
            user=self.user, email='fritz@example.org', verified=True
        )
        # Create Mailman user
        self.mm_user = self.mm_client.create_user('test@example.com', '')
        self.mm_user.add_address('fritz@example.org')
        for address in self.mm_user.addresses:
            address.verify()

    @patch('mailmanclient.MailingList.subscribe')
    def test_anonymous_subscribe(self, mock_subscribe):
        response = self.client.post(
            reverse(
                'list_anonymous_subscribe', args=('open_list.example.com',)
            ),
            {'email': 'test@example.com', 'display_name': 'Test User'},
        )
        mock_subscribe.assert_called_once()
        mock_subscribe.assert_called_with(
            'test@example.com',
            'Test User',
            pre_verified=False,
            pre_confirmed=False,
        )
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        self.assertHasSuccessMessage(response)

    def test_subscribe_open(self):
        # The subscription goes straight through.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com',)),
            {'subscriber': 'test@example.com'},
        )
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        self.assertHasSuccessMessage(response)

    def test_secondary_open(self):
        # Subscribe with a secondary email address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com',)),
            {'subscriber': 'fritz@example.org'},
        )
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        self.assertHasSuccessMessage(response)

    def test_unknown_address(self):
        # Impossible to register with an unknown address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com',)),
            {'subscriber': 'unknown@example.org'},
        )
        self.assertEqual(len(self.open_list.members), 0)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        self.assertHasErrorMessage(response)

    def test_banned_address(self):
        # Impossible to register with a banned address
        self.client.login(username='testuser', password='pwd')
        self.open_list.bans.add('test@example.com')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com',)),
            {'subscriber': 'test@example.com'},
        )
        self.assertEqual(len(self.open_list.members), 0)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        self.assertHasErrorMessage(response)

    def test_subscribe_mod(self):
        # The subscription is held for approval.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com',)),
            {'subscriber': 'test@example.com'},
        )
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertRedirects(
            response,
            reverse('list_summary', args=('moderate_subs.example.com',)),
        )
        self.assertHasSuccessMessage(response)

    def test_secondary_mod(self):
        # Subscribe with a secondary email address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com',)),
            {'subscriber': 'fritz@example.org'},
        )
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertRedirects(
            response,
            reverse('list_summary', args=('moderate_subs.example.com',)),
        )
        self.assertHasSuccessMessage(response)

    def test_subscribe_already_pending(self):
        # The user tries to subscribe twice on a moderated list.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com',)),
            {'subscriber': 'test@example.com'},
        )
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertHasSuccessMessage(response)
        # Try to subscribe a second time.
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com',)),
            {'subscriber': 'test@example.com'},
        )
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        message = self.assertHasErrorMessage(response)
        self.assertIn('Subscription request already pending', message)

    def test_subscribe_with_name(self):
        owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'pwd'
        )
        EmailAddress.objects.create(
            user=owner, email=owner.email, verified=True
        )
        self.open_list.add_owner('owner@example.com')
        self.client.login(username='testowner', password='pwd')
        email_list = """First Person <test-1@example.org>\n
                        "Second Person" <test-2@example.org>\n
                        test-3@example.org (Third Person)\n
                        test-4@example.org\n
                        <test-5@example.org>\n"""
        self.client.post(
            reverse('mass_subscribe', args=('open_list.example.com',)),
            {
                'emails': email_list,
                'pre_verified': True,
                'send_welcome_message': 'default',
            },
        )
        self.assertEqual(len(self.open_list.members), 5)
        first = self.open_list.get_member('test-1@example.org')
        second = self.open_list.get_member('test-2@example.org')
        third = self.open_list.get_member('test-3@example.org')
        fourth = self.open_list.get_member('test-4@example.org')
        fifth = self.open_list.get_member('test-5@example.org')
        self.assertEqual(first.address.display_name, 'First Person')
        self.assertEqual(second.address.display_name, 'Second Person')
        self.assertEqual(third.address.display_name, 'Third Person')
        self.assertIsNone(fourth.address.display_name)
        self.assertIsNone(fifth.address.display_name)

    def test_mass_subscribe_send_welcome_message(self):
        owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'pwd'
        )
        EmailAddress.objects.create(
            user=owner, email=owner.email, verified=True
        )
        self.open_list.add_owner('owner@example.com')
        self.client.login(username='testowner', password='pwd')
        virgin_q = self.mm_client.queues['virgin']
        initial_files = len(virgin_q.files)
        email_list = """First Person <test-1@example.org>\n
                        "Second Person" <test-2@example.org>\n"""
        self.client.post(
            reverse('mass_subscribe', args=('open_list.example.com',)),
            {
                'emails': email_list,
                'pre_verified': True,
                'send_welcome_message': True,
            },
        )
        self.assertEqual(len(self.open_list.members), 2)
        virgin_q = self.mm_client.queues['virgin']
        # There should be two more files in the queue.
        self.assertEqual(len(virgin_q.files) - initial_files, 2)
        initial_files += 2
        # Now subscribe some users by changing it to No.
        email_list = """test-3@example.org (Third Person)\n"""
        self.client.post(
            reverse('mass_subscribe', args=('open_list.example.com',)),
            {
                'emails': email_list,
                'pre_verified': True,
                'send_welcome_message': False,
            },
        )
        self.assertEqual(len(self.open_list.members), 3)
        # There should be zero more messages in virgin queue because we set
        # `sent_welcome_message` to False.
        # There should be two more files in the queue.
        virgin_q = self.mm_client.queues['virgin']
        self.assertEqual(len(virgin_q.files) - initial_files, 0)
        # If set to none, the default value of send_welcome_message works,
        # which is True.
        email_list = """test4@example.org (Third Person)\n"""
        self.client.post(
            reverse('mass_subscribe', args=('open_list.example.com',)),
            {
                'emails': email_list,
                'pre_verified': True,
                'send_welcome_message': 'default',
            },
        )
        self.assertEqual(len(self.open_list.members), 4)
        virgin_q = self.mm_client.queues['virgin']
        self.assertEqual(len(virgin_q.files) - initial_files, 1)

    def test_change_subscription_open(self):
        # The subscription is changed from an address to another
        member = self.open_list.subscribe('test@example.com')
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('change_subscription', args=['open_list.example.com']),
            {'subscriber': 'fritz@example.org', 'member_id': member.member_id},
        )
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        try:
            member = self.open_list.get_member('fritz@example.org')
        except ValueError:
            self.fail('The subscription was not changed')
        self.assertEqual(member.email, 'fritz@example.org')
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )

    def test_change_subscription_confirm(self):
        # The subscription is changed from an address to another
        confirm_list = self.domain.create_list('confirm_list')
        settings = confirm_list.settings
        settings['subscription_policy'] = 'confirm'
        settings.save()
        member = confirm_list.subscribe('test@example.com', pre_confirmed=True)
        self.assertEqual(len(confirm_list.members), 1)
        self.assertEqual(len(confirm_list.requests), 0)
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('change_subscription', args=['confirm_list.example.com']),
            {'subscriber': 'fritz@example.org', 'member_id': member.member_id},
        )
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(confirm_list.members), 1)
        self.assertEqual(len(confirm_list.requests), 0)
        try:
            member = confirm_list.get_member('fritz@example.org')
        except ValueError:
            self.fail('The subscription was not changed')
        self.assertEqual(member.email, 'fritz@example.org')
        self.assertRedirects(
            response,
            reverse('list_summary', args=('confirm_list.example.com',)),
        )

    @expectedFailure
    def test_change_subscription_from_address_to_primary(self):
        # Test that can we can switch subscription between address and primary
        # address (which happens to be same).
        # This test is now expected to fail due to
        # https://gitlab.com/mailman/mailman/-/merge_requests/997 which no
        # longer permits a User whose primary address is the same as a
        # subscribed Address to subscribe and vice versa.
        member = self.open_list.subscribe('test@example.com')
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(
            member.subscription_mode, SubscriptionMode.as_address.name
        )
        self.assertEqual(len(self.open_list.requests), 0)
        self.client.login(username='testuser', password='pwd')
        mm_user = get_mailman_user(self.user)
        mm_user.preferred_address = 'test@example.com'
        # Switch subscription to primary address when the same address is
        # subscribed.
        response = self.client.post(
            reverse('change_subscription', args=['open_list.example.com']),
            {'subscriber': mm_user.user_id, 'member_id': member.member_id},
        )
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        try:
            member = self.open_list.get_member('test@example.com')
        except ValueError:
            self.fail('The subscription was not changed')
        self.assertEqual(
            member.subscription_mode, SubscriptionMode.as_user.name
        )
        self.assertRedirects(
            response, reverse('list_summary', args=('open_list.example.com',))
        )
        # Now, if the user_id and address both are subscribed.
        addr_member = self.open_list.subscribe('test@example.com')
        self.assertIsNotNone(addr_member)
        self.assertEqual(len(self.open_list.members), 2)
        # Now trying to switch subscription should say already subscribed.
        response = self.client.post(
            reverse('change_subscription', args=['open_list.example.com']),
            {
                'subscriber': mm_user.user_id,
                'member_id': addr_member.member_id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasErrorMessage(response)
