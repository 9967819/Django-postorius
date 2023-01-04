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
import json
import time
from email import message_from_bytes, message_from_file

from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from postorius.tests.utils import ViewTestCase, get_test_file, reverse
from postorius.views.rest import get_attachments, parse


class TestRestViews(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            email='bob@example.com', password='testpass'
        )
        self.su = User.objects.create_superuser(
            username='alice', email='alice@example.com', password='testpass'
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True
        )
        EmailAddress.objects.create(
            user=self.su, email=self.su.email, verified=True
        )
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')

    def test_get_attachments(self):
        with open(get_test_file('test-email-attachment.txt')) as fp:
            attachments = get_attachments(fp.read())
        self.assertEqual(len(attachments), 1)
        at1 = attachments[0]
        self.assertEqual(at1[1], 'signature.asc')
        self.assertEqual(at1[2], 'application/pgp-signature')

    def test_get_attachments_bad_charset(self):
        # While this part is supposed to be handled by Django-Mailman3.
        # This should nor fail or error out.
        with open(get_test_file('bad-email.txt')) as fp:
            attachments = get_attachments(fp.read())
        self.assertEqual(len(attachments), 0)

    def test_parsed_email(self):
        with open(get_test_file('simple-email.txt')) as fp:
            retval = parse(fp.read())
        self.assertTrue('This is a test message.' in retval['body'])
        for header_str in [
            'From: gil <puntogil@libero.it>',
            'Content-Type: multipart/mixed;',
            'Sender: devel-bounces@lists.fedoraproject.org',
        ]:
            self.assertTrue(header_str, retval['headers'])


class TestGetHeldMessage(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            email='bob@example.com', password='testpass'
        )
        self.su = User.objects.create_superuser(
            username='alice', email='alice@example.com', password='testpass'
        )
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True
        )
        EmailAddress.objects.create(
            user=self.su, email=self.su.email, verified=True
        )
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.inq = self.mm_client.queues['in']
        with open(get_test_file('test-email-attachment.txt')) as fp:
            message = message_from_file(fp)
        # Now, we inject a non-member post to this email list to simulate a
        # held message.
        self.inq.inject('foo.example.com', message.as_string())
        # We sleep till this message is processed and held.
        time.sleep(2)

    def test_get_held_message(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.get(
            reverse('rest_held_message', args=['foo.example.com', '1'])
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            sorted(list(content.keys())),
            [
                'attachments',
                'hold_date',
                'msg',
                'msgid',
                'reason',
                'sender',
                'subject',
            ],
        )   # noqa
        self.assertEqual(content['msgid'], 1)
        self.assertEqual(len(content['attachments']), 1)
        attachment_uri = content['attachments'][0]
        # Now we will get this attachment.
        self.client.get(attachment_uri)

    def test_get_raw_held_message(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.get(
            reverse('rest_held_message', args=['foo.example.com', '1']),
            {'raw': 'True'},
        )
        self.assertEqual(response.status_code, 200)
        email = message_from_bytes(response.content)
        self.assertIsNotNone(email)

    def test_get_attachments_for_held_message(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.get(
            reverse('rest_held_message', args=['foo.example.com', '1'])
        )
        self.assertEqual(response.status_code, 200)
        attachment_uri = json.loads(response.content.decode('utf-8'))[
            'attachments'
        ][0][
            0
        ]   # noqa: E501
        # Now we will get this attachment.
        response = self.client.get(attachment_uri)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('BEGIN PGP SIGNATURE' in str(response.content))
