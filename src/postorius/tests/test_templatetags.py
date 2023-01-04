# -*- coding: utf-8 -*-
# Copyright (C) 2019-2023 by the Free Software Foundation, Inc.
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

import datetime
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from postorius.templatetags.date_helpers import datetime_parse
from postorius.templatetags.p_gravatar import gravatar


class TestDatetimeParser(SimpleTestCase):
    def test_datetime_parse(self):
        value = '2005-08-01T07:49:23'
        parsed_date = datetime_parse(value)
        # Make sure the parsing actually worked.
        self.assertFalse(parsed_date is value)
        self.assertTrue(isinstance(parsed_date, datetime.datetime))
        self.assertEqual(
            parsed_date.strftime('%Y %m %d, %H %M'), '2005 08 01, 07 49'
        )

    def test_invalid_dateimtime(self):
        # Things that can't be parsed as datetime are returned as None.
        value = 'someraindomstring'
        parsed_date = datetime_parse(value)
        self.assertTrue(parsed_date is None)
        # Things that can be parsed as datetime, but are invalid dates return
        # the value back.
        # 32nd Aug for example:
        value = '2005-08-32T07:49:23'
        parsed_date = datetime_parse(value)
        self.assertTrue(parsed_date is value)


class TestGravatar(SimpleTestCase):
    def test_gravatar(self):
        """Test that we call gravatar library."""
        with patch(
            'postorius' '.templatetags.' 'p_gravatar.gravatar_orig'
        ) as mock_grav:
            gravatar('aperson@example.com')
            self.assertTrue(mock_grav.called)
            mock_grav.assert_called_with('aperson@example.com')
        html = gravatar('bperson@example.com')
        self.assertEqual(
            html,
            '<img class="gravatar" src="https://secure.gravatar.com/avatar/'
            'a100672ae026b5b7a7fb2929ff533e1e.jpg?s=80&amp;d=mm&amp;r=g" '
            'width="80" height="80" alt="" />',
        )

    @override_settings(HYPERKITTY_ENABLE_GRAVATAR=False)
    def test_disabled_gravatar(self):
        with patch(
            'postorius' '.templatetags.' 'p_gravatar.gravatar_orig'
        ) as mock_grav:
            resp = gravatar('aperson@example.com')
            self.assertFalse(mock_grav.called)
            self.assertEqual(resp, '')
