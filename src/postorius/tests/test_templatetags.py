# -*- coding: utf-8 -*-
# Copyright (C) 2019-2021 by the Free Software Foundation, Inc.
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

from django.test import SimpleTestCase

from postorius.templatetags.date_helpers import datetime_parse


class TestDatetimeParser(SimpleTestCase):

    def test_datetime_parse(self):
        value = '2005-08-01T07:49:23'
        parsed_date = datetime_parse(value)
        # Make sure the parsing actually worked.
        self.assertFalse(parsed_date is value)
        self.assertTrue(isinstance(parsed_date, datetime.datetime))
        self.assertEqual(parsed_date.strftime('%Y %m %d, %H %M'),
                         '2005 08 01, 07 49')

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
