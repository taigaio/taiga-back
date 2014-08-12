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


def find_invited_user(invitation, default=None):
    """Check if the invited user is already a registered.

    :param invitation: Invitation object.
    :param default: Default object to return if user is not found.

    :return: The user if it's found, othwerwise return `default`.
    """
    try:
        return type(invitation).user.get_queryset().filter(email=invitation.email).all()[0]
    except IndexError:
        return default
