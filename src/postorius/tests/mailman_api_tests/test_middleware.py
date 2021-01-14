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

# from django.test import RequestFactory, TestCase
# from django.urls import reverse

# import mock
# from mailmanclient import MailmanConnectionError

# from postorius.models import MailmanApiError


# class TestMiddleware(TestCase):

#     def setUp(self):
#         self.factory = RequestFactory()

#     @mock.patch('requests.request')
#     @mock.patch('postorius.views.list.list_index')
#     def test_middleware_request(self, mock_request, mock_list_index):
#         # Mock the view function to raise MailmanApiError and verify
#         # the behavior of the middleware function.
#         mock_list_index.side_effect = MailmanApiError
#         response = self.client.get(reverse('list_index'))
#         # Check that correct error page is rendered.
#         self.assertEqual('Mailman REST API not available. Please start Mailman core.',    # noqa
#                          response.context['error'])
#         mock_list_index.reset_mock()
#         # Check similar semantics with MailmanConnectionError from
#         # mailmanclient.
#         mock_list_index.side_effect = MailmanConnectionError
#         response = self.client.get(reverse('list_index'))
#         self.assertEqual('Mailman REST API not available. Please start Mailman core.',    # noqa
#                          response.context['error'])
