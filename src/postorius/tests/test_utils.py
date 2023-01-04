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
from django.test import RequestFactory, TestCase

from postorius.utils import render_api_error


class TestUtils(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_render_api_error_works(self):
        request = self.factory.get('/postorius/lists')
        response = render_api_error(request)
        self.assertTrue(
            'Mailman REST API not available.' in str(response.content)
        )
        self.assertEqual(response.status_code, 503)
