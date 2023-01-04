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

from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class TestMigrationPending(TestCase):
    def test_pending_migration(self):
        # Test that there aren't any pending migrations to be added.
        output = StringIO()
        # We will call the makemigrations command and check the output.
        call_command(
            'makemigrations', interactive=False, dry_run=True, stdout=output
        )
        self.assertEqual(output.getvalue(), 'No changes detected\n')
