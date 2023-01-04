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

from django.contrib.auth.models import User
from django.forms import formset_factory

from allauth.account.models import EmailAddress

from postorius.forms.user_forms import (
    ManageAddressForm,
    ManageAddressFormSet,
    ManageMemberForm,
    ManageMemberFormSet,
    ManageUserForm,
)
from postorius.tests.utils import ViewTestCase


class ManageMemberFormTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.mm_client.create_user('aperson@example.com', 'xxx')
        domain = self.mm_client.create_domain('example.com')
        self.mlist = domain.create_list('test')
        self.member = self.mlist.subscribe(
            'aperson@example.com', pre_verified=True, pre_confirmed=True
        )

    def test_manage_member_form_basic(self):
        form = ManageMemberForm(member=self.member)
        # Initial values of this form should be the Member's current values.
        form.initial['moderation_action'] = self.member.moderation_action
        form.initial['delivery_mode'] = self.member.delivery_mode
        # Initialized form is valid by default with no changed values.
        form = ManageMemberForm(
            dict(
                delivery_mode=self.member.delivery_mode,
                moderation_action=self.member.moderation_action,
            ),
            member=self.member,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.changed_data, [])
        # Saving the form with no changed data should return False.
        self.assertFalse(form.save())

    def test_manage_member_form_updates(self):
        form = ManageMemberForm(
            dict(moderation_action='hold', delivery_mode='plaintext_digests'),
            member=self.member,
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.changed_data, ['moderation_action'])
        self.assertTrue(form.save())
        self.assertEqual(self.member.moderation_action, 'hold')
        self.assertEqual(self.member.delivery_mode, 'plaintext_digests')

    def test_manage_member_formset(self):
        # Test initialize formset with single Member.
        formset = formset_factory(
            ManageMemberForm, formset=ManageMemberFormSet, extra=0
        )
        form = formset(members=[self.member])
        self.assertEqual(len(form.forms), 1)
        self.assertEqual(form.forms[0].member, self.member)
        # Data in formsets are for each list like this.
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
            'form-0-moderation_action': 'discard',
            'form-0-delivery_mode': 'mime_digests',
        }
        form = formset(data, members=[self.member])
        self.assertTrue(form.is_valid())
        # Saving should return all the list ids for which Members are updated.
        self.assertEqual(form.save(), ['test.example.com'])
        # It should update the Member.
        self.assertEqual(self.member.moderation_action, 'discard')
        self.assertEqual(self.member.delivery_mode, 'mime_digests')


class ManageAddressFormTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.mm_client.create_user('aperson@example.com', 'xxx')
        self.user.add_address('bperson@example.com')
        self.user.add_address('cperson@example.com')

    def test_manage_address_form(self):
        addr = self.user.addresses[0]
        # Initially, the address should be unverified.
        self.assertFalse(addr.verified)
        form = ManageAddressForm(address=addr)
        self.assertEqual(form.initial['verified'], addr.verified)
        form = ManageAddressForm(dict(verified=addr.verified), address=addr)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.changed_data, [])
        # Now let's try to verify that address.
        form = ManageAddressForm(dict(verified=True), address=addr)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())
        self.assertTrue(addr.verified)

    def _test_manage_address_formset(self):
        addresses = self.user.addresses
        formset = formset_factory(
            ManageAddressForm, formset=ManageAddressFormSet, extra=0
        )
        form = formset(addresses=addresses)
        self.assertEqual(len(form.forms), len(addresses))

        newdata = [False, True, True]
        data = self._initialize_formset(newdata)
        form = formset(data, addresses=addresses)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save(), [addresses[1].email, addresses[2].email])
        # Again fetch from API to get new values.
        addresses = self.user.addresses
        # Ensure that the verified is set to the values in form for addresses.
        for addr, verified in zip(addresses, newdata):
            self.assertEqual(addr.verified, verified)
        return zip(addresses, newdata)

    test_manage_address_formset = _test_manage_address_formset

    def test_update_django_addresses(self):
        addresses = self.user.addresses
        # Create the django user.
        user = User.objects.create_user(username='tester', password='test')
        for addr in addresses:
            EmailAddress.objects.create(user=user, email=addr.email)
        # Initially, they are all unverified
        for addr in EmailAddress.objects.filter(user=user):
            self.assertFalse(addr.verified)
        newdata = self._test_manage_address_formset()
        # Now django addreses should be updated too.
        for addr, verified in newdata:
            em = EmailAddress.objects.get(email=addr.email)
            self.assertEqual(em.verified, verified)

    def _initialize_formset(self, data):
        count = len(data)
        formdata = {
            'form-TOTAL_FORMS': count,
            'form-INITIAL_FORMS': count,
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': count,
        }
        for i, each in enumerate(data):
            formdata['form-{}-verified'.format(i)] = each
        return formdata


class ManageuserFormTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.mm_client.create_user('aperson@example.com', 'xxx')

    def test_user_form(self):
        form = ManageUserForm(user=self.user)
        self.assertEqual(form.initial['display_name'], self.user.display_name)
        self.assertEqual(form.changed_data, [])
        # Test that we can update the display name.
        form = ManageUserForm(dict(display_name='My User'), user=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.changed_data, ['display_name'])
        form.save()
        self.assertEqual(self.user.display_name, 'My User')
        self.assertEqual(self.user.addresses[0].display_name, 'My User')
