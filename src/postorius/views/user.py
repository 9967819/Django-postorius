# -*- coding: utf-8 -*-
# Copyright (C) 1998-2021 by the Free Software Foundation, Inc.
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
from urllib.error import HTTPError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import FormView

from allauth.account.models import EmailAddress
from django_mailman3.lib.mailman import get_mailman_client, get_mailman_user

from postorius.forms import (
    ChangeSubscriptionForm, UserPreferences, UserPreferencesFormset)
from postorius.models import List, MailmanUser, SubscriptionMode
from postorius.utils import set_preferred
from postorius.views.generic import MailmanClientMixin


logger = logging.getLogger(__name__)


class UserPreferencesView(FormView, MailmanClientMixin):
    """Generic view for the logged-in user's various preferences."""

    form_class = UserPreferences

    def get_context_data(self, **kwargs):
        data = super(UserPreferencesView, self).get_context_data(**kwargs)
        data['mm_user'] = self.mm_user
        return data

    def get_form_kwargs(self):
        kwargs = super(UserPreferencesView, self).get_form_kwargs()
        kwargs['preferences'] = self._get_preferences()
        return kwargs

    def _set_view_attributes(self, request, *args, **kwargs):
        self.mm_user = MailmanUser.objects.get_or_create_from_django(
            request.user)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self._set_view_attributes(request, *args, **kwargs)
        return super(UserPreferencesView, self).dispatch(
            request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.save()
        except HTTPError as e:
            messages.error(self.request, e.msg)
        if form.has_changed():
            messages.success(
                self.request, _('Your preferences have been updated.'))
        else:
            messages.info(self.request, _('Your preferences did not change.'))
        return super(UserPreferencesView, self).form_valid(form)


class UserMailmanSettingsView(UserPreferencesView):
    """The logged-in user's global Mailman preferences."""

    form_class = UserPreferences
    template_name = 'postorius/user/mailman_settings.html'
    success_url = reverse_lazy('user_mailmansettings')

    def _get_preferences(self):
        # Get the defaults and pre-populate so view shows them
        combinedpreferences = self._get_combined_preferences()
        for key in combinedpreferences:
            if key != "self_link":
                self.mm_user.preferences[key] = combinedpreferences[key]

        # This is a bit of a hack so preferences behave as users expect
        # We probably don't want to save, only display here
        # but this means that whatever preferences the users see first are
        # the ones they have unless they explicitly change them
        self.mm_user.preferences.save()

        return self.mm_user.preferences

    def _get_combined_preferences(self):
        # Get layers of default preferences to match how they are applied
        # We ignore self_link as we don't want to over-write it
        defaultpreferences = get_mailman_client().preferences
        combinedpreferences = {}
        for key in defaultpreferences:
            if key != "self_link":
                combinedpreferences[key] = defaultpreferences[key]

        # Clobber defaults with any preferences already set
        for key in self.mm_user.preferences:
            if key != "self_link":
                combinedpreferences[key] = self.mm_user.preferences[key]

        return(combinedpreferences)


class UserAddressPreferencesView(UserPreferencesView):
    """The logged-in user's address-based Mailman Preferences."""

    template_name = 'postorius/user/address_preferences.html'
    success_url = reverse_lazy('user_address_preferences')

    def get_form_class(self):
        return formset_factory(
            UserPreferences, formset=UserPreferencesFormset, extra=0)

    def _get_preferences(self):
        return [address.preferences for address in self.mm_user.addresses]

    def _get_combined_preferences(self):
        # grab the default preferences
        defaultpreferences = get_mailman_client().preferences

        # grab your global preferences
        globalpreferences = self.mm_user.preferences

        # start a new combined preferences object
        combinedpreferences = []

        for address in self.mm_user.addresses:
            # make a per-address prefs object
            prefs = {}

            # initialize with default preferences
            for key in defaultpreferences:
                if key != "self_link":
                    prefs[key] = defaultpreferences[key]

            # overwrite with user's global preferences
            for key in globalpreferences:
                if key != "self_link":
                    prefs[key] = globalpreferences[key]

            # overwrite with address-specific preferences
            for key in address.preferences:
                if key != "self_link":
                    prefs[key] = address.preferences[key]
            combinedpreferences.append(prefs)

            # put the combined preferences back on the original object
            for key in prefs:
                if key != "self_link":
                    address.preferences[key] = prefs[key]

        return combinedpreferences

    def get_context_data(self, **kwargs):
        data = super(UserAddressPreferencesView, self).get_context_data(
            **kwargs)
        data['formset'] = data.pop('form')
        for form, address in list(zip(
                data['formset'].forms, self.mm_user.addresses)):
            form.address = address
        return data


class UserListOptionsView(UserPreferencesView):
    """The logged-in user's subscription preferences."""

    form_class = UserPreferences
    template_name = 'postorius/user/list_options.html'

    def _get_subscription(self):
        subscription = None
        for s in self.mm_user.subscriptions:
            if s.role == 'member' and s.list_id == self.mlist.list_id:
                subscription = s
                break
        if not subscription:
            raise Http404(_('Subscription does not exist'))
        return subscription

    def _set_view_attributes(self, request, *args, **kwargs):
        super(UserListOptionsView, self)._set_view_attributes(
            request, *args, **kwargs)
        self.mlist = List.objects.get_or_404(fqdn_listname=kwargs['list_id'])
        self.subscription = self._get_subscription()
        if (self.subscription.subscription_mode ==
                SubscriptionMode.as_user.name):
            self.subscriber = self.subscription.user.user_id
        else:
            self.subscriber = self.subscription.email

    def _get_preferences(self):
        return self.subscription.preferences

    def get_context_data(self, **kwargs):
        data = super(UserListOptionsView, self).get_context_data(**kwargs)
        data['mlist'] = self.mlist
        user_emails = EmailAddress.objects.filter(
            user=self.request.user, verified=True).order_by(
            "email").values_list("email", flat=True)
        mm_user = get_mailman_user(self.request.user)
        primary_email = None
        if mm_user.preferred_address is None:
            primary_email = set_preferred(self.request.user, mm_user)
        else:
            primary_email = mm_user.preferred_address.email
        data['change_subscription_form'] = ChangeSubscriptionForm(
            user_emails, mm_user.user_id, primary_email,
            initial={'subscriber': self.subscriber})
        return data

    def get_success_url(self):
        return reverse(
            'user_list_options', kwargs=dict(list_id=self.mlist.list_id))


class UserSubscriptionPreferencesView(UserPreferencesView):
    """The logged-in user's subscription-based Mailman Preferences."""

    template_name = 'postorius/user/subscription_preferences.html'
    success_url = reverse_lazy('user_subscription_preferences')

    def _get_subscriptions(self):
        subscriptions = []
        for s in self.mm_user.subscriptions:
            if s.role != 'member':
                continue
            subscriptions.append(s)
        return subscriptions

    def _set_view_attributes(self, request, *args, **kwargs):
        super(UserSubscriptionPreferencesView, self)._set_view_attributes(
            request, *args, **kwargs)
        self.subscriptions = self._get_subscriptions()

    def get_form_class(self):
        return formset_factory(
            UserPreferences, formset=UserPreferencesFormset, extra=0)

    def _get_preferences(self):
        return [sub.preferences for sub in self.subscriptions]

    def _get_combined_preferences(self):
        # grab the default preferences
        defaultpreferences = get_mailman_client().preferences

        # grab your global preferences
        globalpreferences = self.mm_user.preferences

        # start a new combined preferences object
        combinedpreferences = []

        for sub in self.subscriptions:
            # make a per-address prefs object
            prefs = {}

            # initialize with default preferences
            for key in defaultpreferences:
                if key != "self_link":
                    prefs[key] = defaultpreferences[key]

            # overwrite with user's global preferences
            for key in globalpreferences:
                if key != "self_link":
                    prefs[key] = globalpreferences[key]

            # overwrite with address-based preferences
            # There is currently no better way to do this,
            # we may consider revisiting.
            addresspreferences = {}
            for address in self.mm_user.addresses:
                if sub.email == address.email:
                    addresspreferences = address.preferences

            for key in addresspreferences:
                if key != "self_link":
                    prefs[key] = addresspreferences[key]

            # overwrite with subscription-specific preferences
            for key in sub.preferences:
                if key != "self_link":
                    prefs[key] = sub.preferences[key]

            combinedpreferences.append(prefs)

        return combinedpreferences
        # return [sub.preferences for sub in self.subscriptions]

    def get_context_data(self, **kwargs):
        data = super(UserSubscriptionPreferencesView, self).get_context_data(
            **kwargs)
        data['formset'] = data.pop('form')
        for form, subscription in list(zip(
                data['formset'].forms, self.subscriptions)):
            form.list_id = subscription.list_id
        return data


@login_required
def user_subscriptions(request):
    """Shows the subscriptions of a user."""
    mm_user = MailmanUser.objects.get_or_create_from_django(request.user)
    memberships = [m for m in mm_user.subscriptions]
    return render(request, 'postorius/user/subscriptions.html',
                  {'memberships': memberships})
