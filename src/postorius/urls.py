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


from django.conf.urls import include, url

from postorius.views import domain as domain_views
from postorius.views import list as list_views
from postorius.views import rest as rest_views
from postorius.views import system as system_views
from postorius.views import template as template_views
from postorius.views import user as user_views


list_patterns = [
    url(r'^csv_view/$', list_views.csv_view, name='csv_view'),
    url(r'^members/options/(?P<email>.+)$', list_views.list_member_options,
        name='list_member_options'),
    url(r'^members/(?P<role>\w+)/$', list_views.ListMembersViews.as_view(),
        name='list_members'),
    url(r'^$', list_views.ListSummaryView.as_view(),
        name='list_summary'),
    url(r'^subscribe$', list_views.ListSubscribeView.as_view(),
        name='list_subscribe'),
    url(r'^anonymous_subscribe$',
        list_views.ListAnonymousSubscribeView.as_view(),
        name='list_anonymous_subscribe'),
    url(r'^change_subscription$', list_views.ChangeSubscriptionView.as_view(),
        name='change_subscription'),
    url(r'^unsubscribe/$', list_views.ListUnsubscribeView.as_view(),
        name='list_unsubscribe'),
    url(r'^subscription_requests$', list_views.list_subscription_requests,
        name='list_subscription_requests'),
    url(r'^pending_confirmation$', list_views.list_pending_confirmations,
        name='list_pending_confirmation'),
    url(r'^handle_subscription_request/(?P<request_id>[^/]+)/'
        '(?P<action>[accept|reject|discard|defer]+)$',
        list_views.handle_subscription_request,
        name='handle_subscription_request'),
    url(r'^mass_subscribe/$', list_views.list_mass_subscribe,
        name='mass_subscribe'),
    url(r'^mass_removal/$', list_views.ListMassRemovalView.as_view(),
        name='mass_removal'),
    url(r'^delete$', list_views.list_delete, name='list_delete'),
    url(r'^held_messages$', list_views.list_moderation,
        name='list_held_messages'),
    url(r'^held_messages/moderate$', list_views.moderate_held_message,
        name='moderate_held_message'),
    url(r'^bans/$', list_views.list_bans, name='list_bans'),
    url(r'^header-matches/$', list_views.list_header_matches,
        name='list_header_matches'),
    url(r'^remove/(?P<role>[^/]+)/(?P<address>.+)$', list_views.remove_role,
        name='remove_role'),
    url(r'^settings/(?P<visible_section>[^/]+)?$', list_views.list_settings,
        name='list_settings'),
    url(r'^unsubscribe_all$', list_views.remove_all_subscribers,
        name='unsubscribe_all'),
    url(r'^confirm/$', list_views.confirm_token,
        name='confirm_token'),
    url(r'^templates$',
        template_views.ListTemplateIndexView.as_view(),
        name='list_template_list'),
    url(r'^templates/new$',
        template_views.ListTemplateCreateView.as_view(),
        name='list_template_new'),
    url(r'^templates/(?P<pk>[^/]+)?/update$',
        template_views.ListTemplateUpdateView.as_view(),
        name='list_template_update'),
    url(r'^templates/(?P<pk>[^/]+)?/delete$',
        template_views.ListTemplateDeleteView.as_view(),
        name='list_template_delete')
]

urlpatterns = [
    url(r'^$', list_views.list_index),                   # noqa: W605 (bogus)
    url(r'^accounts/subscriptions/$', user_views.user_subscriptions,
        name='ps_user_profile'),
    url(r'^accounts/per-address-preferences/$',
        user_views.UserAddressPreferencesView.as_view(),
        name='user_address_preferences'),
    # if this URL changes, update Mailman's Member.options_url
    url(r'^accounts/per-subscription-preferences/$',
        user_views.UserSubscriptionPreferencesView.as_view(),
        name='user_subscription_preferences'),
    url(r'^accounts/mailmansettings/$',
        user_views.UserMailmanSettingsView.as_view(),
        name='user_mailmansettings'),
    url(r'^accounts/list-options/(?P<list_id>[^/]+)/$',
        user_views.UserListOptionsView.as_view(),
        name='user_list_options'),
    # /domains/
    url(r'^domains/$', domain_views.domain_index, name='domain_index'),
    url(r'^domains/new/$', domain_views.domain_new, name='domain_new'),
    url(r'^domains/(?P<domain>[^/]+)/$', domain_views.domain_edit,
        name='domain_edit'),
    url(r'^domains/(?P<domain>[^/]+)/delete$', domain_views.domain_delete,
        name='domain_delete'),
    url(r'^domains/(?P<domain>[^/]+)/owners$', domain_views.domain_owners,
        name='domain_owners'),
    url(r'^domains/(?P<domain>[^/]+)/owners/(?P<user_id>.+)/remove$',
        domain_views.remove_owners,
        name='remove_domain_owner'),
    # Ideally, these paths should be accessible by domain_owners, however,
    # we don't have good ways to check that, so for now, this views are
    # protected by superuser privileges.
    # I know it is bad, but this will be fixed soon. See postorius#
    url(r'^domains/(?P<domain>[^/]+)/templates$',
        template_views.DomainTemplateIndexView.as_view(),
        name='domain_template_list'),
    url(r'^domains/(?P<domain>[^/]+)/templates/new$',
        template_views.DomainTemplateCreateView.as_view(),
        name='domain_template_new'),
    url(r'^domains/(?P<domain>[^/]+)/templates/(?P<pk>[^/]+)/update$',
        template_views.DomainTemplateUpdateView.as_view(),
        name='domain_template_update'),
    url(r'^domains/(?P<domain>[^/]+)/templates/(?P<pk>[^/]+)/delete$',
        template_views.DomainTemplateDeleteView.as_view(),
        name='domain_template_delete'),
    # /lists/
    url(r'^lists/$', list_views.list_index, name='list_index'),
    url(r'^lists/new/$', list_views.list_new, name='list_new'),
    url(r'^lists/(?P<list_id>[^/]+)/', include(list_patterns)),

    # /system/
    url(r'^system/$', system_views.system_information,
        name='system_information'),

    # /bans/
    url(r'^bans/$', system_views.bans, name='global_bans'),

    # /api/
    url(r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/$',
        rest_views.get_held_message, name='rest_held_message'),
    url(r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/'
        r'attachment/(?P<attachment_id>\d+)/$',
        rest_views.get_attachment_for_held_message,
        name='rest_attachment_for_held_message'),
    # URL configuration for templates.
    url(r'^api/templates/(?P<context>[^/]+)/(?P<identifier>[^/]+)/(?P<name>[^/]+)',  # noqa: E501
        template_views.get_template_data,
        name='rest_template'),
]
