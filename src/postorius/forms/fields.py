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


try:
    from django.utils.encoding import smart_str
except ImportError:
    # django < 4.0
    from django.utils.encoding import smart_text as smart_str

from django.utils.translation import gettext_lazy as _

from postorius.utils import with_empty_choice


DELIVERY_MODE_CHOICES = (
    ('regular', _('Regular')),
    ('plaintext_digests', _('Plain Text Digests')),
    ('mime_digests', _('MIME Digests')),
    ('summary_digests', _('Summary Digests')),
)


DELIVERY_STATUS_CHOICES = (
    ('enabled', _('Enabled')),
    ('by_user', _('Disabled')),
    ('by_moderator', _('Disabled by Owner')),
    ('by_bounces', _('Disabled by Bounces')),
)

ACTION_CHOICES = (
    ('hold', _('Hold for moderation')),
    ('reject', _('Reject (with notification)')),
    ('discard', _('Discard (no notification)')),
    ('accept', _('Accept immediately (bypass other rules)')),
    ('defer', _('Default processing')),
)


class ListOfStringsField(forms.Field):
    widget = forms.widgets.Textarea

    def prepare_value(self, value):
        if isinstance(value, list):
            value = '\n'.join(value)
        return value

    def to_python(self, value):
        """Returns a list of Unicode object."""
        if value in self.empty_values:
            return []
        result = []
        for line in value.splitlines():
            line = line.strip()
            if not line:
                continue
            result.append(smart_str(line))
        return result


class NullBooleanRadioSelect(forms.RadioSelect):
    """
    This is necessary to detect that such a field has not been changed.
    """

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        return {
            '2': True,
            True: True,
            'True': True,
            '3': False,
            'False': False,
            False: False,
        }.get(value, None)


class SelectWidget(forms.Select):
    """
    Subclass of Django's select widget that allows disabling options.
    """

    def __init__(self, *args, **kwargs):
        self._disabled_choices = []
        super().__init__(*args, **kwargs)

    @property
    def disabled_choices(self):
        return self._disabled_choices

    @disabled_choices.setter
    def disabled_choices(self, other):
        self._disabled_choices = other

    def create_option(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)
        if value in self.disabled_choices:
            option_dict['attrs']['disabled'] = 'disabled'
            return option_dict
        return option_dict


class SiteModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '%s (%s)' % (obj.name, obj.domain)


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


def delivery_mode_field(default=None):

    return forms.ChoiceField(
        widget=forms.Select(),
        choices=with_empty_choice(DELIVERY_MODE_CHOICES),
        required=False,
        initial=default,
        label=_('Delivery mode'),
        help_text=_(
            "If you select digests , you'll get posts bundled "
            'together (usually one per day but possibly more on busy lists), '
            "instead of singly when they're sent. Your mail reader may or "
            'may not support MIME digests. In general MIME digests are '
            'preferred, but if you have a problem reading them, select '
            'plain text digests. '
            'Summary Digests are currently equivalent to MIME Digests.'
        ),
    )


def delivery_status_field(choices=None, widget=None):
    if not choices:
        choices = with_empty_choice(DELIVERY_STATUS_CHOICES)

    if not widget:
        widget = SelectWidget

    return forms.ChoiceField(
        widget=widget(),
        choices=choices,
        required=False,
        label=_('Delivery status'),
        help_text=_(
            'Set this option to Enabled to receive messages posted to this '
            'mailing list. Set it to Disabled if you want to stay subscribed, '
            "but don't want mail delivered to you for a while (e.g. you're "
            "going on vacation). If you disable mail delivery, don't forget "
            'to re-enable it when you come back; it will not be automatically '
            're-enabled.'
        ),
    )


def moderation_action_field():
    return forms.ChoiceField(
        widget=forms.Select(),
        label=_('Moderation'),
        required=False,
        choices=[(None, _('List default'))] + list(ACTION_CHOICES),
        help_text=_(
            'Default action to take when this member posts to the list. \n'
            "List default -- follow the list's default member action. \n"
            'Hold -- This holds the message for approval by the list '
            'moderators. \n'
            'Reject -- this automatically rejects the message by sending a '
            "bounce notice to the post's author. The text of the bounce "
            'notice can be configured by you. \n'
            'Discard -- this simply discards the message, with no notice '
            "sent to the post's author. \n"
            'Accept -- accepts any postings without any further checks. \n'
            'Default Processing -- run additional checks and accept '
            'the message. \n'
        ),
    )
