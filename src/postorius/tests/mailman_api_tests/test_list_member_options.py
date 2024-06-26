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


from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.lib.mailman import get_mailman_client
from six.moves.urllib_parse import quote

from postorius.forms import MemberModeration, UserPreferences
from postorius.tests.utils import ViewTestCase


class ListMembersOptionsTest(ViewTestCase):
    """Tests for the list members page.

    Tests permissions and creation of list owners and moderators.
    """

    def setUp(self):
        super(ListMembersOptionsTest, self).setUp()
        self.domain = get_mailman_client().create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
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
        self.mm_user = get_mailman_client().create_user('test@example.com', '')
        self.mm_user.addresses[0].verify()
        self.foo_list.subscribe(
            'test@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        self.url = reverse(
            'list_member_options',
            args=(
                self.foo_list.list_id,
                'test@example.com',
            ),
        )

    def test_page_not_accessible_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse(settings.LOGIN_URL), quote(self.url)),
        )

    def test_page_not_accessible_for_unprivileged_users(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_not_accessible_for_moderator(self):
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_page_accessible_for_superuser(self):
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['moderation_form'], MemberModeration
        )
        self.assertIsInstance(
            response.context['preferences_form'], UserPreferences
        )

    def test_page_accessible_for_owner(self):
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['moderation_form'], MemberModeration
        )
        self.assertIsInstance(
            response.context['preferences_form'], UserPreferences
        )

    def test_nonexistent_member_returns_404(self):
        self.client.login(username='testsu', password='testpass')
        url = reverse(
            'list_member_options',
            args=(
                self.foo_list.list_id,
                'none@example.com',
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_moderation_action(self):
        self.assertIsNone(
            self.foo_list.get_member('test@example.com').moderation_action
        )
        self.client.login(username='testsu', password='testpass')
        response = self.client.post(
            self.url, {'formname': 'moderation', 'moderation_action': 'hold'}
        )
        self.assertRedirects(response, self.url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(
            self.foo_list.get_member('test@example.com').moderation_action,
            'hold',
        )
        response = self.client.post(
            self.url, {'formname': 'moderation', 'moderation_action': ''}
        )
        self.assertRedirects(response, self.url)
        self.assertHasSuccessMessage(response)
        self.assertIsNone(
            self.foo_list.get_member('test@example.com').moderation_action
        )

    def test_get_nonmember_options(self):
        # Test that nonmember options can also be set using
        # `list_member_options` view.
        self.client.login(username='testowner', password='testpass')
        self.foo_list.add_role(
            role='nonmember', address='nonmember@example.com'
        )
        self.assertEqual(len(self.foo_list.nonmembers), 1)
        # Now, let's try to get options for these users.
        url = reverse(
            'list_member_options',
            args=(
                self.foo_list.list_id,
                'nonmember@example.com',
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_nonmember_moderation_action(self):
        self.foo_list.add_role(
            role='nonmember', address='nonmember@example.com'
        )
        nonmember = self.foo_list.find_members(
            address='nonmember@example.com'
        )[0]
        self.assertIsNone(nonmember.moderation_action)
        url = reverse(
            'list_member_options',
            args=(
                self.foo_list.list_id,
                'nonmember@example.com',
            ),
        )
        self.client.login(username='testsu', password='testpass')
        response = self.client.post(
            url, {'formname': 'moderation', 'moderation_action': 'hold'}
        )
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        nonmember = self.foo_list.find_members(
            address='nonmember@example.com'
        )[0]
        self.assertEqual(nonmember.moderation_action, 'hold')
        response = self.client.post(
            url, {'formname': 'moderation', 'moderation_action': ''}
        )
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        nonmember = self.foo_list.find_members(
            address='nonmember@example.com'
        )[0]
        self.assertIsNone(nonmember.moderation_action)

    def test_nonmember_and_owner_with_same_email_action(self):
        # Test that when an email address with both owner and non-member roles
        # are subscribed that we are able to moderate the non-member using the
        # list options view.
        self.foo_list.add_role(role='nonmember', address='aperson@example.com')
        self.foo_list.add_role(role='owner', address='aperson@example.com')
        url = (
            reverse(
                'list_member_options',
                args=(
                    self.foo_list.list_id,
                    'aperson@example.com',
                ),
            )
            + '?role=nonmember'
        )
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(url)
        member = response.context.get('mm_member')
        # Assert that the list options are rendered for the non-member object
        # and not the owner object.
        self.assertEqual(member.role, 'nonmember')
        self.assertEqual(member.email, 'aperson@example.com')
