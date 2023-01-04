# -*- coding: utf-8 -*-
# Copyright (C) 2012-2023 by the Free Software Foundation, Inc.
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

from django.utils import timezone

from postorius import __version__


logger = logging.getLogger(__name__)
# The day of the month which we celebrate as Mailman Day!
MAILMAN_DAY = 1


def postorius(request):
    """Add template variables to context."""
    return dict(
        POSTORIUS_VERSION=__version__,
        # Mailman Day is first of every month.
        mailman_day=(timezone.localtime(timezone.now()).day == MAILMAN_DAY),
    )
