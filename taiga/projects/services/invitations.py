from djmail.template_mail import MagicMailBuilder


def send_invitation(invitation):
    """Send an invitation email"""
    mbuilder = MagicMailBuilder()
    email = mbuilder.membership_invitation(invitation.email, {"membership": invitation})
    email.send()
