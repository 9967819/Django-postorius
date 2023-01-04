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

import os
import tempfile
from unittest.mock import MagicMock

from django.conf import settings
from django.contrib import messages
from django.test import TransactionTestCase
from django.urls import reverse

from django_mailman3.lib.mailman import get_mailman_client
from django_mailman3.tests.utils import get_flash_messages
from six import PY3, binary_type, text_type
from six.moves.urllib_parse import (
    parse_qsl,
    quote,
    urlencode,
    urlparse,
    urlunparse,
)


def get_test_file(*fileparts):
    return os.path.join(os.path.dirname(__file__), 'test_data', *fileparts)


get_test_file.__test__ = False  # noqa: E305


def reorder_request_params(request):
    def reorder_params(params):
        parsed = None
        if PY3:
            if isinstance(params, binary_type):
                params = params.decode('ascii')
            parsed = parse_qsl(params, encoding='utf-8')
        else:
            parsed = parse_qsl(params)
        if parsed:
            return urlencode(sorted(parsed, key=lambda kv: kv[0]))
        else:
            # Parsing failed, it may be a simple string.
            return params
        # sort the URL query-string by key names.

    uri_parts = urlparse(request.uri)
    if uri_parts.query:
        request.uri = urlunparse(
            (
                uri_parts.scheme,
                uri_parts.netloc,
                uri_parts.path,
                uri_parts.params,
                reorder_params(uri_parts.query),
                uri_parts.fragment,
            )
        )
        # convert the request body to text and sort the parameters.
    if isinstance(request.body, binary_type):
        try:
            request._body = request._body.decode('utf-8')
        except UnicodeDecodeError:
            pass
    if isinstance(request.body, text_type):
        request._body = reorder_params(request._body.encode('utf-8'))
    return request


def filter_response_headers(response):
    for header in ('Date', 'Server', 'date', 'server'):
        # The headers are lowercase on Python 2 and capitalized on Python 3
        if header in response['headers']:
            del response['headers'][header]
    return response


def create_mock_domain(properties=None):
    """Create and return a mocked Domain.

    :param properties: A dictionary of the domain's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='Domain')
    mock_object.contact_address = ''
    mock_object.description = ''
    mock_object.mail_host = ''
    mock_object.lists = []
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


def create_mock_list(properties=None):
    """Create and return a mocked List.

    :param properties: A dictionary of the list's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='List')
    mock_object.members = []
    mock_object.moderators = []
    mock_object.owners = []
    # like in mock_domain, some defaults need to be added...
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


def create_mock_member(properties=None):
    """Create and return a mocked Member.

    :param properties: A dictionary of the member's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='Member')
    # like in mock_domain, some defaults need to be added...
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


class ViewTestCase(TransactionTestCase):
    def setUp(self):
        self.mm_client = get_mailman_client()

    def tearDown(self):
        for d in self.mm_client.domains:
            d.delete()
        for u in self.mm_client.users:
            u.delete()

    def assertHasSuccessMessage(self, response, count=1):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), count)
        self.assertEqual(
            msgs[0].level,
            messages.SUCCESS,
            '%s: %s' % (messages.DEFAULT_TAGS[msgs[0].level], msgs[0].message),
        )
        return msgs[0].message

    def assertHasErrorMessage(self, response):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].level,
            messages.ERROR,
            '%s: %s' % (messages.DEFAULT_TAGS[msgs[0].level], msgs[0].message),
        )
        return msgs[0].message

    def assertHasNoMessage(self, response):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 0)

    def assertRedirectsToLogin(self, url):
        response = self.client.get(url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse(settings.LOGIN_URL), quote(url)),
        )

    @classmethod
    def write_response(cls, response):
        """Print the response in a tmp file and open it in browser."""
        tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
        tmp.write(response.content)
        tmp.close()
        print(f'Wrote response to  file://{tmp.name}')
