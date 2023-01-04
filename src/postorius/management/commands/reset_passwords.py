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

import base64
import os

from django.core.management.base import BaseCommand

from django_mailman3.lib.mailman import get_mailman_client


PASSWORD_BYTES = 32


class Command(BaseCommand):

    help = """Reset passwords of all users in Mailman Core. This does not
    affect the login passwords of users in Django or any other social
    authentication. Users will be able to login with their current passwords.
    Mailman Core maintains a second set of passwords for every user, which
    would be set to a random value of base64 encode 32 bytes."""

    def handle(self, *args, **kwargs):
        client = get_mailman_client()
        for user in self._get_all_users(client):
            self._reset_password(user)

    def _get_all_users(self, client):
        """Given a mailmanclient.Client instance, returns an iterator of
        paginated user records.
        """
        page = client.get_user_page(count=50, page=1)
        while True:
            for user in page:
                yield user
            if page.has_next:
                page = page.next
            else:
                break

    def _reset_password(self, user):
        """Given a mailmanclient.restobject.user.User object, reset its
        password to None in the database.
        """
        user.password = self._get_random_password()
        user.save()
        msg = 'Password reset for {}'.format(user)
        self.stdout.write(self.style.SUCCESS(msg))

    def _get_random_password(self):
        """Generate a random password for a user."""
        tok = os.urandom(PASSWORD_BYTES)
        return base64.urlsafe_b64encode(tok).rstrip(b'=').decode('ascii')
