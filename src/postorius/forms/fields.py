# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 by the Free Software Foundation, Inc.
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
from django.utils.encoding import smart_text
from django.utils.translation import gettext_lazy as _


class ListOfStringsField(forms.Field):
    widget = forms.widgets.Textarea

    def prepare_value(self, value):
        if isinstance(value, list):
            value = '\n'.join(value)
        return value

    def to_python(self, value):
        "Returns a list of Unicode object."
        if value in self.empty_values:
            return []
        result = []
        for line in value.splitlines():
            line = line.strip()
            if not line:
                continue
            result.append(smart_text(line))
        return result


class NullBooleanRadioSelect(forms.RadioSelect):
    """
    This is necessary to detect that such a field has not been changed.
    """

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        return {'2': True,
                True: True,
                'True': True,
                '3': False,
                'False': False,
                False: False}.get(value, None)


class SiteModelChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "%s (%s)" % (obj.name, obj.domain)


class MultipleChoiceForm(forms.Form):

    class MultipleChoiceField(forms.MultipleChoiceField):

        def validate(self, value):
            pass

    choices = MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_choices(self):
        if len(self.cleaned_data['choices']) < 1:
            raise forms.ValidationError(_('Make at least one selection'))
        return self.cleaned_data['choices']
