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


from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path, re_path, reverse_lazy
from django.views.defaults import server_error
from django.views.generic import RedirectView


def not_found(request):
    """A test view to return 404 error to test 400.html"""
    raise Http404('Page not Found.')


urlpatterns = [
    re_path(
        r'^$',
        RedirectView.as_view(url=reverse_lazy('list_index'), permanent=True),
    ),
    re_path(r'^postorius/', include('postorius.urls')),
    re_path(r'', include('django_mailman3.urls')),
    re_path(r'^accounts/', include('allauth.urls')),
    # Add some testing routes to test 400/500 error pages without having to
    # introduce errors.
    re_path(r'500/$', server_error),
    re_path(r'400/$', not_found),
    # Django admin
    re_path(r'^admin/', admin.site.urls),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
