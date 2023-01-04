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

from django import forms
from django.utils.translation import gettext_lazy as _


class MemberForm(forms.Form):
    """Assign a role to the member"""

    email = forms.EmailField(
        label=_('Email Address'),
        error_messages={
            'required': _('Please enter an email address.'),
            'invalid': _('Please enter a valid email address.'),
        },
    )
    display_name = forms.CharField(
        label=_('Display Name'),
        required=False,
        error_messages={'invalid': _('Please enter a display name.')},
    )
