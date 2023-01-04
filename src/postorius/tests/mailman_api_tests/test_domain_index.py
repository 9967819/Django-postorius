# -*- coding: utf-8 -*-
# Copyright (C) 2012-2023 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

from urllib.error import HTTPError

from django.contrib.auth.models import User
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.models import MailDomain

from postorius.tests.utils import ViewTestCase


class DomainIndexPageTest(ViewTestCase):
    """Tests for the list index page."""

    def setUp(self):
        super(DomainIndexPageTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.domain.add_owner('person@domain.com')
        try:
            self.foo_list = self.domain.create_list('foo')
        except HTTPError:
            self.foo_list = self.mm_client.get_list('foo.example.com')

        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass'
        )
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass'
        )
        self.owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'testpass'
        )
        self.moderator = User.objects.create_user(
            'testmoderator', 'moderator@example.com', 'testpass'
        )
        for user in (self.user, self.superuser, self.owner, self.moderator):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        self.foo_list.add_owner('owner@example.com')
        self.foo_list.add_moderator('moderator@example.com')

    def _test_not_accesible_to_public(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def _test_not_accessible_to_unpriveleged_use(self, url):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def _test_not_accessible_to_moderators(self, url):
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def _test_not_accessible_to_owner(self, url):
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_domain_index_not_accessible_to_public(self):
        self._test_not_accesible_to_public(reverse('domain_index'))

    def test_domain_index_not_accessible_to_unpriveleged_user(self):
        self._test_not_accessible_to_unpriveleged_use(reverse('domain_index'))

    def test_domain_index_not_accessible_to_moderators(self):
        self._test_not_accessible_to_moderators(reverse('domain_index'))

    def test_domain_index_not_accessible_to_owners(self):
        self._test_not_accessible_to_owner(reverse('domain_index'))

    def test_contains_domains_and_site(self):
        # The list index page should contain the lists
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['domains']), 1)
        self.assertContains(response, 'example.com')
        self.assertTrue(
            MailDomain.objects.filter(mail_domain='example.com').exists()
        )
        # Test there are owners are listed.
        self.assertContains(response, 'person@domain.com')

    def test_domain_add_owner_not_acceesible_to_anyone_but_superuser(self):
        url = reverse('domain_owners', args=(self.domain.mail_host,))
        self._test_not_accesible_to_public(url)
        self._test_not_accessible_to_unpriveleged_use(url)
        self._test_not_accessible_to_moderators(url)
        self._test_not_accessible_to_owner(url)
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, b'Add a new owner to example.com')
        response = self.client.post(url, dict(email='person@example.com'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'person@example.com',
            [owner.addresses[0].email for owner in self.domain.owners],
        )

    def test_domain_delete_owner_not_acceesible_to_anyone_but_superuser(self):
        self.domain.add_owner('one@example.com')
        self.domain.add_owner('two@example.com')
        url = reverse(
            'remove_domain_owner',
            args=(self.domain.mail_host, 'person@domain.com'),
        )
        self.client.login(username='testsu', password='testpass')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(len(self.domain.owners), 2)
        self.assertEqual(
            sorted(owner.addresses[0].email for owner in self.domain.owners),
            ['one@example.com', 'two@example.com'],
        )
