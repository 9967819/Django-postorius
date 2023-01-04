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
from django import template
from django.utils.dateparse import parse_datetime


register = template.Library()


@register.filter
def datetime_parse(value):
    """Parse string value into datetime object."""
    try:
        return parse_datetime(value)
    except ValueError:
        # If they are invalid dates, just return them back.
        return value
