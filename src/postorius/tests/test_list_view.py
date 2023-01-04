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


from django.contrib.messages.storage.base import BaseStorage, Message
from django.test import TestCase
from django.test.client import RequestFactory

from mailmanclient import MailingList

from postorius.views.list import ListMembersViews


class LocalStorage(BaseStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._storage = []

    def _get(self, *args, **kwargs):
        return self._storage, True

    def _store(self, messages, response, *args, **kwargs):
        if messages:
            self._storage = messages
        else:
            self._storage = []
        return []


class TestListView(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_error_message(self):
        mailing_list_data = {'list_id': 'test_list.example.com'}
        mailing_list = MailingList(None, None, data=mailing_list_data)
        view = ListMembersViews(mailing_list=mailing_list)
        request_data = {'email': ['.*@example.com'], 'display_name': ['']}
        request = self.request_factory.post(
            '/postorius/lists/test_list.example.com/members/nonmember/',
            data=request_data,
        )
        request._messages = LocalStorage(request)
        view.post(request, 'test_list.example.com', role='nonmember')
        self.assertTrue(len(request._messages))
        self.assertIsInstance(list(request._messages)[0], Message)
