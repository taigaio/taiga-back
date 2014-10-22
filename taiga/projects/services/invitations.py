from django.apps import apps
from django.conf import settings

from djmail.template_mail import MagicMailBuilder


def send_invitation(invitation):
    """Send an invitation email"""
    mbuilder = MagicMailBuilder()
    if invitation.user:
        template = mbuilder.membership_notification
    else:
        template = mbuilder.membership_invitation

    email = template(invitation.email, {"membership": invitation})
    email.send()


def find_invited_user(email, default=None):
    """Check if the invited user is already a registered.

    :param invitation: Invitation object.
    :param default: Default object to return if user is not found.

    TODO: only used by importer/exporter and should be moved here

    :return: The user if it's found, othwerwise return `default`.
    """

    User = apps.get_model(settings.AUTH_USER_MODEL)

    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return default
