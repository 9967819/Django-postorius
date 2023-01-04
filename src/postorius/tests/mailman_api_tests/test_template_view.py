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

import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse

from allauth.account.models import EmailAddress
from django_mailman3.models import MailDomain

from postorius.models import TEMPLATES_LIST, EmailTemplate
from postorius.tests.utils import ViewTestCase


class DomainTemplateViewTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.su = User.objects.create_superuser(
            username='su', email='su@example.com', password='testpass'
        )
        self.domain_owner = User.objects.create_user(
            username='domain_owner',
            email='do@example.com',
            password='testpass',
        )
        self.testuser = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
        )
        for user in (self.testuser, self.su, self.domain_owner):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.domain.add_owner('do@example.com')

    def tearDown(self):
        EmailTemplate.objects.all().delete()
        # We do this because instead of returning an empty list, we get
        # a 404 error. This must be fixed in Client.

        super().tearDown()

    def test_access_anonymous(self):
        self.assertEqual(
            403,
            self._check_access(
                None, reverse('domain_template_list', args=('example.com',))
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None, reverse('domain_template_new', args=('example.com',))
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None,
                reverse(
                    'domain_template_update',
                    args=('example.com', 'template_id'),
                ),
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None,
                reverse(
                    'domain_template_delete',
                    args=('example.com', 'template_id'),
                ),
            ),
        )

    def _check_access(self, user, url):
        if user is not None:
            self.client.login(username=user.username, password=user.password)
        response = self.client.get(url)
        return response.status_code

    # Index Checks that access control works as expected. We don't test for
    # access control in other Template Views.
    def test_template_index_view_non_owner(self):
        # Test that the templates are accessible, but only to superuser and
        # domain owners.
        url = reverse('domain_template_list', args=('example.com',))
        response = self.client.login(username='testuser', password='testpass')
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_template_index_view_owner(self):
        # Not let's try domain owner.
        url = reverse('domain_template_list', args=('example.com',))
        response = self.client.login(
            username='domain_owner', password='testpass'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_template_index_view_superuser(self):
        url = reverse('domain_template_list', args=('example.com',))
        # Now, let's try the superuser.
        response = self.client.login(username='su', password='testpass')
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_template_create_view(self):
        self.client.login(username='domain_owner', password='testpass')
        # First, let's make sure we can GET the view.
        url = reverse('domain_template_new', args=('example.com',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('New Template' in str(response.content))
        # Now, let's try to create a new Template.
        data = {'name': 'list:admin:action:post', 'data': 'This is test data.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('domain_template_list', args=('example.com',)),
        )
        self.assertTrue(
            EmailTemplate.objects.filter(
                context='domain',
                name='list:admin:action:post',
                identifier='example.com',
            ).exists()
        )

    def test_template_create_view_whitespace(self):
        self.client.login(username='domain_owner', password='testpass')
        # First, let's make sure we can GET the view.
        url = reverse('domain_template_new', args=('example.com',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('New Template' in str(response.content))
        # Now, let's try to create a new Template with leading whitespace.
        data = {
            'name': 'list:admin:action:post',
            'data': '\n\n\t\tThis is test data.',
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        # Now, let's check to make sure that the data wasn't stripped.
        templates = EmailTemplate.objects.get(
            name='list:admin:action:post', identifier='example.com'
        )
        self.assertEqual(templates.data, '\n\n\t\tThis is test data.')

    def test_template_create_all(self):
        # Test that we can create all the template options.
        self.client.login(username='domain_owner', password='testpass')
        url = reverse('domain_template_new', args=('example.com',))
        for template_name, template_desc in TEMPLATES_LIST:
            # XXX(maxking): This is a bit weird, but Core for some reason
            # causes problems with this particular template. I am going to try
            # to debug this in Core.
            if template_name == 'list:user:notice:welcome':
                continue
            data = {'name': template_name, 'data': 'This is test data.'}
            response = self.client.post(url, data=data)
            self.assertEqual(response.status_code, 302, template_name)

    def test_template_unique_property(self):
        # Test that we can create templates with uniqueness.
        self.client.login(username='domain_owner', password='testpass')
        url = reverse('domain_template_new', args=('example.com',))
        data = {'name': 'list:admin:action:post', 'data': 'This is test data.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        template = EmailTemplate.objects.get(
            identifier='example.com', context='domain', name=data['name']
        )
        self.assertEqual(template.data, 'This is test data.')
        # Now, let's create a 2nd domain, and set a template with different
        # domain and same name.
        dom2 = self.mm_client.create_domain('example.net')
        url = reverse('domain_template_new', args=('example.net',))
        # Let's become superuser to post to this.
        self.assertTrue(self.client.login(username='su', password='testpass'))
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        templates = EmailTemplate.objects.filter(name=data['name'])
        self.assertEqual(len(templates), 2)
        # clean up.
        try:
            for template in dom2.templates:
                template.delete()
        except urllib.error.HTTPError:
            pass

    def test_template_delete_view(self):
        self.client.login(username='domain_owner', password='testpass')
        template = EmailTemplate.objects.create(
            name='list:admin:action:post',
            data='This is some new data.',
            context='domain',
            identifier='example.com',
        )
        # First, make sure we get the confirmation page when we GET.
        url = reverse(
            'domain_template_delete', args=('example.com', template.id)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Delete Template' in str(response.content))
        # Now, let's try to Delete this domain.
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('domain_template_list', args=('example.com',)),
        )
        # Make sure that this domain is now deleted.
        self.assertFalse(
            EmailTemplate.objects.filter(
                context='domain',
                name='list:admin:action:post',
                identifier='example.com',
            ).exists()
        )

    def test_template_update_view(self):
        self.client.login(username='domain_owner', password='testpass')
        data = dict(
            name='list:admin:action:post',
            context='domain',
            identifier='example.com',
            data='This is some new data.',
        )
        template = EmailTemplate.objects.create(**data)
        # First, make sure we can GET the page.
        url = reverse(
            'domain_template_update', args=('example.com', template.id)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Edit Template' in str(response.content))
        # Now, let's try to update this template by POST'ing.
        data = {'data': 'This is the update template data.'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        template = EmailTemplate.objects.get(pk=template.id)
        self.assertEqual(template.data, data['data'])


class MailingListTemplateViewTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.su = User.objects.create_superuser(
            username='su', email='su@example.com', password='testpass'
        )
        self.list_owner = User.objects.create_user(
            username='list_owner',
            email='owner@example.com',
            password='testpass',
        )
        self.list_mod = User.objects.create_user(
            username='list_mod', email='mod@example.com', password='testpass'
        )
        self.testuser = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
        )
        for user in (self.testuser, self.su, self.list_owner, self.list_mod):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.mlist = self.domain.create_list('fun')
        self.mlist.add_owner('owner@example.com')
        self.mlist.add_moderator('mod@example.com')

    def tearDown(self):
        for each_level in (
            self.mm_client.templates,
            self.domain.templates,
            self.mlist.templates,
        ):
            try:
                for template in each_level:
                    template.delete()
            except urllib.error.HTTPError:
                pass

        super().tearDown()

    def test_access_anonymous(self):
        self.assertEqual(
            403,
            self._check_access(
                None, reverse('list_template_list', args=('fun.example.com',))
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None, reverse('list_template_new', args=('fun.example.com',))
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None,
                reverse(
                    'list_template_update',
                    args=('fun.example.com', 'template_id'),
                ),
            ),
        )
        self.assertEqual(
            403,
            self._check_access(
                None,
                reverse(
                    'list_template_delete',
                    args=('fun.example.com', 'template_id'),
                ),
            ),
        )

    def _check_access(self, user, url):
        if user is not None:
            self.client.login(username=user.username, password=user.password)
        response = self.client.get(url)
        return response.status_code

    def test_template_index_view_non_owner(self):
        url = reverse('list_template_list', args=('fun.example.com',))
        response = self.client.login(username='testuser', password='testpass')
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_template_index_view_owner(self):
        url = reverse('list_template_list', args=('fun.example.com',))
        response = self.client.login(
            username='list_owner', password='testpass'
        )
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_template_index_view_moderator(self):
        url = reverse('list_template_list', args=('fun.example.com',))
        response = self.client.login(username='list_mod', password='testpass')
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_template_index_view_superuser(self):
        url = reverse('list_template_list', args=('fun.example.com',))
        response = self.client.login(username='su', password='testpass')
        self.assertTrue(response)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_template_create_view(self):
        self.client.login(username='list_owner', password='testpass')
        # First, let's make sure we can GET the view.
        url = reverse('list_template_new', args=('fun.example.com',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'Choose the template you want to customize.'
            in str(response.content)
        )
        # Now, let's try to create a new Template.
        data = {'name': 'list:admin:action:post', 'data': 'This is test data.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('list_template_list', args=('fun.example.com',)),
        )
        self.assertTrue(
            EmailTemplate.objects.filter(
                context='list',
                name='list:admin:action:post',
                identifier='fun.example.com',
            ).exists()
        )

    def test_template_create_view_whitespace(self):
        self.client.login(username='list_owner', password='testpass')
        # First, let's make sure we can GET the view.
        url = reverse('list_template_new', args=('fun.example.com',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'Choose the template you want to customize.'
            in str(response.content)
        )
        # Now, let's try to create a new Template with leading whitespace.
        data = {
            'name': 'list:admin:action:post',
            'data': '\n\n\t\tThis is test data.',
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        # Now, let's check to make sure that the data wasn't stripped.
        templates = EmailTemplate.objects.get(
            name='list:admin:action:post', identifier='fun.example.com'
        )
        self.assertEqual(templates.data, '\n\n\t\tThis is test data.')

    def test_template_create_all(self):
        # Test that we can create all the template options.
        self.client.login(username='list_owner', password='testpass')
        url = reverse('list_template_new', args=('fun.example.com',))
        for template_name, template_desc in TEMPLATES_LIST:
            data = {
                'name': template_name,
                'data': 'This is test data.',
                'language': 'en',
            }
            response = self.client.post(url, data=data)
            self.assertEqual(response.status_code, 302, template_name)

    def test_template_unique_property(self):
        # Test that we can create templates with uniqueness.
        self.client.login(username='list_owner', password='testpass')
        url = reverse('list_template_new', args=('fun.example.com',))
        data = {'name': 'list:admin:action:post', 'data': 'This is test data.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        template = EmailTemplate.objects.get(
            identifier='fun.example.com', context='list', name=data['name']
        )
        self.assertEqual(template.data, 'This is test data.')
        # Now, let's create a 2nd domain, and set a template with different
        # domain and same name.
        mlist2 = self.domain.create_list('new')
        url = reverse('list_template_new', args=('new.example.com',))
        # Let's become superuser to post to this.
        self.assertTrue(self.client.login(username='su', password='testpass'))
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        templates = EmailTemplate.objects.filter(name=data['name'])
        self.assertEqual(len(templates), 2)
        # Clean up.
        try:
            for template in mlist2.templates:
                template.delete()
        except urllib.error.HTTPError:
            pass

    def test_template_delete_view(self):
        self.client.login(username='list_owner', password='testpass')
        template = EmailTemplate.objects.create(
            name='list:admin:action:post',
            data='This is some new data.',
            context='list',
            identifier='fun.example.com',
        )
        # First, make sure we get the confirmation page when we GET.
        url = reverse(
            'list_template_delete', args=('fun.example.com', template.id)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Now, let's try to Delete this domain.
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('list_template_list', args=('fun.example.com',)),
        )
        # Make sure that this domain is now deleted.
        self.assertFalse(
            EmailTemplate.objects.filter(
                context='list',
                name='list:admin:action:post',
                identifier='fun.example.com',
            ).exists()
        )

    def _test_template_update_view(self, template_name, updated_data):
        self.client.login(username='list_owner', password='testpass')
        data = dict(
            name=template_name,
            context='list',
            identifier='fun.example.com',
            data='This is some new data.',
        )
        template = EmailTemplate.objects.create(**data)
        # First, make sure we can GET the page.
        url = reverse(
            'list_template_update', args=('fun.example.com', template.id)
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Now, let's try to update this template by POST'ing.
        data = {'data': updated_data}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        template = EmailTemplate.objects.get(pk=template.id)
        self.assertEqual(template.data, data['data'])

    def test_template_update_view(self):
        self._test_template_update_view(
            'list:admin:action:post', 'This is the update template data.'
        )
        self._test_template_update_view(
            'list:admin:action:subscribe', '\n\n\n\tHello World'
        )


class TestTemplateAPIView(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.mlist = self.domain.create_list('fun')

    def tearDown(self):
        EmailTemplate.objects.all().delete()
        super().tearDown()

    def test_get_empty_templates_via_API(self):
        # Test that we can get a domain level template from API.
        data = dict(
            name='list:admin:action:post',
            context='domain',
            identifier='example.com',
            data='',
        )
        # First, let's create a template.
        EmailTemplate.objects.create(**data)
        # Now, let's try to GET this template.
        url = reverse(
            'rest_template',
            kwargs=dict(
                name=data['name'],
                context=data['context'],
                identifier=data['identifier'],
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertRegex(
            response['Content-Type'], 'charset=' + settings.DEFAULT_CHARSET
        )
        self.assertNotRegex(response['Content-Type'], 'charset=$')

    def test_get_one_domain_template_via_API(self):
        # Test that we can get a domain level template from API.
        data = dict(
            name='list:admin:action:post',
            context='domain',
            identifier='example.com',
            data='This is some new data.',
        )
        # First, let's create a template.
        EmailTemplate.objects.create(**data)
        # Now, let's try to GET this template.
        url = reverse(
            'rest_template',
            kwargs=dict(
                name=data['name'],
                context=data['context'],
                identifier=data['identifier'],
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'This is some new data.')
        self.assertRegex(
            response['Content-Type'], 'charset=' + settings.DEFAULT_CHARSET
        )
        self.assertNotRegex(response['Content-Type'], 'charset=$')

    def test_get_one_list_template_via_API(self):
        # Test that we can get a list level template from API.
        data = dict(
            name='list:admin:action:post',
            context='list',
            identifier='fun.example.com',
            data='This is some other new data.',
        )
        # First, let's create a template.
        EmailTemplate.objects.create(**data)
        # Now, let's try to GET this template.
        url = reverse(
            'rest_template',
            kwargs=dict(
                name=data['name'],
                context=data['context'],
                identifier=data['identifier'],
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'This is some other new data.')
        self.assertRegex(
            response['Content-Type'], 'charset=' + settings.DEFAULT_CHARSET
        )
        self.assertNotRegex(response['Content-Type'], 'charset=$')
