# -*- coding: utf-8 -*-
# Copyright (C) 2017-2023 by the Free Software Foundation, Inc.
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

from django.contrib.sites.models import Site
from django.test import TestCase

from postorius.forms.domain_forms import (
    DomainEditForm,
    DomainForm,
    DomainOwnerForm,
)


class TestDomainEditForm(TestCase):
    def test_form_does_not_contain_mail_host(self):
        form = DomainEditForm()
        self.assertTrue('description' in form.fields)
        self.assertTrue('alias_domain' in form.fields)
        self.assertTrue('site' in form.fields)
        self.assertFalse('mail_host' in form.fields)


class TestDomainOwnerAddForm(TestCase):
    def test_form_sanity(self):
        form = DomainOwnerForm(dict(email='some'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        form = DomainOwnerForm(dict(email='some@example.com'))
        self.assertTrue(form.is_valid())


class TestDomainForm(TestCase):
    def test_form_contains_mail_host(self):
        form = DomainForm()
        self.assertTrue('description' in form.fields)
        self.assertTrue('alias_domain' in form.fields)
        self.assertTrue('site' in form.fields)
        self.assertTrue('mail_host' in form.fields)

    def test_form_labels(self):
        form = DomainForm()
        self.assertTrue(form.fields['mail_host'].label == 'Mail Host')
        self.assertTrue(form.fields['description'].label == 'Description')
        self.assertTrue(form.fields['alias_domain'].label == 'Alias Domain')
        self.assertTrue(form.fields['site'].label == 'Web Host')

    def test_error_messages(self):
        form = DomainForm(
            {
                'mail_host': 'mailman.most-desirable.org',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('site' in form.errors.keys())
        self.assertEqual(form.errors['site'][0], 'Please enter a domain name')
        form = DomainForm({'site': 1})
        self.assertFalse(form.is_valid())
        self.assertTrue('mail_host' in form.errors.keys())
        self.assertEqual(
            form.errors['mail_host'][0], 'Please enter a domain name'
        )

    def test_form_fields_validation(self):
        # With all valid values, the form should be valid.
        form = DomainForm(
            {
                'mail_host': 'mailman.most-desirable.org',
                'description': 'The Most Desirable organization',
                'site': 1,
            }
        )
        self.assertTrue(form.is_valid())
        # With a valid alias_domain the form should be valid.
        form = DomainForm(
            {
                'mail_host': 'mailman.most-desirable.org',
                'description': 'The Most Desirable organization',
                'alias_domain': 'x.most-desirable.org',
                'site': 1,
            }
        )
        self.assertTrue(form.is_valid())
        # Because there is no site_id 2 by default in Django, this form should
        # not be valid.
        form = DomainForm(
            {
                'mail_host': 'mailman.most-desirable.org',
                'description': 'The Most Desirable organization',
                'site': 2,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('site' in form.errors.keys())
        self.assertEqual(
            form.errors['site'][0],
            'Select a valid choice.'
            ' That choice is not one of the available choices.',
        )
        # Now we use an invalid value for domain name.
        form = DomainForm(
            {
                'mail_host': 'mailman@most-desirable.org',
                'description': 'The Most Desirable organization',
                'site': 1,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('mail_host' in form.errors.keys())
        self.assertEqual(
            form.errors['mail_host'][0], 'Please enter a valid domain name'
        )
        # Now we use an invalid value for alias domain.
        form = DomainForm(
            {
                'mail_host': 'mailman.most-desirable.org',
                'description': 'The Most Desirable organization',
                'alias_domain': 'x@most-desirable.org',
                'site': 1,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('alias_domain' in form.errors.keys())
        self.assertEqual(
            form.errors['alias_domain'][0],
            'Please enter a valid domain name or nothing.',
        )

    def test_site_field_values(self):
        form = DomainForm()
        self.assertTrue('site' in form.fields.keys())
        self.assertTrue(
            [x for x in form.fields['site'].choices],
            [(1, 'example.com (example.com)')],
        )
        # Now let's create a new domain and see if it shows up.
        Site.objects.create(domain='mail.most-desirable.org', name='My Domain')
        Site.objects.create(domain='dom.most-desirable.org', name='A Domain')
        # Items are ordered by "name".
        self.assertTrue(
            [x for x in form.fields['site'].choices],
            [
                (1, 'A Domain (dom.most-desirable.org)'),
                (2, 'example.com (example.com)'),
                (3, 'My Domain (mail.most-desirable.org)'),
            ],
        )
        # Initial value should be set to the current site.
        self.assertEqual(
            form.fields['site'].initial(),
            Site.objects.get(domain='example.com'),
        )
