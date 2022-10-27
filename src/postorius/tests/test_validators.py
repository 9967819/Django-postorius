from django.core.exceptions import ValidationError

import pytest

from postorius.forms.validators import validate_uuid_or_email


class TestValidators:
    def test_validate_uuid_or_email(self):
        # Test valid email.
        emails = ['aperson@example.com', 'user@localhost', 'bp@localhost.com']
        for email in emails:
            assert validate_uuid_or_email(email) == email
        # Test invalid email uuid.
        uuids = [
            '00000000000000000000000000000034',
            '00000000000000000000000000000084',
        ]
        for uuid in uuids:
            assert validate_uuid_or_email(uuid) == uuid

        # Test invalid email.
        invalid_emails = ['missingdomain@', '@missinglocal', 'mis2']
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_uuid_or_email(email)
        # Test invalid uuid.
        invalid_uuids = ['02394', '0923402340000000023']
        for uuid in invalid_uuids:
            with pytest.raises(ValidationError):
                validate_uuid_or_email(uuid)
