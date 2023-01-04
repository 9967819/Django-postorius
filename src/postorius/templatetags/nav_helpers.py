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


from django import template
from django.utils.translation import gettext_lazy as _


register = template.Library()

translation_msgids = {
    'msgid:title:list_header_matches': _('Header Filters'),
    'msgid:title:list_bans': _('Banned Addresses'),
    'msgid:title:list_delete': _('Delete List'),
    'msgid:title:list_held_messages': _('Held Messages'),
    'msgid:title:list_mass_removal': _('Mass Removal'),
    'msgid:title:list_mass_subscription': _('Mass Subscription'),
    'msgid:title:list_members': _('Subscription Options'),
    'msgid:title:list_settings': _('List Settings'),
    'msgid:title:list_summary': _('Summary'),
    'msgid:title:list_mass_removal_confirm': _(
        'Confirm Removal of All Members'
    ),
    'msgid:title:list_templates': _('Templates'),
    'msgid:title:user_settings_address': _('Address-based Settings'),
    'msgid:title:user_settings_list': _('Subscription Settings'),
    'msgid:title:user_settings_global': _('Global Settings'),
    'msgid:title:user_subscriptions': _('Subscriptions'),
}


@register.inclusion_tag('postorius/menu/list_nav.html', takes_context=True)
def list_nav(context, current, title='', subtitle=''):
    title = translation_msgids.get(title, title)
    subtitle = translation_msgids.get(subtitle, subtitle)
    return dict(
        list=context['list'],
        current=current,
        user=context['request'].user,
        title=title,
        subtitle=subtitle,
    )


@register.inclusion_tag('postorius/menu/user_nav.html', takes_context=True)
def user_nav(context, current, title='', subtitle=''):
    title = translation_msgids.get(title, title)
    subtitle = translation_msgids.get(subtitle, subtitle)
    return dict(
        current=current,
        user=context['request'].user,
        title=title,
        subtitle=subtitle,
    )


@register.simple_tag(takes_context=True)
def nav_active_class(context, current, view_name):
    if current == view_name:
        return 'active'
    return ''


@register.filter
def held_count(mlist):
    return mlist.get_held_count()


@register.filter
def pending_subscriptions(mlist):
    return mlist.get_requests_count(token_owner='moderator')
