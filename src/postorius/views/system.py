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


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy

from django_mailman3.lib.mailman import get_mailman_client

from postorius.auth.decorators import superuser_required
from postorius.views.generic import bans_view


SYSTEM_INFO_KEYS = (
    ('mailman_version', gettext_lazy('Mailman Core Version')),
    ('api_version', gettext_lazy('Mailman Core API Version')),
    ('python_version', gettext_lazy('Mailman Core Python Version')),
)


@login_required
@superuser_required
def system_information(request):
    client = get_mailman_client()
    all_configs = client.system

    configs = []
    for key, name in SYSTEM_INFO_KEYS:
        configs.append((name, all_configs.get(key)))

    queues = {
        queue_name: len(queue.files)
        for queue_name, queue in client.queues.items()
    }

    return render(
        request,
        'postorius/system_information.html',
        {'configs': configs, 'queues': queues},
    )


@login_required
@superuser_required
def bans(request):
    return bans_view(request, template='postorius/bans.html')
