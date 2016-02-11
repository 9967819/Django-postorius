# -*- coding: utf-8 -*-
# Copyright (C) 2016 by the Free Software Foundation, Inc.
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

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.test import TestCase

from postorius.forms import AddressActivationForm
from postorius.models import AddressConfirmationProfile
from postorius.tests import MM_VCR
from postorius.tests.utils import get_flash_messages
from postorius.utils import get_client


vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)

class TestAddressActivationForm(TestCase):
    """
    Test the activation form.
    """

    @MM_VCR.use_cassette('test_address_activation_form.yaml')
    def setUp(self):
        # Create a user and profile.
        self.user = User.objects.create_user('testuser', 'les@example.org', 'testpass')
        self.profile = AddressConfirmationProfile.objects.create(email='les2@example.org',
                                                                         user=self.user)
        self.expired = AddressConfirmationProfile.objects.create(email='expired@example.org',
                                                                         user=self.user)
        self.expired.created -= timedelta(weeks=100)
        self.expired.save()
        self.mm_user = get_client().create_user('subscribed@example.org', 'password')

    @MM_VCR.use_cassette('test_address_activation_form.yaml')
    def tearDown(self):
        self.profile.delete()
        self.expired.delete()
        self.user.delete()
        self.mm_user.delete()

    @MM_VCR.use_cassette('test_address_activation_form.yaml')
    def test_valid_email_is_valid(self):
        form = AddressActivationForm({'email': 'very_new_email@example.org',})
        self.assertTrue(form.is_valid())

    def test_email_used_by_django_auth_is_invalid(self):
        # No need for cassette because we should check mailman last since it's the most expensive
        form = AddressActivationForm({'email': 'les@example.org',})
        self.assertFalse(form.is_valid())

    def test_invalid_email_is_not_valid(self):
        # No need for cassette because we should check mailman last since it's the most expensive
        form = AddressActivationForm({'email': 'les@example',})
        self.assertFalse(form.is_valid())

    @MM_VCR.use_cassette('test_address_activation_form.yaml')
    def test_email_used_by_expired_confirmation_profile_is_valid(self):
        form = AddressActivationForm({'email': 'expired@example.org',})
        self.assertTrue(form.is_valid())

    @MM_VCR.use_cassette('test_address_activation_form.yaml')
    def test_email_used_by_mailman_is_invalid(self):
        form = AddressActivationForm({'email': 'subscribed@example.org',})
        self.assertFalse(form.is_valid())


class TestAddressConfirmationProfile(TestCase):
    """
    Test the confirmation of an email address activation (validating token,
    expiration, Mailman API calls etc.).
    """

    def setUp(self):
        # Create a user and profile.
        self.user = User.objects.create_user(
            username=u'ler_mm', email=u'ler@mailman.mostdesirable.org',
            password=u'pwd')
        self.profile = AddressConfirmationProfile.objects.create(email=u'les@example.org',
                                                                 user=self.user)
        # Create a test request object
        self.request = RequestFactory().get('/')

    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        mail.outbox = []

    def test_profile_creation(self):
        # Profile is created and has all necessary properties.
        self.assertEqual(self.profile.email, u'les@example.org')
        self.assertEqual(len(self.profile.activation_key), 32)
        self.assertTrue(type(self.profile.created), datetime)

    def test_unicode_representation(self):
        # Correct unicode representation?
        self.assertEqual(unicode(self.profile),
                         'Address Confirmation Profile for les@example.org')

    def test_profile_not_expired_default_setting(self):
        # A profile created less then a day ago is not expired by default.
        delta = timedelta(hours=23)
        now = datetime.now()
        self.profile.created = now - delta
        self.assertFalse(self.profile.is_expired)

    def test_profile_is_expired_default_setting(self):
        # A profile older than 1 day is expired by default.
        delta = timedelta(days=1, hours=1)
        now = datetime.now()
        self.profile.created = now - delta
        self.assertTrue(self.profile.is_expired)

    def test_profile_is_updated_on_save(self):
        key = self.profile.activation_key
        created = self.profile.created
        self.profile.save()
        self.assertNotEqual(self.profile.activation_key, key)
        self.assertNotEqual(self.profile.created, created)

    @override_settings(
        EMAIL_CONFIRMATION_EXPIRATION_DELTA=timedelta(hours=5))
    def test_profile_not_expired(self):
        # A profile older than the timedelta set in the settings is
        # expired.
        delta = timedelta(hours=6)
        now = datetime.now()
        self.profile.created = now - delta
        self.assertTrue(self.profile.is_expired)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_CONFIRMATION_FROM='mailman@mostdesirable.org')
    def test_confirmation_link(self):
        # The profile obj can send out a confirmation email.
        # Simulate a VirtualHost with a different name
        self.request.META["HTTP_HOST"] = "another-virtualhost"
        # Now send the email
        self.profile.send_confirmation_link(self.request)
        self.assertEqual(mail.outbox[0].to[0], u'les@example.org')
        self.assertEqual(mail.outbox[0].subject, u'Confirmation needed')
        self.assertIn(self.profile.activation_key, mail.outbox[0].body)
        self.assertIn("another-virtualhost", mail.outbox[0].body)


class TestAddressActivationLinkSuccess(TestCase):
    """
    This tests the activation link view if the key is valid and the profile is
    not expired.
    """

    @MM_VCR.use_cassette('test_address_activation_link.yaml')
    def setUp(self):
        self.user = User.objects.create_user(
            username='ler', email=u'ler@example.org',
            password='pwd')
        self.mm_user = get_client().create_user('ler@example.org', None)
        self.profile = AddressConfirmationProfile.objects.create(email=u'les@example.org', user=self.user)
        self.profile.save()

    @MM_VCR.use_cassette('test_address_activation_link.yaml')
    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        self.mm_user.delete()

    @MM_VCR.use_cassette('test_address_activation_link.yaml')
    def test_add_address(self):
        # An activation key pointing to a valid profile adds the address
        # to the user.
        self.client.login(username='ler', password='pwd')
        url = reverse('address_activation_link',
                      args=[self.profile.activation_key])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('user_profile'))
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].level, messages.SUCCESS, msgs[0].message)
        self.assertEqual(
            set([a.email for a in self.mm_user.addresses]),
            set(['ler@example.org', 'les@example.org']))
        try:
            logged_in_user = response.wsgi_request.user
        except AttributeError:
            # Django 1.6: the wsgi request is not available, ignore this last
            # assertion.
            pass
        else:
            self.assertEqual(logged_in_user.other_emails, ['les@example.org'])
