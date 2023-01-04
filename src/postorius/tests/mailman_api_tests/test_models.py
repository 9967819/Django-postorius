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

from postorius.models import MailmanListManager
from postorius.tests.utils import ViewTestCase


class TestMailmanListManager(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.domain2 = self.mm_client.create_domain('most-desirable.org')
        self.foo_list = self.domain.create_list('foo')
        self.bar_list = self.domain.create_list('bar')
        self.baz_list = self.domain2.create_list('baz')
        self.list_manager = MailmanListManager()

    def test_get_all_mailinglists(self):
        lists = self.list_manager.all()
        # This should return all the 2 mailing lists that we have.
        self.assertEqual(len(lists), 3)
        self.assertEqual(
            [x.fqdn_listname for x in lists],
            ['bar@example.com', 'baz@most-desirable.org', 'foo@example.com'],
        )

    def test_get_by_mail_host(self):
        lists = self.list_manager.by_mail_host('example.com')
        self.assertEqual(len(lists), 2)
        self.assertEqual(
            [x.fqdn_listname for x in lists],
            ['bar@example.com', 'foo@example.com'],
        )

    def test_get_single_mailinglist(self):
        mlist = self.list_manager.get('baz@most-desirable.org')
        self.assertIsNotNone(mlist)
        self.assertEqual(str(mlist), str(self.baz_list))
