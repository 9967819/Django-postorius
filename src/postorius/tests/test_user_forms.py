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

from django.test import TestCase

from postorius.forms.user_forms import UserPreferences


class UserPreferencesTest(TestCase):
    def test_form_fields_valid(self):
        form = UserPreferences(
            {
                'acknowledge_posts': 'True',
                'hide_address': 'True',
                'receive_list_copy': 'False',
                'receive_own_postings': 'False',
            }
        )
        self.assertTrue(form.is_valid())

    def test_disabled_fields(self):
        # Test that when some fields are disabled, their widgets actually have
        # the right attrs set.
        form = UserPreferences({}, disabled_delivery_choices=['by_moderator'])
        self.assertTrue(form.is_valid())
        # Verify that the disabled choices are set on the widget.
        self.assertEqual(
            form.fields['delivery_status'].widget.disabled_choices,
            ['by_moderator'],
        )
        delivery_status_field = None
        for each in form.visible_fields():
            if each.name == 'delivery_status':
                delivery_status_field = each
                break
        # Make sure the field is actually disabled in the form html.
        self.assertIsNotNone(delivery_status_field)
        self.assertTrue(
            '<option value="by_moderator" disabled="disabled">'
            'Disabled by Admin</option>',
            str(delivery_status_field),
        )

    def test_value_for_disabled_field_cannot_be_set(self):
        # Initially, this value is set to by_bounces, it shouldn't change on
        # saving the form.
        initial = {
            'acknowledge_posts': 'True',
            'hide_address': 'True',
            'receive_list_copy': 'False',
            'receive_own_postings': 'True',
            'delivery_status': 'by_bounces',
        }

        # Mock preferences obj that can be saved.
        class Pref(dict):
            def save(self):
                pass

        preferences = Pref()
        #  A user can set the delivery_status field to any value other than
        #  disabled_choices
        form = UserPreferences(
            dict(delivery_status='by_user'),
            initial=initial,
            preferences=preferences,
            disabled_delivery_choices=['by_moderator', 'by_bounces'],
        )
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        form.save()
        # Verify that the preference object was updated to that value.
        self.assertEqual(preferences, {'delivery_status': 'by_user'})

        # If the intial value was by_bounces, it can still be saved.
        preferences = Pref()
        form = UserPreferences(
            dict(hide_address='False'),
            initial=initial,
            preferences=preferences,
            disabled_delivery_choices=['by_moderator', 'by_bounces'],
        )
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        form.save()
        # Verify that the preference object was updated to that value.
        self.assertEqual(preferences, {'hide_address': False})

        # If the value is set to a disabled choice, it raises validaiton error.
        preferences = Pref()
        form = UserPreferences(
            dict(delivery_status='by_moderator'),
            initial=initial,
            preferences=preferences,
            disabled_delivery_choices=['by_moderator', 'by_bounces'],
        )
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors.get('delivery_status')[0],
            'Cannot set delivery_status to by_moderator',
        )
