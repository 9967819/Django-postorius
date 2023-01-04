# -*- coding: utf-8 -*-
# Copyright (C) 2020-2023 by the Free Software Foundation, Inc.
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

from django import forms
from django.utils.translation import gettext_lazy as _


class AddBanForm(forms.Form):
    """Ban an email address or regular expression."""

    # TODO maxking: This form should only accept valid emails or regular
    # expressions. Anything else that doesn't look like a valid email address
    # or regexp for email should not be a valid value for the field. However,
    # checking for that might not be easy.
    email = forms.CharField(
        label=_('Add ban'),
        help_text=_(
            'You can ban a single email address or use a regular expression '
            'to match similar email addresses.'
        ),
        error_messages={
            'required': _('Please enter an email address.'),
            'invalid': _('Please enter a valid email address.'),
        },
    )
