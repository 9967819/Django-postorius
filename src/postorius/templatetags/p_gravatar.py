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

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from django_gravatar.templatetags.gravatar import gravatar as gravatar_orig


register = template.Library()


@register.simple_tag()
def gravatar(*args, **kw):
    """A proxy for django-gravatar's template.

    This templatetag allows disabling Gravatar altogether using
    HYPERKITTY_ENABLE_GRAVATAR setting, which is True by default.
    """
    if not getattr(settings, 'HYPERKITTY_ENABLE_GRAVATAR', True):
        return mark_safe('')
    return gravatar_orig(*args, **kw)
