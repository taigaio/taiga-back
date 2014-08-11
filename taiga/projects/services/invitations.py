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
