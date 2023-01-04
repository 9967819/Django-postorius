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
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.models import MailDomain

from postorius.tests.utils import ViewTestCase


class TestDomainEdit(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.user = User.objects.create_user('user', 'user@example.com', 'pwd')
        self.superuser = User.objects.create_superuser(
            'su', 'su@example.com', 'pwd'
        )
        for user in (self.user, self.superuser):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.url = reverse('domain_edit', args=['example.com'])

    def test_permission_denied(self):
        self.client.login(username='user', password='pwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_edit_non_existent_domain(self):
        self.client.login(username='su', password='pwd')
        response = self.client.get(reverse('domain_edit', args=['random.com']))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.context['exception'], 'Domain does not exist'
        )

    def test_edit_domain_works(self):
        self.client.login(username='su', password='pwd')
        response = self.client.post(
            self.url,
            dict(
                mail_host='example.com',
                description='This is a new list description',
                site=Site.objects.get_current().id,
            ),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.domain.description, 'This is a new list description'
        )

    def test_change_mail_host(self):
        new_site = Site.objects.create(domain='most-desirable.org')
        self.client.login(username='su', password='pwd')
        response = self.client.post(
            self.url, dict(mail_host='example.com', site=new_site.id)
        )
        self.assertEqual(response.status_code, 302)
        mdomain = MailDomain.objects.get(mail_domain=self.domain.mail_host)
        self.assertEqual(mdomain.site, new_site)
