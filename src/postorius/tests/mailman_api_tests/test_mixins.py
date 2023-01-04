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


from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import TemplateView

from allauth.account.models import EmailAddress
from django_mailman3.models import MailDomain

from postorius.auth.mixins import (
    DomainOwnerMixin,
    ListModeratorMixin,
    ListOwnerMixin,
)
from postorius.tests.utils import ViewTestCase


class TestAuthenticationMixins(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.su = User.objects.create_superuser(
            username='su', email='su@example.com', password='testpass'
        )
        self.do = User.objects.create_user(
            username='domain_owner',
            email='do@example.com',
            password='testpass',
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
        for user in (
            self.testuser,
            self.su,
            self.list_owner,
            self.list_mod,
            self.do,
        ):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
        MailDomain.objects.create(
            site=Site.objects.get_current(), mail_domain='example.com'
        )
        self.domain.add_owner('do@example.com')
        self.mlist = self.domain.create_list('fun')
        self.mlist.add_owner('owner@example.com')
        self.mlist.add_moderator('mod@example.com')
        self.factory = RequestFactory()

    def test_list_owner_mixin(self):
        class TestView(ListOwnerMixin, TemplateView):
            def get(request, *args, **kwargs):
                return HttpResponse('Hello')

        view = TestView.as_view()
        request = self.factory.get(
            reverse('list_delete', args=('fun.example.com',))
        )
        # Make sure that an anonymous user isn't able to access this view.
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            view(request)
        # Make sure a logged-in user who is not an owner isn't able to access
        # this view.
        request.user = self.list_mod
        with self.assertRaises(PermissionDenied):
            view(request, list_id='fun.example.com')
        # Make sure that a superuser is able to access the view too.
        request.user = self.su
        response = view(request, list_id='fun.example.com')
        self.assertEqual(response.content, b'Hello')
        # Make sure that a list owner is able to access this view.
        request.user = self.list_owner
        response = view(request, list_id='fun.example.com')
        self.assertEqual(response.content, b'Hello')

    def test_list_moderator_mixin(self):
        class TestView(ListModeratorMixin, TemplateView):
            def get(request, *args, **kwargs):
                return HttpResponse('Hello')

        view = TestView.as_view()
        request = self.factory.get(
            reverse('list_delete', args=('fun.example.com',))
        )
        # Make sure that an anonymous user can not get this.
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            view(request)
        # Make sure a logged-in user who is not an owner isn't able to access
        # this view.
        request.user = self.testuser
        with self.assertRaises(PermissionDenied):
            view(request, list_id='fun.example.com')
        # Make sure that a superuser is able to access the view too.
        request.user = self.su
        response = view(request, list_id='fun.example.com')
        self.assertEqual(response.content, b'Hello')
        # Make sure that a list owner is able to access this view.
        request.user = self.list_owner
        response = view(request, list_id='fun.example.com')
        self.assertEqual(response.content, b'Hello')
        # Make sure that a list moderator is able to access this view.
        request.user = self.list_mod
        response = view(request, list_id='fun.example.com')
        self.assertEqual(response.content, b'Hello')

    def test_domain_owner_requred(self):
        class TestView(DomainOwnerMixin, TemplateView):
            def get(request, *args, **kwargs):
                return HttpResponse('Hello')

        view = TestView.as_view()
        request = self.factory.get(
            reverse('domain_delete', args=('example.com',))
        )
        # Non logged-in user.
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            view(request, domain='example.com')
        # Logged-in normal user.
        request.user = self.testuser
        with self.assertRaises(PermissionDenied):
            view(request, domain='example.com')
        # Another mailing list owner.
        request.user = self.list_owner
        with self.assertRaises(PermissionDenied):
            view(request, domain='example.com')
        # Test that superuser is able to access the page.
        request.user = self.su
        response = view(request, domain='example.com')
        self.assertEqual(response.content, b'Hello')
        # The domain owner itself should be able to access everything.
        request.user = self.do
        response = view(request, domain='example.com')
        self.assertEqual(response.content, b'Hello')
