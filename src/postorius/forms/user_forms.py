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
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from postorius.forms.fields import (
    NullBooleanRadioSelect, delivery_mode_field, delivery_status_field)
from postorius.utils import LANGUAGES, with_empty_choice


class UserPreferences(forms.Form):

    """
    Form handling the user's global, address and subscription based preferences
    """

    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences', None)
        self.disabled_delivery_choices = kwargs.pop(
            'disabled_delivery_choices', [])
        super().__init__(*args, **kwargs)
        # Disable some options to be set.
        self.fields['delivery_status'].widget.disabled_choices = (
            self.disabled_delivery_choices)

    @property
    def initial(self):
        # Redirect to the preferences, this allows setting the preferences
        # after instanciation and it will also set the initial data.
        return self._preferences or {}

    @initial.setter
    def initial(self, value):
        pass

    choices = ((True, _('Yes')), (False, _('No')))

    delivery_status = delivery_status_field()
    delivery_mode = delivery_mode_field()
    receive_own_postings = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Receive own postings'),
        help_text=_(
            'Ordinarily, you will get a copy of every message you post to the '
            'list. If you don\'t want to receive this copy, set this option '
            'to No.'
        ))
    acknowledge_posts = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Acknowledge posts'),
        help_text=_(
            'Receive acknowledgement mail when you send mail to the list?'))
    hide_address = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Hide address'),
        help_text=_(
            'When someone views the list membership, your email address is '
            'normally shown (in an obscured fashion to thwart spam '
            'harvesters). '
            'If you do not want your email address to show up on this '
            'membership roster at all, select Yes for this option.'))
    receive_list_copy = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Receive list copies (possible duplicates)'),
        help_text=_(
            'When you are listed explicitly in the To: or Cc: headers of a '
            'list message, you can opt to not receive another copy from the '
            'mailing list. Select Yes to receive copies. '
            'Select No to avoid receiving copies from the mailing list'))

    preferred_language = forms.ChoiceField(
        widget=forms.Select(),
        choices=with_empty_choice(LANGUAGES),
        required=False,
        label=_('Preferred language'),
        help_text=_(
            'Preferred language for your interactions with Mailman. When '
            'this is set, it will override the MailingList\'s preferred '
            'language. This affects which language is used for your '
            'email notifications and such.'))

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """
        layout = [["User Preferences", "acknowledge_posts", "hide_address",
                   "receive_list_copy", "receive_own_postings",
                   "delivery_mode", "delivery_status", "preferred_language"]]

    def save(self):
        # Note (maxking): It is possible that delivery_status field will always
        # be a part of changed_data because of how the SelectWidget() works.
        if not self.changed_data:
            return
        for key in self.changed_data:
            if self.cleaned_data[key] is not None:
                # None: nothing set yet. Remember to remove this test
                # when Mailman accepts None as a "reset to default"
                # value.
                self._preferences[key] = self.cleaned_data[key]
        self._preferences.save()

    def clean_delivery_status(self):
        """Check that someone didn't pass the disabled value.

        This is meant to enforce that certain values are RO and can be seen but
        not set.
        """
        val = self.cleaned_data.get('delivery_status')
        # When the options are disabled in the widget, the values returned are
        # empty. Consider that as unchanged values and just return the initial
        # value of the field.
        if not val:
            return self.initial.get('delivery_status')
        # This means the value was changed, check if the change was allowed. If
        # not, just raise a ValidationError.
        if val in self.disabled_delivery_choices:
            raise ValidationError(
                _('Cannot set delivery_status to {}').format(val))
        # The change seems correct, just return the value.
        return val


class UserPreferencesFormset(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences')
        self._disabled_delivery_choices = kwargs.pop(
            'disabled_delivery_choices', [])
        kwargs["initial"] = self._preferences
        super(UserPreferencesFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(UserPreferencesFormset, self)._construct_form(i, **kwargs)
        form._preferences = self._preferences[i]
        form.fields['delivery_status'].widget.disabled_choices = (
            self._disabled_delivery_choices)
        return form

    def save(self):
        for form in self.forms:
            form.save()
