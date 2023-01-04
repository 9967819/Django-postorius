# -*- coding: utf-8 -*-
# Copyright (C) 2015-2023 by the Free Software Foundation, Inc.
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

import logging
from urllib.error import HTTPError

from django_mailman3.lib import mailman
from mailmanclient import MailmanConnectionError

from postorius import utils
from postorius.models import MailmanApiError


logger = logging.getLogger('postorius')


__all__ = [
    'PostoriusMiddleware',
]


class PostoriusMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, (MailmanApiError, MailmanConnectionError)):
            logger.exception('Mailman REST API not available')
            return utils.render_api_error(request)
        elif isinstance(exception, HTTPError):
            logger.exception('Un-handled exception: %s', str(exception))
            return utils.render_client_error(request, exception)


class APICountingMiddleware:
    """Counts the total number of API calls made to Core and prints summary.

    It hooks into mailmanclient's hooking mechanism, facilitated by
    ``django_mailman3.lib.mailman.mailmanclient_request_hook``. It stores the
    parameter of each API call made in `self.api_call_counter()` and prints it
    *before* returning the response in `__call__`.

    It hooks up ``_trace_api_calls()`` method into the Hooks API. Even if the
    hooking happens multiple times, it is only added once since it
    deduplicates the hooks.

    Output looks something like:

    DEBUG: =======================
    DEBUG: Handle reqsponse for /postorius/lists/mylist.lists.araj.me/settings/
    DEBUG: View function was postorius.views.list.list_settings
    DEBUG: 4 calls to API
    DEBUG: [GET] http://localhost:8001/3.1/lists/mylist.lists.araj.me with None
    DEBUG: [snip]
    DEBUG: ======================

    Note: If you don't see the output on console, check the 'postorius' logger
    settings and make sure that it has `console` handler and level is set to
    'DEBUG'.

    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        mailman.mailmanclient_request_hook(self._trace_api_calls)
        self.api_call_counter = []
        self.view_func = ''

    def __call__(self, request):
        self.request = request
        response = self.get_response(request)
        logger.debug('=======================')
        logger.debug('Handle reqsponse for %s', request.path)
        logger.debug('View function was %s', self.view_func)
        logger.debug('%s calls to API', len(self.api_call_counter))
        for each in self.api_call_counter:
            logger.debug(
                '[%s] %s with %s',
                each.get('method'),
                each.get('url'),
                each.get('data'),
            )
        logger.debug('=======================')
        self.api_call_counter = []
        return response

    def _trace_api_calls(self, params):
        """Hook that adds all the call parameters to self.api_call_counter.

        :param params: List of request params from mailmanclient.
        """
        self.api_call_counter.append(params)
        return params

    def process_view(self, request, view_func, view_args, view_kwars):
        """Get a pointer to view function object."""
        self.view_func = '{}.{}'.format(
            view_func.__module__, view_func.__name__
        )
