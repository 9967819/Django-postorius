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


from unittest import expectedFailure

from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.lib.mailman import get_mailman_user

from postorius.forms import ChangeSubscriptionForm, UserPreferences
from postorius.models import Mailman404Error, MailmanUser
from postorius.tests.utils import ViewTestCase


class MailmanUserTest(ViewTestCase):
    """
    Tests for the mailman user preferences settings page.
    """

    def setUp(self):
        super(MailmanUserTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.foo_list.send_welcome_message = False
        self.user = User.objects.create_user(
            'user', 'user@example.com', 'testpass'
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True
        )
        self.mm_user = get_mailman_user(self.user)

    def test_address_preferences_not_logged_in(self):
        self.assertRedirectsToLogin(reverse('user_address_preferences'))

    def test_subscriptions_not_logged_in(self):
        self.assertRedirectsToLogin(reverse('ps_user_profile'))

    def test_subscriptions_logged_in(self):
        self.client.login(username='user', password='testpass')
        response = self.client.get(reverse('ps_user_profile'))
        self.assertEqual(response.status_code, 200)

    def test_address_based_preferences(self):
        self.client.login(username='user', password='testpass')
        self.mm_user.add_address('user2@example.com')
        self.mm_user.add_address('user3@example.com')
        response = self.client.get(reverse('user_address_preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset']), 3)

    # this test needs re-thinking with the way we've hacked preferences
    # it has been disabled for now
    # def test_preferences_none(self):
    #     # Mailman does not accept None values for boolean preferences. When
    #     # those preferences are unset, they must be excluded from the POST
    #     # data.
    #     self.client.login(username='user', password='testpass')
    #     self.foo_list.subscribe(self.user.email, pre_verified=True,
    #                             pre_confirmed=True, pre_approved=True)
    #     prefs_with_none = (
    #         'receive_own_postings', 'acknowledge_posts',
    #         'hide_address', 'receive_list_copy',
    #         )
    #     # Prepare a Preferences subclass that will check the POST data
    #     import mailmanclient._client

    #     class TestingPrefs(mailmanclient._client.Preferences):
    #         testcase = self

    #         def save(self):
    #             for pref in prefs_with_none:
    #                 self.testcase.assertNotIn(pref, self._changed_rest_data)
    #     # Now check the relevant URLs
    #     with patch('mailmanclient._client.Preferences') as pref_class:
    #         pref_class.side_effect = TestingPrefs
    #         # Simple forms
    #         for url in (
    #                 reverse('user_mailmansettings'),
    #                 reverse('user_list_options',
    #                     args=[self.foo_list.list_id]),
    #                 ):
    #             response = self.client.post(
    #                 url, dict((pref, None) for pref in prefs_with_none))
    #             self.assertEqual(response.status_code, 302)
    #         # Formsets
    #         for url in ('user_address_preferences',
    #                     'user_subscription_preferences'):
    #             url = reverse(url)
    #             post_data = dict(
    #                 ('form-0-%s' % pref, None)
    #                 for pref in prefs_with_none)
    #             post_data.update({
    #                 'form-TOTAL_FORMS': '1',
    #                 'form-INITIAL_FORMS': '0',
    #                 'form-MAX_NUM_FORMS': ''
    #             })
    #             response = self.client.post(url, post_data)
    #             self.assertEqual(response.status_code, 302)

    @override_settings(AUTOCREATE_MAILMAN_USER=False)
    def test_subscriptions_no_mailman_user(self):
        # Existing Django users without a corresponding Mailman user must not
        # cause views to crash.
        user = User.objects.create_user(
            'old-user', 'old-user@example.com', 'testpass'
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True)
        self.client.login(username='old-user', password='testpass')
        self.assertRaises(
            Mailman404Error, MailmanUser.objects.get, address=user.email
        )
        response = self.client.get(reverse('ps_user_profile'))
        self.assertEqual(response.status_code, 200)
        # The Mailman user must have been created
        self.assertIsNotNone(MailmanUser.objects.get(address=user.email))

    def test_presence_of_form_in_user_global_settings(self):
        self.client.login(username='user', password='testpass')
        response = self.client.get(reverse('user_mailmansettings'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserPreferences)

    def test_presence_of_form_in_user_subscription_preferences(self):
        self.client.login(username='user', password='testpass')
        self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        response = self.client.get(reverse('user_subscription_preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['formset'])
        self.assertEqual(len(response.context['formset']), 1)

    def test_presence_of_form_in_user_list_options(self):
        self.client.login(username='user', password='testpass')
        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserPreferences)
        self.assertIsInstance(
            response.context['change_subscription_form'],
            ChangeSubscriptionForm,
        )

    def test_list_options_shows_all_addresses(self):
        self.client.login(username='user', password='testpass')
        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        # Add another email
        EmailAddress.objects.create(
            user=self.user, email='anotheremail@example.com', verified=True
        )
        user = self.mm_client.get_user('user@example.com')
        address = user.add_address('anotheremail@example.com')
        address.verify()
        # Check response
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'anotheremail@example.com')

    def _set_primary(self, user, mm_user):
        for addr in mm_user.addresses:
            addr.verify()
        mm_user.preferred_address = user.email

    def test_change_subscription_to_new_email(self):
        # Test that we can change subscription to a new email.
        self.client.login(username='user', password='testpass')
        user = self.mm_client.get_user('user@example.com')
        EmailAddress.objects.create(
            user=self.user, email='anotheremail@example.com', verified=True
        )
        address = user.add_address('anotheremail@example.com')
        address.verify()
        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        # Now, first verify that the list_options page has all the emails.
        # Check response
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertContains(response, 'anotheremail@example.com')
        self.assertContains(
            response,
            '<option value="user@example.com"'
            ' selected>user@example.com</option>',
        )
        member = self.mm_client.get_member(
            self.foo_list.list_id, 'user@example.com'
        )
        self.assertIsNotNone(member)
        # Initially, all preferences are none. Let's set it to something
        # custom.
        self.assertIsNone(member.preferences.get('acknowledge_posts'))
        member.preferences['acknowledge_posts'] = True
        member.preferences.save()
        # now, let's switch the subscription to a new user.
        response = self.client.post(
            reverse('change_subscription', args=(self.foo_list.list_id,)),
            {
                'subscriber': 'anotheremail@example.com',
                'member_id': member.member_id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response)
        member_new = self.mm_client.get_member(
            self.foo_list.list_id, 'anotheremail@example.com'
        )
        self.assertIsNotNone(member_new)
        # There is no 'member_id' attribute, so we simply use the self_link to
        # compare and make sure that the Member object is same.
        self.assertEqual(member.self_link, member_new.self_link)
        self.assertEqual(member_new.subscription_mode, 'as_address')
        # Also, assert that the new member's preferences are same.
        self.assertEqual(
            member.preferences['acknowledge_posts'],
            member_new.preferences['acknowledge_posts'],
        )

    def test_change_subscription_to_from_primary_address(self):
        # Test that we can change subscription to a new email.
        self.client.login(username='user', password='testpass')
        user = self.mm_client.get_user('user@example.com')
        self._set_primary(self.user, user)
        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        # Now, first verify that the list_options page has the primary address.
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertContains(response, 'Primary Address (user@example.com)')
        self.assertContains(
            response,
            '<option value="user@example.com" '
            'selected>user@example.com</option>',
        )
        member = self.mm_client.get_member(
            self.foo_list.list_id, 'user@example.com'
        )
        self.assertIsNotNone(member)
        # Initially, all preferences are none. Let's set it to something
        # custom.
        self.assertIsNone(member.preferences.get('acknowledge_posts'))
        member.preferences['acknowledge_posts'] = True
        member.preferences.save()
        # now, let's switch the subscription to a new user.
        response = self.client.post(
            reverse('change_subscription', args=(self.foo_list.list_id,)),
            {'subscriber': str(user.user_id), 'member_id': member.member_id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertHasSuccessMessage(response)
        new_member = self.mm_client.get_member(
            self.foo_list.list_id, 'user@example.com'
        )
        self.assertIsNotNone(new_member)
        self.assertEqual(new_member.subscription_mode, 'as_user')
        # we can't compare against the preferences object of `member` since the
        # resource is now Deleted due to unsubscribe-subscribe dance.
        self.assertEqual(new_member.preferences['acknowledge_posts'], True)

    def test_already_subscribed(self):
        self.client.login(username='user', password='testpass')

        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        # Now, first verify that the list_options page has all the emails.
        # Check response
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertContains(
            response,
            '<option value="user@example.com" '
            'selected>user@example.com</option>',
        )
        # now, let's switch the subscription to a new user.
        response = self.client.post(
            reverse('change_subscription', args=(self.foo_list.list_id,)),
            {'subscriber': 'user@example.com', 'member_id': member.member_id},
        )
        self.assertEqual(response.status_code, 302)
        error = self.assertHasErrorMessage(response)
        self.assertIn('You are already subscribed', error)

    def test_already_subscribed_with_primary_address(self):
        # Test that we can change subscription to a new email.
        self.client.login(username='user', password='testpass')
        user = self.mm_client.get_user('user@example.com')
        self._set_primary(self.user, user)
        member = self.foo_list.subscribe(
            user.user_id,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        # Now, first verify that the list_options page has the primary address.
        response = self.client.get(
            reverse('user_list_options', args=[member.member_id])
        )
        self.assertContains(
            response,
            (
                '<option value="{}" selected>Primary Address (user@example.com)'  # noqa: E501
                '</option>'
            ).format(user.user_id),
        )
        # now, let's switch the subscription to a new user.
        response = self.client.post(
            reverse('change_subscription', args=(self.foo_list.list_id,)),
            {'subscriber': str(user.user_id), 'member_id': member.member_id},
        )
        self.assertEqual(response.status_code, 302)
        error = self.assertHasErrorMessage(response)
        self.assertIn('You are already subscribed', error)

    def test_list_options_sets_preferred_address(self):
        # Test that preferred address is set.
        mm_user = get_mailman_user(self.user)
        self.assertIsNone(mm_user.preferred_address)
        member = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        self.client.login(username='user', password='testpass')
        self.client.get(reverse('user_list_options', args=[member.member_id]))
        self.assertEqual(mm_user.preferred_address.email, self.user.email)

    @expectedFailure
    def test_access_list_options_multiple_subscriptions(self):
        # Test that when multiple addresses of a single user are subscribed to
        # the same list that they are able to access them.
        # This test is now expected to fail due to
        # https://gitlab.com/mailman/mailman/-/merge_requests/997 which no
        # longer permits a User whose primary address is the same as a
        # subscribed Address to subscribe and vice versa.
        mm_user = get_mailman_user(self.user)
        self.assertIsNone(mm_user.preferred_address)
        self._set_primary(self.user, mm_user)
        # Subscribe the user twice, once with their address and then with their
        # primary address.
        member_primary = self.foo_list.subscribe(
            mm_user.user_id,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        member_addr = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        self.assertEqual(len(self.foo_list.members), 2)

        self.client.login(username='user', password='testpass')
        response = self.client.get(reverse('user_subscription_preferences'))
        self.assertEqual(response.status_code, 200)
        # There should be list options for two users.
        self.assertContains(response, 'Primary Address')
        self.assertContains(response, 'user@example.com')
        # Get the list options for both memberships and check subscriber ==
        # address.
        response = self.client.get(
            reverse('user_list_options', args=[member_addr.member_id])
        )
        self.assertEqual(response.status_code, 200)
        subscriber = response.context.get(
            'change_subscription_form'
        ).initial.get('subscriber')
        self.assertEqual(subscriber, member_addr.address.email)
        # Check subscriber == member_id
        response = self.client.get(
            reverse('user_list_options', args=[member_primary.member_id])
        )
        self.assertEqual(response.status_code, 200)
        subscriber = response.context.get(
            'change_subscription_form'
        ).initial.get('subscriber')
        self.assertEqual(subscriber, member_primary.user.user_id)

    def test_access_list_options_other_member(self):
        # Test that a user can't access member options for a different user.
        member_addr = self.foo_list.subscribe(
            self.user.email,
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        another_member = self.foo_list.subscribe(
            'anoter@example.com',
            pre_verified=True,
            pre_confirmed=True,
            pre_approved=True,
        )
        self.client.login(username='user', password='testpass')
        response = self.client.get(
            reverse('user_list_options', args=[another_member.member_id])
        )
        self.assertEqual(response.status_code, 404)
        # But they can access their own.
        response = self.client.get(
            reverse('user_list_options', args=[member_addr.member_id])
        )
        self.assertEqual(response.status_code, 200)


class TestListAllUsers(ViewTestCase):
    def setUp(self):
        super().setUp()
        for i in range(11):
            self.mm_client.create_user(
                'user{}@example.com'.format(i), 'testpass', 'User {}'.format(i)
            )
        self.su = User.objects.create_superuser('su', 'su@example.com', 'pass')

    def test_get_all_users_forbidden(self):
        response = self.client.get(reverse('list_users'))
        self.assertEqual(response.status_code, 403)

    def test_get_all_users_as_superuser(self):
        self.client.force_login(self.su)
        url = reverse('list_users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # default page size is 10, so we will get 10.
        self.assertEqual(len(response.context['all_users']), 10)
        # lets get all users by setting count.
        url += '?count=15'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # default page size is 10, so we will get 10.
        self.assertEqual(len(response.context['all_users']), 11)

    def test_search_user(self):
        self.client.force_login(self.su)

        def _get_url(query):
            return reverse('list_users') + '?q={}'.format(query)

        response = self.client.get(_get_url('0@e'))
        self.assertEqual(response.status_code, 200)
        # It should be two users, user0@example.com and user10@example.com
        self.assertEqual(len(response.context['all_users']), 2)
        # search with display name.
        response = self.client.get(_get_url('User 7'))
        self.assertEqual(response.status_code, 200)
        # It should be one user, user7@example.com, but it should search with
        # display name because of the space.
        self.assertEqual(len(response.context['all_users']), 1)
        self.assertEqual(
            response.context['all_users'][0].display_name, 'User 7'
        )


class TestManageUser(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.mm_client.create_user('user@example.com', 'testpass')
        self.su = User.objects.create_superuser('su', 'su@example.com', 'pass')
        self.dom = self.mm_client.create_domain('example.com')
        self.mlist = self.dom.create_list('test')
        self.mlist.subscribe(
            'user@example.com', pre_verified=True, pre_confirmed=True
        )

    def test_get_all_users_forbidden(self):
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 403)

    def test_get_manage_user(self):
        self.client.force_login(self.su)
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['auser'].user_id, self.user.user_id)
        user_form = response.context['user_form']
        self.assertEqual(user_form.user.user_id, self.user.user_id)
        addr_forms = response.context['addresses']
        self.assertEqual(len(addr_forms.forms), 1)
        subform = response.context['subscriptions']
        self.assertEqual(len(subform.forms), 1)
        self.assertIsNone(response.context['django_user'])
        self.assertIsNone(response.context['change_password'])

    def test_get_manage_user_with_django_user(self):
        user = User.objects.create_user(username='tester', password='test')
        for addr in self.user.addresses:
            EmailAddress.objects.create(user=user, email=addr.email)
        self.client.force_login(self.su)
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['auser'].user_id, self.user.user_id)
        user_form = response.context['user_form']
        self.assertEqual(user_form.user.user_id, self.user.user_id)
        addr_forms = response.context['addresses']
        self.assertEqual(len(addr_forms.forms), 1)
        subform = response.context['subscriptions']
        self.assertEqual(len(subform.forms), 1)
        self.assertEqual(response.context['django_user'], user)
        self.assertIsNotNone(response.context['change_password'])

    def test_update_display_name(self):
        self.client.force_login(self.su)
        response = self.client.post(
            reverse('manage_user', args=[self.user.user_id]),
            data={'display_name': 'My User', 'user_form': 'Update'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Successfully updated user.', response.content.decode())

    def test_update_user_address(self):
        self.client.force_login(self.su)
        addresses = self.user.addresses
        addresses[0].unverify()
        self.assertFalse(self.user.addresses[0].verified)
        formdata = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1',
            'form-0-verified': 'on',
            'address_form': 'Update',
        }
        response = self.client.post(
            reverse('manage_user', args=[self.user.user_id]),
            data=formdata,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.addresses[0].verified)
        self.assertIn(
            'Successfully updated addresses user@example.com',
            response.content.decode(),
        )

    def test_update_user_subscriptions(self):
        self.client.force_login(self.su)
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
            'form-0-moderation_action': 'discard',
            'form-0-delivery_mode': 'mime_digests',
            'subs_form': 'Update',
        }
        response = self.client.post(
            reverse('manage_user', args=[self.user.user_id]),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Successfully updated memberships for test.example.com',
            response.content.decode(),
        )

    def test_update_user_password(self):
        user = User.objects.create_user(
            username='myuser', password='mypassword'
        )
        EmailAddress.objects.create(user=user, email='user@example.com')
        self.assertTrue(
            self.client.login(username='myuser', password='mypassword')
        )
        self.client.force_login(self.su)
        data = {
            'change_password': 'Update',
            'password1': 'newpsdsd1987',
            'password2': 'newpsdsd1987',
        }
        response = self.client.post(
            reverse('manage_user', args=[self.user.user_id]), data=data
        )
        self.assertEqual(response.status_code, 302)
        # Verify by tring to login.
        self.assertTrue(
            self.client.login(username='myuser', password='newpsdsd1987')
        )

    def test_delete_user(self):
        user = User.objects.create_user(
            'deluser1', 'deluser1@example.com', 'delpassword1'
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True)
        mm_user = get_mailman_user(user)
        self.client.force_login(self.su)
        response = self.client.post(
            reverse('delete_user', args=[mm_user.user_id]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Successfully deleted account',
            response.content.decode(),
        )
        self.assertRaises(
            User.DoesNotExist, User.objects.get, email='deluser1@example.com'
        )
        self.assertRaises(
            Mailman404Error,
            MailmanUser.objects.get,
            address='deluser1@example.com',
        )

    def test_delete_user_multiple_emails(self):
        user = User.objects.create_user(
            'deluser2', 'deluser2@example.com', 'delpassword2'
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True)
        EmailAddress.objects.create(
            user=user, email='deluser2-another@example.com', verified=True
        )
        mm_user = get_mailman_user(user)
        address = mm_user.add_address('deluser2-another@example.com')
        address.verify()
        self.client.force_login(self.su)
        response = self.client.post(
            reverse('delete_user', args=[mm_user.user_id]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertRaises(
            User.DoesNotExist, User.objects.get, email='deluser2@example.com'
        )
        self.assertRaises(
            Mailman404Error,
            MailmanUser.objects.get,
            address='deluser2@example.com',
        )
        self.assertRaises(
            Mailman404Error,
            MailmanUser.objects.get,
            address='deluser2-another@example.com',
        )

    def test_get_ownerships_on_manage_user(self):
        self.client.force_login(self.su)
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ownerships']), 0)
        self.mlist.add_owner(self.user.addresses[0].email)
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ownerships']), 1)
        self.assertEqual(
            response.context['ownerships'][0].list_id, self.mlist.list_id
        )
        self.assertEqual(response.context['ownerships'][0].role, 'owner')
        self.assertEqual(
            response.context['ownerships'][0].address.email,
            self.user.addresses[0].email,
        )
        mlist2 = self.dom.create_list('test2')
        mlist2.add_moderator(self.user.addresses[0].email)
        response = self.client.get(
            reverse('manage_user', args=[self.user.user_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ownerships']), 2)
        self.assertEqual(
            response.context['ownerships'][1].list_id, mlist2.list_id
        )
        self.assertEqual(response.context['ownerships'][1].role, 'moderator')
        self.assertEqual(
            response.context['ownerships'][1].address.email,
            self.user.addresses[0].email,
        )
