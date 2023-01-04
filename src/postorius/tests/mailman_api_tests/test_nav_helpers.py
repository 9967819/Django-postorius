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

import time

from postorius.templatetags.nav_helpers import (
    held_count,
    pending_subscriptions,
)
from postorius.tests.utils import ViewTestCase


class TestNavigationHelpers(ViewTestCase):
    def setUp(self):
        super().setUp()
        # Create a domain.
        self.domain = self.mm_client.create_domain('example.com')
        self.mlist = self.domain.create_list('test_list')

    def tearDown(self):
        self.domain.delete()

    def test_subscription_request_count(self):
        # Initially, the count of held messages is 0.
        self.assertEqual(pending_subscriptions(self.mlist), 0)
        self.mlist.settings['subscription_policy'] = 'moderate'
        self.mlist.settings.save()
        self.mlist.subscribe('needsmoderation@example.com', pre_verified=True)
        self.assertEqual(pending_subscriptions(self.mlist), 1)
        # Make sure the ones pending user approval don't show up.
        self.mlist.settings['subscription_policy'] = 'confirm'
        self.mlist.settings.save()
        self.mlist.subscribe(
            'needsconfirmation@example.com', pre_verified=True
        )
        self.assertEqual(pending_subscriptions(self.mlist), 1)

    def test_held_message_count(self):
        # Initially, the count of held messages is 0.
        self.assertEqual(held_count(self.mlist), 0)
        # Now, let's inject some message.
        msg = """\
From: nonmember@example.com
To: test_list@example.com
Subject: What??
Message-ID: <moderated_01>

Hello.
"""
        inq = self.mm_client.queues['in']
        inq.inject('test_list.example.com', msg)
        # Wait for the message to be processed.
        while True:
            if len(inq.files) == 0:
                break
            time.sleep(0.1)
        # Wait for message to show up in held queue.
        while True:
            all_held = self.mlist.held
            if len(all_held) > 0:
                break
            time.sleep(0.1)

        self.assertEqual(held_count(self.mlist), 1)
