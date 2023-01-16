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


class ListMembersAccessTest(ViewTestCase):
    """Tests for the list members page.

    Tests permissions and creation of list owners and moderators.
    """

    def setUp(self):
        super(ListMembersAccessTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
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

    def test_page_not_accessible_if_not_logged_in(self):
        for role in ['owner', 'moderator', 'member', 'nonmember']:
            response = self.client.get(
                reverse(
                    'list_members',
                    args=(
                        'foo.example.com',
                        role,
                    ),
                )
            )
            self.assertEqual(response.status_code, 403)

    def test_page_not_accessible_for_unprivileged_users(self):
        self.client.login(username='testuser', password='testpass')
        for role in ['owner', 'moderator', 'member', 'nonmember']:
            response = self.client.get(
                reverse(
                    'list_members',
                    args=(
                        'foo.example.com',
                        role,
                    ),
                )
            )
            self.assertEqual(response.status_code, 403)

    def test_page_accessible_for_moderator(self):
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(
            reverse(
                'list_members',
                args=(
                    'foo.example.com',
                    'member',
                ),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_page_accessible_for_superuser(self):
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(
            reverse(
                'list_members',
                args=(
                    'foo.example.com',
                    'member',
                ),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_page_accessible_for_owner(self):
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(
            reverse(
                'list_members',
                args=(
                    'foo.example.com',
                    'member',
                ),
            )
        )
        self.assertEqual(response.status_code, 200)


class AddRemoveOwnerTest(ViewTestCase):
    """Tests for the list members page.

    Tests creation of list owners.
    """

    def setUp(self):
        super(AddRemoveOwnerTest, self).setUp()
        self.mm_client = self.mm_client
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.su = User.objects.create_superuser('su', 'su@example.com', 'pwd')
        EmailAddress.objects.create(
            user=self.su, email=self.su.email, verified=True
        )
        self.client.login(username='su', password='pwd')
        self.mm_client.get_list('foo.example.com').add_owner('su@example.com')

    def test_add_remove_owner(self):
        url = reverse(
            'list_members',
            args=(
                'foo.example.com',
                'owner',
            ),
        )
        response = self.client.post(url, {'email': 'newowner@example.com'})
        self.assertRedirects(response, url)
        owners_emails = [owner.email for owner in self.foo_list.owners]
        self.assertTrue('newowner@example.com' in owners_emails)
        self.client.post(
            reverse(
                'remove_role',
                args=('foo.example.com', 'owner', 'newowner@example.com'),
            )
        )
        owners_emails = [owner.email for owner in self.foo_list.owners]
        self.assertFalse('newowner@example.com' in owners_emails)

    def test_remove_owner_by_owner(self):
        owners_emails = [owner.email for owner in self.foo_list.owners]
        self.assertTrue('su@example.com' in owners_emails)
        # Make the logged in user a simple list owner
        self.su.is_superuser = False
        self.su.save()
        # It must still be allowed to create and remove owners
        url = reverse(
            'list_members',
            args=(
                'foo.example.com',
                'owner',
            ),
        )
        response = self.client.post(url, {'email': 'newowner@example.com'})
        self.assertRedirects(response, url)
        owners_emails = [owner.email for owner in self.foo_list.owners]
        self.assertTrue('newowner@example.com' in owners_emails)
        response = self.client.post(
            reverse(
                'remove_role',
                args=('foo.example.com', 'owner', 'newowner@example.com'),
            )
        )
        self.assertHasSuccessMessage(response)
        owners_emails = [owner.email for owner in self.foo_list.owners]
        self.assertFalse('newowner@example.com' in owners_emails)

    def test_remove_owner_as_owner_self_last(self):
        # It is allowed to remove itself, but only if there's another owner
        # left.
        mm_list = self.mm_client.get_list('foo.example.com')
        mm_list.add_owner('otherowner@example.com')
        owners_emails = [owner.email for owner in mm_list.owners]
        self.assertTrue('su@example.com' in owners_emails)
        self.assertTrue('otherowner@example.com' in owners_emails)
        response = self.client.post(
            reverse(
                'remove_role',
                args=('foo.example.com', 'owner', 'su@example.com'),
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response)
        owners_emails = [owner.email for owner in mm_list.owners]
        self.assertFalse('su@example.com' in owners_emails)
        # But not to remove the last owner
        mm_list.add_owner('su@example.com')
        mm_list.remove_owner('otherowner@example.com')
        owners_emails = [owner.email for owner in mm_list.owners]
        self.assertTrue('su@example.com' in owners_emails)
        self.assertFalse('otherowner@example.com' in owners_emails)
        response = self.client.post(
            reverse(
                'remove_role',
                args=('foo.example.com', 'owner', 'su@example.com'),
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasErrorMessage(response)
        owners_emails = [owner.email for owner in mm_list.owners]
        self.assertTrue('su@example.com' in owners_emails)


class AddModeratorTest(ViewTestCase):
    """Tests for the list members page.

    Tests creation of moderators.
    """

    def setUp(self):
        super(AddModeratorTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.su = User.objects.create_superuser('su', 'su@example.com', 'pwd')
        EmailAddress.objects.create(
            user=self.su, email=self.su.email, verified=True
        )
        # login and post new moderator data to url
        self.client.login(username='su', password='pwd')
        url = reverse(
            'list_members',
            args=(
                'foo.example.com',
                'moderator',
            ),
        )
        response = self.client.post(url, {'email': 'newmod@example.com'})
        self.assertRedirects(response, url)

    def tearDown(self):
        self.foo_list.delete()
        self.su.delete()
        self.domain.delete()

    def test_new_moderator_added(self):
        mods_emails = [mod.email for mod in self.foo_list.moderators]
        self.assertTrue('newmod@example.com' in mods_emails)


class ListMembersTest(ViewTestCase):
    """Test the list members page."""

    def setUp(self):
        super(ListMembersTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        EmailAddress.objects.create(
            user=self.superuser, email=self.superuser.email, verified=True
        )

    def tearDown(self):
        self.foo_list.delete()
        self.superuser.delete()
        self.domain.delete()

    def test_show_members_page(self):
        self.client.login(username='testsu', password='testpass')
        member_1 = self.foo_list.subscribe(
            'member-1@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        member_2 = self.foo_list.subscribe(
            'member-2@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 2)
        self.assertEqual(response.context['members'].paginator.count, 2)
        self.assertContains(response, member_1.email)
        self.assertContains(response, member_2.email)
        self.assertContains(response, '<small>(2)</small>')

    def test_show_members_details(self):
        """Test that Members's delivery related settings/preferences."""
        self.client.login(username='testsu', password='testpass')
        member_1 = self.foo_list.subscribe(
            'member-1@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        member_1.delivery_mode = 'plaintext_digests'
        member_1.moderation_action = 'hold'
        member_1.save()
        member_2 = self.foo_list.subscribe(
            'member-2@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        member_2.delivery_mode = 'summary_digests'
        member_2.moderation_action = 'defer'
        member_2.save()
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 2)
        for each in (
            # Delivery mode settings.
            'Plain Text Digests',
            'Summary Digests',
            # Moderatation action settings.
            'Hold for moderation',
            'Default processing',
        ):
            self.assertContains(response, each)

    def test_search_members_1(self):
        self.client.login(username='testsu', password='testpass')
        member_1 = self.foo_list.subscribe(
            'member-1@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        member_2 = self.foo_list.subscribe(
            'member-2@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member']),
            {'q': 'example.com'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 2)
        self.assertContains(response, member_1.email)
        self.assertContains(response, member_2.email)
        self.assertContains(response, '<small>(2)</small>')
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member']),
            {'q': 'member-1'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 1)
        self.assertContains(response, member_1.email)
        self.assertNotContains(response, member_2.email)
        self.assertContains(response, '<small>(1)</small>')
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member']),
            {'q': 'not_a_member'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 0)
        self.assertNotContains(response, member_1.email)
        self.assertNotContains(response, member_2.email)
        self.assertContains(response, '<small>(0)</small>')
        self.assertEqual(
            response.context['empty_error'],
            'No members were found matching the search.',
        )
        self.foo_list.unsubscribe('member-1@example.com')
        self.foo_list.unsubscribe('member-2@example.com')
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'member'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 0)
        self.assertEqual(
            response.context['empty_error'], 'List has no members'
        )
        self.assertContains(response, '<small>(0)</small>')


class ListNonMembersTest(ViewTestCase):
    """Test list non-members"""

    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        EmailAddress.objects.create(
            user=self.superuser, email=self.superuser.email, verified=True
        )

    def tearDown(self):
        self.foo_list.delete()
        self.superuser.delete()
        self.domain.delete()

    def test_show_nonmembers(self):
        self.client.login(username='testsu', password='testpass')
        self.foo_list.add_role(
            address='nonmember-1@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-2@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-3@example.com', role='nonmember'
        )
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'nonmember'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 3)
        self.assertEqual(response.context['members'].paginator.count, 3)
        self.assertContains(response, 'nonmember-1@example.com')
        self.assertContains(response, 'nonmember-2@example.com')
        self.assertContains(response, 'nonmember-3@example.com')
        self.assertContains(response, '<small>(3)</small>')

    def test_search_nonmembers(self):
        self.client.login(username='testsu', password='testpass')
        self.foo_list.add_role(
            address='nonmember-1@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-2@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-3@example.com', role='nonmember'
        )
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'nonmember']),
            {'q': '2@example.com'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 1)
        self.assertContains(response, 'nonmember-2@example.com')
        self.assertContains(response, '<small>(1)</small>')
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'nonmember']),
            {'q': 'random_query'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 0)
        self.assertEqual(
            response.context['empty_error'],
            'No nonmembers were found matching the search.',
        )
        self.assertContains(response, '<small>(0)</small>')

    def test_add_nonmember(self):
        self.client.login(username='testsu', password='testpass')
        # Check that there aren't any nonmembers.
        self.assertEqual(len(self.foo_list.nonmembers), 0)
        # Add a new nonmember.
        url = reverse(
            'list_members',
            args=(
                'foo.example.com',
                'nonmember',
            ),
        )
        response = self.client.post(
            url, {'email': 'new.nonmember@example.com'}
        )
        self.assertRedirects(response, url)
        response = self.client.get(
            reverse('list_members', args=['foo.example.com', 'nonmember'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['members']), 1)
        self.assertEqual(
            response.context['members'][0].email, 'new.nonmember@example.com'
        )

    def test_nonmember_delete(self):
        self.client.login(username='testsu', password='testpass')
        self.foo_list.add_role(
            address='nonmember-1@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-2@example.com', role='nonmember'
        )
        self.foo_list.add_role(
            address='nonmember-3@example.com', role='nonmember'
        )
        nonmember_emails = [nm.email for nm in self.foo_list.nonmembers]
        self.assertEqual(
            sorted(nonmember_emails),
            [
                'nonmember-1@example.com',
                'nonmember-2@example.com',
                'nonmember-3@example.com',
            ],
        )
        response = self.client.post(
            reverse(
                'remove_role',
                args=(
                    'foo.example.com',
                    'nonmember',
                    'nonmember-1@example.com',
                ),
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response)
        nonmember_emails = [nm.email for nm in self.foo_list.nonmembers]
        self.assertEqual(len(nonmember_emails), 2)
        self.assertFalse('nonmember-1@example.com' in nonmember_emails)


class TestMassRemoval(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        EmailAddress.objects.create(
            user=self.superuser, email=self.superuser.email, verified=True
        )
        self.client.login(username='testsu', password='testpass')

    def tearDown(self):
        self.foo_list.delete()
        self.superuser.delete()
        self.domain.delete()

    def test_mass_removal(self):
        member_list = []
        for count in range(100):
            member = f'member-{count}@example.com'
            member_list.append(member)
            self.foo_list.subscribe(
                member,
                pre_verified=True,
                pre_confirmed=True,
                pre_approved=True,
            )
        # Also, add an invalid address.
        member_list.append('member@member@example.com')
        self.assertEqual(len(self.foo_list.members), 100)
        response = self.client.post(
            reverse('mass_removal', args=('foo.example.com',)),
            data=dict(emails='\n'.join(member_list)),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.foo_list.members), 0)
