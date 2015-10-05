from django.apps import apps
from django.conf import settings

from taiga.base.mails import mail_builder


def send_invitation(invitation):
    """Send an invitation email"""
    if invitation.user:
        template = mail_builder.membership_notification
        email = template(invitation.user, {"membership": invitation})
    else:
        template = mail_builder.membership_invitation
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
