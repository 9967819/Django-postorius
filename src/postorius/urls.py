# -*- coding: utf-8 -*-
# Copyright (C) 1998-2023 by the Free Software Foundation, Inc.
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

from django.conf.urls import include
from django.urls import re_path

from postorius.views import domain as domain_views
from postorius.views import list as list_views
from postorius.views import rest as rest_views
from postorius.views import system as system_views
from postorius.views import template as template_views
from postorius.views import user as user_views


list_patterns = [
    re_path(r'^csv_view/$', list_views.csv_view, name='csv_view'),
    re_path(
        r'^members/options/(?P<email>.+)$',
        list_views.list_member_options,
        name='list_member_options',
    ),
    re_path(
        r'^members/(?P<role>\w+)/$',
        list_views.ListMembersViews.as_view(),
        name='list_members',
    ),
    re_path(r'^$', list_views.ListSummaryView.as_view(), name='list_summary'),
    re_path(
        r'^subscribe$',
        list_views.ListSubscribeView.as_view(),
        name='list_subscribe',
    ),
    re_path(
        r'^anonymous_subscribe$',
        list_views.ListAnonymousSubscribeView.as_view(),
        name='list_anonymous_subscribe',
    ),
    re_path(
        r'^change_subscription$',
        list_views.ChangeSubscriptionView.as_view(),
        name='change_subscription',
    ),
    re_path(
        r'^unsubscribe/$',
        list_views.ListUnsubscribeView.as_view(),
        name='list_unsubscribe',
    ),
    re_path(
        r'^subscription_requests$',
        list_views.list_subscription_requests,
        name='list_subscription_requests',
    ),
    re_path(
        r'^unsubscription_requests$',
        list_views.list_unsubscription_requests,
        name='list_unsubscription_requests',
    ),
    re_path(
        r'^pending_confirmation$',
        list_views.list_pending_confirmations,
        name='list_pending_confirmation',
    ),
    re_path(
        r'^handle_subscription_request/(?P<request_id>[^/]+)/$',
        list_views.handle_subscription_request,
        name='handle_subscription_request',
    ),
    re_path(
        r'^mass_subscribe/$',
        list_views.list_mass_subscribe,
        name='mass_subscribe',
    ),
    re_path(
        r'^mass_removal/$',
        list_views.ListMassRemovalView.as_view(),
        name='mass_removal',
    ),
    re_path(r'^delete$', list_views.list_delete, name='list_delete'),
    re_path(
        r'^held_messages$',
        list_views.list_moderation,
        name='list_held_messages',
    ),
    re_path(
        r'^held_messages/moderate$',
        list_views.moderate_held_message,
        name='moderate_held_message',
    ),
    re_path(r'^bans/$', list_views.list_bans, name='list_bans'),
    re_path(
        r'^header-matches/$',
        list_views.list_header_matches,
        name='list_header_matches',
    ),
    re_path(
        r'^remove/(?P<role>[^/]+)/(?P<address>.+)$',
        list_views.remove_role,
        name='remove_role',
    ),
    re_path(
        r'^settings/(?P<visible_section>[^/]+)?$',
        list_views.list_settings,
        name='list_settings',
    ),
    re_path(
        r'^unsubscribe_all$',
        list_views.remove_all_subscribers,
        name='unsubscribe_all',
    ),
    re_path(r'^confirm/$', list_views.confirm_token, name='confirm_token'),
    re_path(
        r'^templates$',
        template_views.ListTemplateIndexView.as_view(),
        name='list_template_list',
    ),
    re_path(
        r'^templates/new$',
        template_views.ListTemplateCreateView.as_view(),
        name='list_template_new',
    ),
    re_path(
        r'^templates/(?P<pk>[^/]+)?/update$',
        template_views.ListTemplateUpdateView.as_view(),
        name='list_template_update',
    ),
    re_path(
        r'^templates/(?P<pk>[^/]+)?/delete$',
        template_views.ListTemplateDeleteView.as_view(),
        name='list_template_delete',
    ),
]

urlpatterns = [
    re_path(r'^$', list_views.list_index),  # noqa: W605 (bogus)
    re_path(
        r'^accounts/subscriptions/$',
        user_views.user_subscriptions,
        name='ps_user_profile',
    ),
    re_path(
        r'^accounts/per-address-preferences/$',
        user_views.UserAddressPreferencesView.as_view(),
        name='user_address_preferences',
    ),
    # if this URL changes, update Mailman's Member.options_url
    re_path(
        r'^accounts/per-subscription-preferences/$',
        user_views.UserSubscriptionPreferencesView.as_view(),
        name='user_subscription_preferences',
    ),
    re_path(
        r'^accounts/mailmansettings/$',
        user_views.UserMailmanSettingsView.as_view(),
        name='user_mailmansettings',
    ),
    re_path(
        r'^accounts/list-options/(?P<member_id>[^/]+)/$',
        user_views.UserListOptionsView.as_view(),
        name='user_list_options',
    ),
    # /domains/
    re_path(r'^domains/$', domain_views.domain_index, name='domain_index'),
    re_path(r'^domains/new/$', domain_views.domain_new, name='domain_new'),
    re_path(
        r'^domains/(?P<domain>[^/]+)/$',
        domain_views.domain_edit,
        name='domain_edit',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/delete$',
        domain_views.domain_delete,
        name='domain_delete',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/owners$',
        domain_views.domain_owners,
        name='domain_owners',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/owners/(?P<user_id>.+)/remove$',
        domain_views.remove_owners,
        name='remove_domain_owner',
    ),
    # Ideally, these paths should be accessible by domain_owners, however,
    # we don't have good ways to check that, so for now, this views are
    # protected by superuser privileges.
    # I know it is bad, but this will be fixed soon. See postorius#
    re_path(
        r'^domains/(?P<domain>[^/]+)/templates$',
        template_views.DomainTemplateIndexView.as_view(),
        name='domain_template_list',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/templates/new$',
        template_views.DomainTemplateCreateView.as_view(),
        name='domain_template_new',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/templates/(?P<pk>[^/]+)/update$',  # noqa: E501
        template_views.DomainTemplateUpdateView.as_view(),
        name='domain_template_update',
    ),
    re_path(
        r'^domains/(?P<domain>[^/]+)/templates/(?P<pk>[^/]+)/delete$',  # noqa: E501
        template_views.DomainTemplateDeleteView.as_view(),
        name='domain_template_delete',
    ),
    # /lists/
    re_path(r'^lists/$', list_views.list_index, name='list_index'),
    re_path(r'^lists/new/$', list_views.list_new, name='list_new'),
    re_path(r'^lists/(?P<list_id>[^/]+)/', include(list_patterns)),
    # /system/
    re_path(
        r'^system/$',
        system_views.system_information,
        name='system_information',
    ),
    # /bans/
    re_path(r'^bans/$', system_views.bans, name='global_bans'),
    # /api/
    re_path(
        r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/$',  # noqa: E501
        rest_views.get_held_message,
        name='rest_held_message',
    ),
    re_path(
        r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/'
        r'attachment/(?P<attachment_id>\d+)/$',
        rest_views.get_attachment_for_held_message,
        name='rest_attachment_for_held_message',
    ),
    # URL configuration for templates.
    re_path(
        r'^api/templates/(?P<context>[^/]+)/(?P<identifier>[^/]+)/(?P<name>[^/]+)',  # noqa: E501
        template_views.get_template_data,
        name='rest_template',
    ),
    # users.
    re_path(r'users$', user_views.list_users, name='list_users'),
    re_path(
        r'users/(?P<user_id>[^/]+)/manage$',
        user_views.manage_user,
        name='manage_user',
    ),
    re_path(
        r'users/(?P<user_id>[^/]+)/delete$',
        user_views.delete_user,
        name='delete_user',
    ),
]
