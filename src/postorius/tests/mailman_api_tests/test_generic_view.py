# -*- coding: utf-8 -*-
# Copyright (C) 2018-2023 by the Free Software Foundation, Inc.
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

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from postorius.views.generic import MailingListView


class TestGenericView(TestCase):
    """Test generic view adds templates and Mailing List."""

    def setUp(self):
        # We first create a test view that is based on the MailingListView.
        # This view only implements a POST and no GET.
        class TestView(MailingListView):
            def post(self, request):
                return HttpResponse(status=200)

        self.view = TestView.as_view()
        self.factory = RequestFactory()

    def test_no_GET_in_view(self):
        request = self.factory.post('/')
        request.user = AnonymousUser()
        # Since out view implements a POST, we shouldn't get an ERROR here.
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        # Now, let's try a GET request.
        request = self.factory.get('/')
        request.user = AnonymousUser()
        # We shouldn't a ImproperlyConfigured error with GET but 405 error.
        response = self.view(request)
        self.assertEqual(response.status_code, 405)
