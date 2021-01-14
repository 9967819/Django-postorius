# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 by the Free Software Foundation, Inc.
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
        form = UserPreferences({
            'acknowledge_posts': 'True',
            'hide_address': 'True',
            'receive_list_copy': 'False',
            'receive_own_postings': 'False',
        })
        self.assertTrue(form.is_valid())
