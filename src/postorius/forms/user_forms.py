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
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress

from postorius.forms.fields import (
    NullBooleanRadioSelect,
    delivery_mode_field,
    delivery_status_field,
    moderation_action_field,
)
from postorius.utils import LANGUAGES, with_empty_choice


class UserPreferences(forms.Form):

    """
    Form handling the user's global, address and subscription based preferences
    """

    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences', None)
        self.disabled_delivery_choices = kwargs.pop(
            'disabled_delivery_choices', []
        )
        super().__init__(*args, **kwargs)
        # Disable some options to be set.
        self.fields[
            'delivery_status'
        ].widget.disabled_choices = self.disabled_delivery_choices

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
            "list. If you don't want to receive this copy, set this option "
            'to No.'
        ),
    )
    acknowledge_posts = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Acknowledge posts'),
        help_text=_(
            'Receive acknowledgement mail when you send mail to the list?'
        ),
    )
    hide_address = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Hide address'),
        help_text=_(
            'When other members allowed to view the list membership, '
            'your email address is normally shown. '
            'If you do not want your email address to show up on this '
            'membership roster, select Yes for this option.'
        ),
    )
    receive_list_copy = forms.NullBooleanField(
        widget=NullBooleanRadioSelect(choices=choices),
        required=False,
        label=_('Receive list copies (possible duplicates)'),
        help_text=_(
            'When you are listed explicitly in the To: or Cc: headers of a '
            'list message, you can opt to not receive another copy from the '
            'mailing list. Select Yes to receive copies. '
            'Select No to avoid receiving copies from the mailing list'
        ),
    )

    preferred_language = forms.ChoiceField(
        widget=forms.Select(),
        choices=with_empty_choice(LANGUAGES),
        required=False,
        label=_('Preferred language'),
        help_text=_(
            'Preferred language for your interactions with Mailman. When '
            "this is set, it will override the MailingList's preferred "
            'language. This affects which language is used for your '
            'email notifications and such.'
        ),
    )

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """

        layout = [
            [
                'User Preferences',
                'acknowledge_posts',
                'hide_address',
                'receive_list_copy',
                'receive_own_postings',
                'delivery_mode',
                'delivery_status',
                'preferred_language',
            ]
        ]

    def save(self):
        # Note (maxking): It is possible that delivery_status field will always
        # be a part of changed_data because of how the SelectWidget() works.
        if not self.changed_data:
            return
        for key in self.changed_data:
            if self.cleaned_data[key] not in (None, ''):
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
                _('Cannot set delivery_status to {}').format(val)
            )
        # The change seems correct, just return the value.
        return val


class UserPreferencesFormset(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        self._preferences = kwargs.pop('preferences')
        self._disabled_delivery_choices = kwargs.pop(
            'disabled_delivery_choices', []
        )
        kwargs['initial'] = self._preferences
        super(UserPreferencesFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(UserPreferencesFormset, self)._construct_form(i, **kwargs)
        form._preferences = self._preferences[i]
        form.fields[
            'delivery_status'
        ].widget.disabled_choices = self._disabled_delivery_choices
        return form

    def save(self):
        for form in self.forms:
            form.save()


class ManageMemberForm(forms.Form):

    # RW fields.
    moderation_action = moderation_action_field()
    delivery_mode = delivery_mode_field()

    # TODO: Maybe add Member's preferences here to set other things like
    # delivery_mode and such?

    def __init__(self, *args, **kw):
        self.member = kw.pop('member')
        super().__init__(*args, **kw)

    @property
    def initial(self):
        return {
            'moderation_action': self.member.moderation_action,
            'delivery_mode': self.member.delivery_mode,
        }

    @initial.setter
    def initial(self, value):
        pass

    def save(self):
        """Save the data to the Member object by calling into REST API.

        Also, return True/False to determine if anything was updated or not.
        """
        if not self.changed_data:
            return False
        for each in self.changed_data:
            updated = self.cleaned_data.get(each)
            if updated not in (None, ''):
                setattr(self.member, each, updated)
        self.member.save()
        return True


class ManageMemberFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kw):
        self._members = kw.pop('members')
        kw['initial'] = self._members
        super().__init__(*args, **kw)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['member'] = self._members[index]
        return kwargs

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.member = self._members[i]
        return form

    def save(self):
        """Save and return the lists for which subs were updated"""
        updated = []
        for form in self.forms:
            was_updated = form.save()
            if was_updated:
                updated.append(form.member.list_id)
        return updated


class ManageAddressForm(forms.Form):
    # RW fields.
    verified = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False,
        label=_('Verified'),
        help_text=_('Specifies whether or not this email address is verified'),
    )

    # TODO: Primary/Preferred Address. Needs integration with EmailAddress
    # model from Django/Allauth.

    def __init__(self, *args, **kw):
        self.address = kw.pop('address')
        super().__init__(*args, **kw)

    @property
    def initial(self):
        return {'verified': self.address.verified}

    @initial.setter
    def initial(self, value):
        pass

    def save(self):
        """Save the data and return if there was anything changed."""
        if not self.changed_data:
            return False
        # Since there is a single field, the below shouldn't raise KeyError. In
        # future when more fields are added, it can raise KeyError so make sure
        # to use .get() and not do anything if value is None.
        verified = self.cleaned_data['verified']
        if verified:
            self.address.verify()
            self._update_django_address(True)
            return True
        self.address.unverify()
        self._update_django_address(False)
        return True

    def _update_django_address(self, value):
        """Verify/Unverify the EmailAddress model in Allauth."""
        try:
            email = EmailAddress.objects.get(email=self.address.email)
        except EmailAddress.DoesNotExist:
            return
        email.verified = value
        email.save()


class ManageAddressFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kw):
        self._addresses = kw.pop('addresses')
        kw['initial'] = self._addresses
        super().__init__(*args, **kw)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['address'] = self._addresses[index]
        return kwargs

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.address = self._addresses[i]
        return form

    def save(self):
        """Save and return which addresses were updated."""
        updated = []
        for form in self.forms:
            was_updated = form.save()
            if was_updated:
                updated.append(form.address.email)
        return updated


class ManageUserForm(forms.Form):

    display_name = forms.CharField(label=_('Display Name'), required=True)

    def __init__(self, *args, **kw):
        self.user = kw.pop('user')
        super().__init__(*args, **kw)

    @property
    def initial(self):
        return {'display_name': self.user.display_name}

    @initial.setter
    def initial(self, value):
        pass

    def save(self):
        if not self.changed_data:
            return
        new_name = self.cleaned_data.get('display_name')
        self.user.display_name = new_name
        self.user.save()
        for addr in self.user.addresses:
            addr.display_name = new_name
            addr.save()
