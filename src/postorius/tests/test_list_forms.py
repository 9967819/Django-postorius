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
import unittest

from django.test import TestCase

from postorius.forms.list_forms import (
    ArchiveSettingsForm,
    ChangeSubscriptionForm,
    DigestSettingsForm,
    DMARCMitigationsForm,
    ListAnonymousSubscribe,
    ListAutomaticResponsesForm,
    ListHeaderMatchForm,
    ListIdentityForm,
    ListMassRemoval,
    ListMassSubscription,
    ListNew,
    ListSubscribe,
    MemberModeration,
    MemberPolicyForm,
    MessageAcceptanceForm,
)
from postorius.forms.system import AddBanForm
from postorius.tests.utils import create_mock_list


class TestListSubscribe(TestCase):
    def test_required_fields_only(self):
        user_emails = ['bob@example.com', 'anne@example.com']
        form = ListSubscribe(
            user_emails, None, None, dict(subscriber='bob@example.com')
        )
        self.assertTrue(form.is_valid())

    def test_email_is_only_from_choices(self):
        user_emails = ['bob@example.com', 'anne@example.com']
        form = ListSubscribe(
            user_emails,
            None,
            None,
            dict(subscriber='alice@example.com', display_name='Alice'),
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('subscriber' in form.errors)
        self.assertTrue(
            'Select a valid choice.' in form.errors['subscriber'][0]
        )

    def test_subscribe_works(self):
        user_emails = ['someone@example.com']
        form = ListSubscribe(
            user_emails,
            None,
            None,
            {'subscriber': 'someone@example.com', 'display_name': 'Someone'},
        )
        self.assertTrue(form.is_valid())

    def test_subscribe_fails(self):
        user_emails = ['someone@example.com']
        form = ListSubscribe(
            user_emails,
            None,
            None,
            {'subscriber': 'notaemail', 'display_name': 'Someone'},
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('subscriber' in form.errors.keys())
        self.assertEqual(
            form.errors['subscriber'][0],
            'Select a valid choice.'
            ' notaemail is not one of the available choices.',
        )

    def test_subscribe_validates_email(self):
        user_emails = ['something']
        form = ListSubscribe(
            user_emails,
            None,
            None,
            {'subscriber': 'something', 'display_name': 'Someone'},
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('subscriber' in form.errors.keys())
        self.assertEqual(
            form.errors['subscriber'][0], 'Please enter a valid email address.'
        )

    def test_subscribe_with_user_uuid(self):
        user_emails = ['aperson@example.com']
        form = ListSubscribe(
            user_emails,
            '00000000000000000000000000000004',
            'aperson@example.com',
            {'subscriber': '00000000000000000000000000000004'},
        )
        self.assertEqual(form.is_valid(), True)

    def test_subscribe_with_invalid_uuid(self):
        # Test that invalid UUID returns errors.
        user_emails = ['aperson@example.com']
        form = ListSubscribe(
            user_emails, '4', 'aperson@example.com', {'subscriber': '4'}
        )
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(
            form.errors['subscriber'][0], 'Please enter a valid email address.'
        )

    def test_list_subscribe_with_delivery_mode(self):
        user_emails = ['aperson@example.com']
        form = ListSubscribe(
            user_emails,
            '00000000000000000000000000000004',
            'aperson@example.com',
            {
                'subscriber': '00000000000000000000000000000004',
                'delivery_mode': 'plaintext_digests',
                'delivery_status': 'by_user',
            },
        )
        self.assertTrue(form.is_valid())

    def test_list_subscribe_with_invalid_delivery_status(self):
        user_emails = ['aperson@example.com']
        form = ListSubscribe(
            user_emails,
            '00000000000000000000000000000004',
            'aperson@example.com',
            {
                'subscriber': '00000000000000000000000000000004',
                'delivery_mode': 'plaintext_digest',
                'delivery_status': 'by_bounces',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('delivery_status' in form.errors)


class TestChangeSubscription(TestCase):
    def test_subscription_changes_only_to_user_addresses(self):
        user_emails = ['one@example.com', 'two@example.com']
        form = ChangeSubscriptionForm(
            user_emails,
            None,
            None,
            {'subscriber': 'abcd@d.com', 'member_id': '1235sdfsd314'},
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('subscriber' in form.errors.keys())
        self.assertEqual(
            form.errors['subscriber'][0],
            'Select a valid choice. '
            'abcd@d.com is not one of the available choices.',
        )

    def test_subscription_works(self):
        user_emails = ['one@example.com', 'two@example.com']
        form = ChangeSubscriptionForm(
            user_emails,
            None,
            None,
            {'subscriber': 'two@example.com', 'member_id': '1235sdfsd314'},
        )
        self.assertTrue(form.is_valid())

    def test_subscription_form_labels(self):
        user_emails = ['one@example.com', 'two@example.com']
        form = ChangeSubscriptionForm(
            user_emails, None, None, {'member_id': '1235sdfsd314'}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['subscriber'].label, 'Select Email')

    def test_form_validity(self):
        form = ChangeSubscriptionForm(
            ['email@example.com', 'john@example.com', 'doe@example.com'],
            None,
            None,
            {'subscriber': 'email@example.com', 'member_id': '1235sdfsd314'},
        )
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        # There is only one required fields.
        form = ChangeSubscriptionForm(
            ['email@example.com', 'john@example.com', 'doe@example.com'],
            None,
            None,
            {'member_id': '1235sdfsd314'},
        )
        self.assertTrue(form.is_valid())

    def test_change_subscription_with_user_uuid(self):
        user_emails = ['aperson@example.com']
        form = ChangeSubscriptionForm(
            user_emails,
            '00000000000000000000000000000004',
            'aperson@example.com',
            {
                'subscriber': '00000000000000000000000000000004',
                'member_id': '1235sdfsd314',
            },
        )
        self.assertEqual(form.is_valid(), True)

    def test_subscribe_with_invalid_uuid(self):
        # Test that invalid UUID returns errors.
        user_emails = ['aperson@example.com']
        # UUIDs are 32bit and 4 is not a valid email.
        form = ChangeSubscriptionForm(
            user_emails, '4', 'aperson@example.com', {'subscriber': '4'}
        )
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(
            form.errors['subscriber'][0],
            'Invalid: "4" should be either email or UUID',
        )


class TestListNew(TestCase):
    def test_form_fields_list(self):
        domain_choices = [
            ('mailman.most-desirable.org', 'mailman.most-desirable.org')
        ]
        style_choices = [
            ('legacy-default', 'Ordinary discussion mailing list style.'),
            ('legacy-announce', 'Announce only mailing list style.'),
        ]
        form = ListNew(
            domain_choices,
            style_choices,
            {
                'listname': 'xyz',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'contact@mailman.most-desirable.org',
                'advertised': 'True',
                'list_style': 'legacy-default',
                'description': 'The Most Desirable organization',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_fields_list_invalid(self):
        domain_choices = [
            ('mailman.most-desirable.org', 'mailman.most-desirable.org')
        ]
        style_choices = [
            ('legacy-default', 'Ordinary discussion mailing list style.'),
            ('legacy-announce', 'Announce only mailing list style.'),
        ]
        form = ListNew(
            domain_choices,
            style_choices,
            {
                'listname': 'xy#z',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'mailman.most-desirable.org',
                'advertised': 'abcd',
                'list_style': 'defg',
                'description': 'The Most Desirable organization',
            },
        )
        self.assertFalse(form.is_valid())
        # Test that all invalid fields are actually checked.
        for field in ('list_owner', 'advertised'):
            self.assertTrue(field in form.errors)
        self.assertTrue(
            'Enter a valid email address.' in form.errors['list_owner']
        )
        self.assertTrue(
            'Select a valid choice. abcd is not one of the available choices.'
            in form.errors['advertised']
        )

    def test_form_without_domain_choices(self):
        form = ListNew(
            [],
            {
                'listname': 'xyz',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'contact@mailman.most-desirable.org',
                'advertised': 'True',
                'description': 'The Most Desirable organization',
            },
        )
        # Without domain choices, the form is not going to be valid.
        self.assertFalse(form.is_valid())
        self.assertTrue(
            form.fields['mail_host'].help_text
            == 'Site admin has not created any domains'  # noqa: W504
        )

    def test_listname_validation(self):
        domain_choices = [
            ('mailman.most-desirable.org', 'mailman.most-desirable.org')
        ]
        style_choices = [
            ('legacy-default', 'Ordinary discussion mailing list style.'),
            ('legacy-announce', 'Announce only mailing list style.'),
        ]
        form = ListNew(
            domain_choices,
            style_choices,
            {
                'listname': 'xy@z',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'mailman.most-desirable.org',
                'advertised': 'abcd',
                'description': 'The Most Desirable organization',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('listname' in form.errors)
        self.assertTrue(
            'Please enter a valid listname' in form.errors['listname']
        )

    @unittest.expectedFailure
    def test_listname_validation_errors_sane(self):
        # This test is going to fail right now, but needs to be fixed.
        form = ListNew(
            [('mailman.most-desirable.org', 'mailman.most-desirable.org')],
            {
                'listname': 'xy#z',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'mailman.most-desirable.org',
                'advertised': 'abcd',
                'description': 'The Most Desirable organization',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('listname' in form.errors)
        self.assertEqual(
            'Please enter a valid listname, "@" is not allowed in listname',
            form.errors['listname'],
        )

    def test_form_fields_order(self):
        domain_choices = [
            ('mailman.most-desirable.org', 'mailman.most-desirable.org')
        ]
        style_choices = [
            ('legacy-default', 'Ordinary discussion mailing list style.'),
            ('legacy-announce', 'Announce only mailing list style.'),
        ]
        form = ListNew(
            domain_choices,
            style_choices,
            {
                'listname': 'xyz',
                'mail_host': 'mailman.most-desirable.org',
                'list_owner': 'mailman@most-desirable.org',
                'list_style': 'legacy-default',
                'advertised': 'True',
                'description': 'The Most Desirable organization',
            },
        )
        self.assertTrue(form.is_valid())
        # The order of the fields should remain exactly like this.
        self.assertEqual(
            list(form.fields),
            [
                'listname',
                'mail_host',
                'list_owner',
                'advertised',
                'list_style',
                'description',
            ],
        )


class TestListIdentityForm(TestCase):
    def test_not_required_fields(self):
        # Only advertised is the required form field.
        form = ListIdentityForm(
            {
                'advertised': 'True',
            },
            mlist=None,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_field_validations(self):
        form = ListIdentityForm(
            {
                'advertised': 'abcd',
                'description': 'This is the most desirable organization',
                'info': 'This is a larger description of this mailing list.',
                'display_name': 'Most Desirable Mailing List',
                'subject_prefix': '  [Most Desirable]               ',
                'preferred_language': 'en',
                'member_roster_visibility': 'public',
            },
            mlist=None,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('advertised' in form.errors)
        self.assertEqual(
            [
                'Select a valid choice. abcd is not one of the available choices.'  # noqa: E501
            ],
            form.errors['advertised'],
        )
        # We shouldn't be removing trailing whitespaces, but we
        # should remove the leading ones.
        self.assertEqual(
            form.cleaned_data['subject_prefix'],
            '[Most Desirable]               ',
        )


class TestListMassSubscription(TestCase):
    def test_all_valid_email_formats(self):
        form = ListMassSubscription(
            {
                'emails': """
jdoe@example.com
<jdoe@example.com>
John Doe <jdoe@example.com>
"John Doe" <jdoe@example.com>
jdoe@example.com (John Doe)"""
            }
        )
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = ListMassSubscription({'email': '   '})
        self.assertFalse(form.is_valid())
        self.assertEqual(['This field is required.'], form.errors['emails'])
        form = ListMassSubscription({'email': '----'})
        self.assertFalse(form.is_valid())
        self.assertEqual(['This field is required.'], form.errors['emails'])


class TestListMassRemoval(TestCase):
    def test_all_valid_formats(self):
        form = ListMassRemoval(
            {
                'emails': """
jdoe@example.com
<jdoe@example.com>
John Doe <jdoe@example.com>
"John Doe" <jdoe@example.com>
jdoe@example.com (John Doe)"""
            }
        )
        self.assertTrue(form.is_valid())


class TestAddBanForm(TestCase):
    def test_form_validity(self):
        form = AddBanForm({'email': 'jdoe@example.com'})
        self.assertTrue(form.is_valid())

    def test_missing_fields_errors(self):
        form = AddBanForm({})
        self.assertFalse(form.is_valid())
        self.assertTrue('email' in form.errors)
        self.assertEqual(
            form.errors['email'], ['Please enter an email address.']
        )

    @unittest.expectedFailure
    def test_invalid_fields_type(self):
        # Valid values for email is either a regexp or an email address.
        # However, this is currently not validated by the form.
        form = AddBanForm({'email': 'invalid@'})
        self.assertFalse(form.is_valid())
        self.assertTrue('email' in form.errors)
        self.assertEqual(
            form.errors['email'], ['Please enter a valid email address.']
        )


class TestListHeaderMatchForm(TestCase):
    def test_form_validity(self):
        # Test by putting only required fields.
        form = ListHeaderMatchForm(
            {'header': 'To', 'pattern': 'value@example.com'}
        )
        self.assertTrue(form.is_valid())
        # Test all fileds.
        form = ListHeaderMatchForm(
            {
                'header': 'To',
                'pattern': 'value@example.com',
                'action': 'accept',
            }
        )
        self.assertTrue(form.is_valid())
        # Defer is not a valid action, so validation should fail here.
        form = ListHeaderMatchForm(
            {'header': 'To', 'pattern': 'value@example.com', 'action': 'defer'}
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('action' in form.errors)


class TestMemberModeration(TestCase):
    def test_moderation_action_validity(self):
        form = MemberModeration({'moderation_action': 'moderation'})
        self.assertFalse(form.is_valid())
        self.assertTrue('moderation_action' in form.errors)
        self.assertEqual(
            form.errors['moderation_action'],
            [
                'Select a valid choice. moderation is not one of the available choices.'  # noqa: E501
            ],
        )

    def test_required_fields(self):
        form = MemberModeration({})
        self.assertTrue(form.is_valid())


class TestListAutomaticResponsesForm(TestCase):

    fields = (
        'autorespond_owner',
        'autoresponse_owner_text',
        'autorespond_postings',
        'autoresponse_postings_text',
        'autorespond_requests',
        'autoresponse_request_text',
        'autoresponse_grace_period',
        'send_welcome_message',
        'welcome_message_uri',
        'send_goodbye_message',
        'goodbye_message_uri',
        'admin_immed_notify',
        'admin_notify_mchanges',
    )

    def prepare_formdata(self, values):
        return dict(
            (
                (key, val)
                for key, val in zip(self.fields, values)
                if val is not None
            )
        )   # noqa

    def test_required_fields_only(self):
        values = (
            'respond_and_continue',
            None,
            'respond_and_continue',
            None,
            'respond_and_continue',
            None,
            '2',
            None,
            None,
            None,
            None,
            None,
        )
        formdata = self.prepare_formdata(values)
        form = ListAutomaticResponsesForm(formdata, mlist=None)
        self.assertTrue(form.is_valid())

    def test_all_values(self):
        values = (
            'respond_and_continue',
            'Autorespond text',
            'respond_and_continue',
            'Autorespond text',
            'respond_and_continue',
            'Autorespond text',
            '2',
            'True',
            'http://example.com/welcome_text',
            'True',
            'http://example.com/goodbye_message',
            'True',
            'False',
        )
        formdata = self.prepare_formdata(values)
        form = ListAutomaticResponsesForm(formdata, mlist=None)
        print(form.errors)
        self.assertTrue(form.is_valid())


class TestAlterMessageForm(TestCase):

    fields = (
        'filter_content',
        'collapse_alternatives',
        'convert_html_to_plaintext',
        'anonymous_list',
        'include_rfc2369_headers',
        'allow_list_posts',
        'reply_list_posts',
        'reply_to_address',
        'first_strip_reply_to',
        'reply_goes_to_list',
        'posting_pipeline',
    )

    def prepare_formdata(self, values):
        return dict(
            (
                (key, val)
                for key, val in zip(self.fields, values)
                if val is not None
            )
        )   # noqa


class TestDMARCMitigationsForm(TestCase):
    def test_required_fields(self):
        # All fields in the form are optional, so an empty form should be
        # valid.
        form = DMARCMitigationsForm({}, mlist=None)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        formdata = dict(
            dmarc_mitigate_action='munge_from',
            dmarc_mitigate_unconditionally='True',
            dmarc_addresses='user@example.com\n^.*@example.net',
            dmarc_moderation_notice='This is a moderation notice',
            dmarc_wrapped_message_text='This is wrapped message text',
        )
        form = DMARCMitigationsForm(formdata, mlist=None)
        self.assertTrue(form.is_valid())


class TestDigestSettingsForm(TestCase):
    def test_required_fields(self):
        form = DigestSettingsForm({}, mlist=None)
        self.assertFalse(form.is_valid())
        self.assertTrue('digest_size_threshold' in form.errors)
        self.assertEqual(
            form.errors['digest_size_threshold'], ['This field is required.']
        )
        form = DigestSettingsForm({'digest_size_threshold': 40}, mlist=None)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        formdata = dict(
            digests_enabled='True',
            digests_send_periodic='True',
            digests_volume_frequency='daily',
            digest_size_threshold='10',
        )
        form = DigestSettingsForm(formdata, mlist=None)
        self.assertTrue(form.is_valid())


class TestMessageAcceptanceForm(TestCase):

    fields = (
        'acceptable_aliases',
        'require_explicit_destination',
        'administrivia',
        'default_member_action',
        'default_nonmember_action',
        'max_message_size',
        'max_num_recipients',
    )

    def prepare_formdata(self, values):
        return dict(
            (
                (key, val)
                for key, val in zip(self.fields, values)
                if val is not None
            )
        )   # noqa

    def test_required_fields(self):
        # Without any fields, form should not be valid.
        form = MessageAcceptanceForm({}, mlist=None)
        self.assertFalse(form.is_valid())
        # Now lets try with only required fields.
        values = (None, None, None, 'hold', 'hold', 40, 100)
        form = MessageAcceptanceForm(self.prepare_formdata(values), mlist=None)
        print(form.errors)
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        pass


class TestArchiveSettingsForm(TestCase):
    def setUp(self):
        self.mlist = create_mock_list()
        archivers = {'pipermail': True, 'hyperkitty': True}
        self.mlist.archivers.keys.side_effect = archivers.keys
        self.mlist.archivers.__getitem__.side_effect = archivers.__getitem__
        self.mlist.archivers.__iter__.side_effect = archivers.__iter__
        self.mlist.archivers.__contains__.side_effect = archivers.__contains__

    def test_required_fields(self):
        # First try without any fields.
        form = ArchiveSettingsForm({}, mlist=self.mlist)
        self.assertFalse(form.is_valid())
        self.assertTrue('archive_policy' in form.errors)
        # Now, with only required fields, this should be a valid form.
        form = ArchiveSettingsForm(
            dict(archive_policy='public'), mlist=self.mlist
        )
        self.assertTrue(form.is_valid())

    def test_all_fields(self):
        formdata = dict(
            archive_policy='public', archivers=['pipermail', 'hyperkitty']
        )
        form = ArchiveSettingsForm(formdata, mlist=self.mlist)
        self.assertTrue(form.is_valid())

    def test_setup_archivers_populated(self):
        formdata = dict(
            archive_policy='public', archivers=['pipermail', 'hyperkitty']
        )
        form = ArchiveSettingsForm(
            formdata, mlist=self.mlist, initial={'archivers': None}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.initial['archivers'], ['hyperkitty', 'pipermail']
        )

    def test_optional_archive_rendering_field(self):
        # Test that archive rendering mode is set only when Hyperkitty is
        # installed.
        formdata = dict(archive_policy='public', archivers=['pipermail'])
        form = ArchiveSettingsForm(
            formdata, mlist=self.mlist, initial={'archivers': None}
        )
        self.assertTrue(form.is_valid())
        self.assertFalse('archive_rendering_mode' in form.fields)
        # With Hyperkitty installed, the field should show up.
        with unittest.mock.patch(
            'postorius.forms.list_forms.apps.is_installed', return_value=True
        ):
            formdata = dict(archive_policy='public', archivers=['pipermail'])
            form = ArchiveSettingsForm(
                formdata, mlist=self.mlist, initial={'archivers': None}
            )
            self.assertTrue(form.is_valid())
            self.assertTrue('archive_rendering_mode' in form.fields)


class TestMemberPolicyForm(TestCase):
    def test_required_fields(self):
        form = MemberPolicyForm({}, mlist=None)
        self.assertFalse(form.is_valid())
        self.assertTrue('subscription_policy' in form.errors)
        self.assertTrue('unsubscription_policy' in form.errors)
        form = MemberPolicyForm(
            dict(
                subscription_policy='confirm', unsubscription_policy='confirm'
            ),
            mlist=None,
        )
        self.assertTrue(form.is_valid())


class TestListAnonymousSubscribe(TestCase):
    def test_required_fields_only(self):
        form = ListAnonymousSubscribe(dict(email='bob@exmaple.com'))
        self.assertTrue(form.is_valid())

    def test_email_is_validated(self):
        form = ListAnonymousSubscribe(dict(email='invalid'))
        self.assertFalse(form.is_valid())
        self.assertTrue('email' in form.errors)
        self.assertEqual(
            form.errors['email'], ['Please enter a valid email address.']
        )

    def test_all_fields(self):
        form = ListAnonymousSubscribe(
            dict(email='bob@example.com', display_name='Bob')
        )
        self.assertTrue(form.is_valid())
