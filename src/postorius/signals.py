# -*- coding: utf-8 -*-
# Copyright (C) 2020-2023 by the Free Software Foundation, Inc.
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

import logging

from django.dispatch import receiver

from django_mailman3.models import MailDomain
from django_mailman3.signals import domain_created

from postorius.models import Domain


log = logging.getLogger(__name__)


@receiver(domain_created, sender=Domain)
def maybe_update_site(sender, **kw):
    """Update the Site's name and description match the domain iff it is
    example.com.

    On a new Django instance, the default Site is example.com and when a user
    creates a new domain, they'll still see example.com in the Title.  It is
    safe to update the Site object to the domain's mail host and description.

    Do not touch the Site object if it isn't example.com.

    :param sender: The model class.
    :param instance: The actual instance of the sender class.
    :param created: IF the new record was created.
    """
    mail_host = kw.get('mail_host')

    mail_domain = MailDomain.objects.get(mail_domain=mail_host)
    domain = Domain.objects.get(mail_host=mail_host)
    site = mail_domain.site
    if not site.domain == 'example.com':
        log.info('Not updating site domain')
        return
    log.info('Updating site domain.')
    # Update the Site to match the domain with mail_host and description to
    # description if not empty else mail_host.
    site.domain = domain.mail_host
    site.name = domain.description or domain.mail_host
    site.save()
    log.debug('Update Site %s to match domain %s', site, domain)
