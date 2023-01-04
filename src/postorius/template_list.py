# -*- coding: utf-8 -*-
# Copyright (C) 2018-2023 by the Free Software Foundation, Inc.
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
# flake8: noqa

from django.utils.translation import gettext_lazy as _


TEMPLATES_LIST = (
    (
        'list:admin:action:post',
        _(
            'Sent to the list administrators when moderator approval for a posting is required.'
        ),
    ),
    (
        'list:admin:action:subscribe',
        _(
            'Sent to the list administrators when moderator approval for a subscription request is required.'
        ),
    ),
    (
        'list:admin:action:unsubscribe',
        _(
            'Sent to the list administrators when moderator approval for an unsubscription request is required.'
        ),
    ),
    (
        'list:admin:notice:subscribe',
        _(
            'Sent to the list administrators to notify them when a new member has been subscribed.'
        ),
    ),
    (
        'list:admin:notice:unrecognized',
        _(
            'Sent to the list administrators when a bounce message in an unrecognized format has been received.'
        ),
    ),
    (
        'list:admin:notice:pending',
        _(
            "Sent to the list administrators from the 'mailman notify' command."
        ),
    ),
    (
        'list:admin:notice:increment',
        _(
            "Sent to the list administrators to notify them when a member's bounce score is incremented."
        ),
    ),
    (
        'list:admin:notice:disable',
        _(
            "Sent to the list administrators to notify them when a member's delivery is disabled due to excessive bounces."
        ),
    ),
    (
        'list:admin:notice:unsubscribe',
        _(
            'Sent to the list administrators to notify them when a member has been unsubscribed.'
        ),
    ),
    ('list:member:digest:footer', _('The footer for a digest message.')),
    ('list:member:digest:header', _('The header for a digest message.')),
    (
        'list:member:digest:masthead',
        _(
            'The digest “masthead”; i.e. a common introduction for all digest messages.'
        ),
    ),
    (
        'list:member:regular:footer',
        _('The footer for a regular (non-digest) message.'),
    ),
    (
        'list:member:regular:header',
        _('The header for a regular (non-digest) message.'),
    ),
    (
        'list:user:action:subscribe',
        _(
            'The message sent to subscribers when a subscription confirmation is required.'
        ),
    ),
    (
        'list:user:action:unsubscribe',
        _(
            'The message sent to subscribers when an unsubscription confirmation is required.'
        ),
    ),
    (
        'list:user:action:invite',
        _(
            'The message sent to subscribers when they are invited to join a list.'
        ),
    ),
    (
        'list:user:notice:goodbye',
        _(
            'The notice sent to a member when they unsubscribe from a mailing list.'
        ),
    ),
    (
        'list:user:notice:hold',
        _(
            'The notice sent to a poster when their message is being held for moderator approval.'
        ),
    ),
    (
        'list:user:notice:no-more-today',
        _(
            'Sent to a user when the maximum number of autoresponses has been reached for that day.'
        ),
    ),
    (
        'list:user:notice:post',
        _(
            'Notice sent to a poster when their message has been received by the mailing list.'
        ),
    ),
    (
        'list:user:notice:probe',
        _(
            'A bounce probe sent to a member when their subscription has been disabled due to bounces.'
        ),
    ),
    (
        'list:user:notice:refuse',
        _(
            'Notice sent to a poster when their message has been rejected by the list’s moderator.'
        ),
    ),
    (
        'list:user:notice:rejected',
        _(
            'Notice sent to a poster when their message has been rejected automatically.'
        ),
    ),
    (
        'list:user:notice:welcome',
        _(
            'The notice sent to a member when they are subscribed to the mailing list.'
        ),
    ),
    (
        'list:user:notice:warning',
        _(
            'The notice sent to a member when their membership has been disabled due to excessive bounces.'
        ),
    ),
)
