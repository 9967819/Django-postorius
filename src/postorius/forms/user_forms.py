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
from django.utils.translation import gettext_lazy as _

from postorius.forms.fields import NullBooleanRadioSelect
from postorius.utils import LANGUAGES, with_empty_choice


class UserPreferences(forms.Form):

    """
    Form handling the user's global, address and subscription based preferences
    """

    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences', None)
        super(UserPreferences, self).__init__(*args, **kwargs)

    @property
    def initial(self):
        # Redirect to the preferences, this allows setting the preferences
        # after instanciation and it will also set the initial data.
        return self._preferences or {}

    @initial.setter
    def initial(self, value):
        pass

    choices = ((True, _('Yes')), (False, _('No')))

    delivery_mode_choices = (("regular", _('Regular')),
                             ("plaintext_digests", _('Plain Text Digests')),
                             ("mime_digests", _('Mime Digests')),
                             ("summary_digests", _('Summary Digests')))
    delivery_status_choices = (
        ("enabled", _('Enabled')), ("by_user", _('Disabled')))
    delivery_status = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=delivery_status_choices,
        required=False,
        label=_('Delivery status'),
        help_text=_(
            'Set this option to Enabled to receive messages posted to this '
            'mailing list. Set it to Disabled if you want to stay subscribed, '
            'but don\'t want mail delivered to you for a while (e.g. you\'re '
            'going on vacation). If you disable mail delivery, don\'t forget '
            'to re-enable it when you come back; it will not be automatically '
            're-enabled.'))
    delivery_mode = forms.ChoiceField(
        widget=forms.Select(),
        choices=with_empty_choice(delivery_mode_choices),
        required=False,
        label=_('Delivery mode'),
        help_text=_(
            'If you select summary digests , you\'ll get posts bundled '
            'together (usually one per day but possibly more on busy lists), '
            'instead of singly when they\'re sent. Your mail reader may or '
            'may not support MIME digests. In general MIME digests are '
            'preferred, but if you have a problem reading them, select '
            'plain text digests.'))
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
        if not self.changed_data:
            return
        for key in self.changed_data:
            if self.cleaned_data[key] is not None:
                # None: nothing set yet. Remember to remove this test
                # when Mailman accepts None as a "reset to default"
                # value.
                self._preferences[key] = self.cleaned_data[key]
        self._preferences.save()


class UserPreferencesFormset(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences')
        kwargs["initial"] = self._preferences
        super(UserPreferencesFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(UserPreferencesFormset, self)._construct_form(i, **kwargs)
        form._preferences = self._preferences[i]
        return form

    def save(self):
        for form in self.forms:
            form.save()
