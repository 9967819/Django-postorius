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


from django.test import TestCase

from postorius.forms import MemberForm


class TestMemberForm(TestCase):
    def test_form_labels(self):
        form = MemberForm({})
        self.assertTrue('email' in form.fields.keys())
        self.assertEqual(form.fields['email'].label, 'Email Address')
        self.assertTrue('display_name' in form.fields.keys())
        self.assertEqual(form.fields['display_name'].label, 'Display Name')

    def test_form_errors(self):
        form = MemberForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['email'][0], 'Please enter an email address.'
        )
        form = MemberForm({'email': 'invalid.example.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['email'][0], 'Please enter a valid email address.'
        )
