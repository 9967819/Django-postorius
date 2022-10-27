import uuid

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _


def validate_uuid_or_email(input_value):
    """Check if the value is a valid email or UUID.

    This is useful to determine if a given input is a user identifier in
    Mailman 3 API 3.1+, where, user identifiers are either UUID or email.

    :param input_value: The value to validate.
    :type input_value: str
    :returns: input_value
    :rtype: str
    :raises ValidationError: If the value is either a UUID, not an email.
    """

    try:
        validate_email(input_value)
    except ValidationError:
        is_email = False
    else:
        is_email = True

    is_uuid = False
    if not is_email:
        try:
            uuid.UUID(input_value)
        except ValueError:
            is_uuid = False
        else:
            is_uuid = True

    if not any([is_email, is_uuid]):
        raise ValidationError(
            _('Invalid: "{0}" should be either email or UUID').format(
                input_value
            ),
            params={'value': input_value},
            code='invalid',
        )
    return input_value
