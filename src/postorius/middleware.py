# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 by the Free Software Foundation, Inc.
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
