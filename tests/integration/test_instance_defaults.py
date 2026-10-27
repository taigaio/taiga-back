# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from unittest.mock import patch as mock_patch

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils.translation import get_language

from settings import common as common_settings
from taiga.base.mails import InlineCSSTemplateMail, mail_builder
from taiga.instance_settings.models import InstanceDefaults, InstanceDefaultsAudit
from taiga.instance_settings.services import deployment_language, recipient_language
from .. import factories as f


pytestmark = pytest.mark.django_db


def bearer(client, user):
    auth = client.post(reverse("auth-list"), {
        "type": "normal", "username": user.username, "password": user.username,
    })
    assert auth.status_code == 200
    return {"HTTP_AUTHORIZATION": "Bearer " + auth.data["auth_token"]}


def patch(client, headers, revision, language=None, theme=None):
    return client.patch(reverse("instance-defaults-admin"), data=json.dumps({
        "revision": revision, "default_language": language, "default_theme": theme,
    }), content_type="application/json", **headers)


def test_plain_settings_default_language_is_selectable():
    assert common_settings.LANGUAGE_CODE == "en"
    assert common_settings.LANGUAGE_CODE in dict(common_settings.LANGUAGES)
    assert deployment_language() == "en"


def test_public_bootstrap_contains_only_overrides_and_revision(client):
    result = client.get(reverse("instance-defaults-public"))
    assert result.status_code == 200
    assert result.data == {"default_language": None, "default_theme": None, "revision": 0}
    assert result["Cache-Control"] == "no-store"


def test_unavailable_saved_defaults_fall_back_for_public_bootstrap(client, settings):
    settings.LANGUAGE_CODE = "en"
    settings.INSTANCE_AVAILABLE_LANGUAGES = ("en",)
    settings.INSTANCE_AVAILABLE_THEMES = ("taiga",)
    defaults = InstanceDefaults.objects.get(pk=1)
    defaults.default_language = "pt-br"
    defaults.default_theme = "taiga-dark"
    defaults.save(update_fields=["default_language", "default_theme"])

    result = client.get(reverse("instance-defaults-public"))
    assert result.status_code == 200
    assert result.data == {"default_language": None, "default_theme": None, "revision": 0}

    admin = f.UserFactory(is_superuser=True, is_staff=True)
    details = client.get(reverse("instance-defaults-admin"), **bearer(client, admin))
    assert details.data["default_language"] == "pt-br"
    assert details.data["default_theme"] == "taiga-dark"
    assert details.data["effective_language"] == "en"
    assert details.data["effective_theme"] == "taiga"


def test_only_instance_superuser_can_read_and_change_defaults(client, settings):
    settings.INSTANCE_AVAILABLE_THEMES = ("taiga", "taiga-dark")
    member = f.UserFactory()
    project = f.ProjectFactory(owner=member)
    f.MembershipFactory(user=member, project=project, is_admin=True)
    ordinary = bearer(client, member)
    assert client.get(reverse("instance-defaults-admin"), **ordinary).status_code == 403
    assert patch(client, ordinary, 0, "pt-br", "taiga-dark").status_code == 403
    assert client.get(reverse("instance-defaults-admin")).status_code == 403
    assert patch(client, {}, 0, "pt-br", "taiga-dark").status_code == 403

    inactive = f.UserFactory(is_superuser=True, is_staff=True)
    inactive_token = bearer(client, inactive)
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    assert client.get(reverse("instance-defaults-admin"), **inactive_token).status_code in (401, 403)
    assert patch(client, inactive_token, 0, "pt-br", "taiga-dark").status_code in (401, 403)

    admin = f.UserFactory(is_superuser=True, is_staff=True)
    token = bearer(client, admin)
    result = client.get(reverse("instance-defaults-admin"), **token)
    assert result.status_code == 200
    assert "pt-br" in [language["code"] for language in result.data["languages"]]
    assert "fr" in [language["code"] for language in result.data["languages"]]
    assert result.data["themes"] == ("taiga", "taiga-dark")
    assert patch(client, token, 0, "pt-br", "taiga-dark").status_code == 200
    assert InstanceDefaultsAudit.objects.get().actor == admin
    assert client.get(reverse("instance-defaults-public")).data == {
        "default_language": "pt-br", "default_theme": "taiga-dark", "revision": 1}

    # The optional API session authenticator does not enforce CSRF. A session
    # alone must therefore never authorize this write.
    client.login(admin)
    assert patch(client, {}, 1, "fr", "taiga").status_code == 403


def test_validation_conflict_audit_and_reset(client, settings):
    settings.INSTANCE_AVAILABLE_THEMES = ("taiga", "taiga-dark")
    admin = f.UserFactory(is_superuser=True, is_staff=True)
    token = bearer(client, admin)
    assert patch(client, token, 0, "fr", "taiga-dark").status_code == 200
    assert patch(client, token, 0, "pt-br", "taiga").status_code == 409
    assert patch(client, token, 1, "zz", "taiga").status_code == 400
    assert patch(client, token, 1, "en", "missing").status_code == 400
    assert client.patch(reverse("instance-defaults-admin"), data=json.dumps({
        "revision": 1, "default_language": "en", "default_theme": "taiga",
        "unknown": "value"}), content_type="application/json", **token).status_code == 400
    assert patch(client, token, 1, None, None).status_code == 200
    defaults = InstanceDefaults.objects.get(pk=1)
    assert (defaults.default_language, defaults.default_theme, defaults.revision) == ("", "", 2)
    assert list(InstanceDefaultsAudit.objects.values_list("revision", flat=True)) == [1, 2]


def test_recovery_command_requires_confirmation_and_records_actor():
    admin = f.UserFactory(is_superuser=True, is_staff=True)
    defaults = InstanceDefaults.objects.get(pk=1)
    defaults.default_language = "pt-br"
    defaults.default_theme = "taiga-dark"
    defaults.save(update_fields=["default_language", "default_theme"])

    call_command("clear_instance_defaults", actor=admin.username)
    defaults.refresh_from_db()
    assert (defaults.default_language, defaults.default_theme, defaults.revision) == (
        "pt-br", "taiga-dark", 0)
    assert InstanceDefaultsAudit.objects.count() == 0

    call_command("clear_instance_defaults", actor=admin.username, confirm=True)
    defaults.refresh_from_db()
    assert (defaults.default_language, defaults.default_theme, defaults.revision) == (
        "", "", 1)
    audit = InstanceDefaultsAudit.objects.get()
    assert audit.actor == admin
    assert (audit.old_language, audit.new_language, audit.old_theme,
            audit.new_theme, audit.revision) == ("pt-br", "", "taiga-dark", "", 1)


def test_mail_language_uses_account_then_instance_then_deployment(settings):
    settings.LANGUAGE_CODE = "en"
    user = f.UserFactory(lang="")
    assert recipient_language(user) == "en"
    defaults = InstanceDefaults.objects.get(pk=1)
    defaults.default_language = "pt-br"
    defaults.save(update_fields=["default_language"])
    assert recipient_language(user) == "pt-br"
    inherited_subject = mail_builder.password_recovery(user, {"user": user}).subject
    user.lang = "fr"
    user.save(update_fields=["lang"])
    assert recipient_language(user) == "fr"
    explicit_subject = mail_builder.password_recovery(user, {"user": user}).subject
    assert inherited_subject != explicit_subject
    assert mail_builder.password_recovery(
        user, {"user": user, "lang": "pt-br"}).subject == explicit_subject
    assert mail_builder.password_recovery(
        "diagnostic@example.invalid", {"user": user, "lang": "pt-br"}).subject == inherited_subject
    user.new_email = "pending@example.invalid"
    assert mail_builder.change_email(
        user.new_email, {"user": user, "lang": "pt-br"}).subject != mail_builder.change_email(
        "diagnostic@example.invalid", {"user": user, "lang": "pt-br"}).subject
    user.lang = ""
    user.save(update_fields=["lang"])
    assert recipient_language(user, project_language="fr") == "fr"

    # Transfer and contact mail pass the recipient as `to` while the context
    # may name another user; the recipient's account choice must still win.
    recipient = f.UserFactory(lang="pt-br")
    addressed_subject = mail_builder.password_recovery(
        recipient, {"user": user}).subject
    assert addressed_subject == inherited_subject


def test_invitation_and_transfer_mail_use_recipient_language(settings):
    settings.LANGUAGE_CODE = "en"
    defaults = InstanceDefaults.objects.get(pk=1)
    defaults.default_language = "pt-br"
    defaults.save(update_fields=["default_language"])
    recipient = f.UserFactory(lang="")
    membership = f.MembershipFactory(user=recipient)
    invitation = f.InvitationFactory(project=membership.project)

    invitation_subject = mail_builder.membership_invitation(
        invitation.email, {"membership": invitation}).subject
    inherited_membership_subject = mail_builder.membership_notification(
        recipient, {"membership": membership}).subject
    with mock_patch.object(InlineCSSTemplateMail, "_render_message_subject",
                      lambda self, context: get_language()):
        inherited_transfer_language = mail_builder.transfer_request(
            recipient, {"project": membership.project,
                        "requester": membership.project.owner}).subject

    recipient.lang = "en"
    recipient.save(update_fields=["lang"])
    explicit_membership_subject = mail_builder.membership_notification(
        recipient, {"membership": membership}).subject
    with mock_patch.object(InlineCSSTemplateMail, "_render_message_subject",
                      lambda self, context: get_language()):
        explicit_transfer_language = mail_builder.transfer_request(
            recipient, {"project": membership.project,
                        "requester": membership.project.owner}).subject
    assert inherited_membership_subject != explicit_membership_subject
    assert inherited_transfer_language == "pt-br"
    assert explicit_transfer_language == "en"
    defaults.default_language = ""
    defaults.save(update_fields=["default_language"])
    deployment_invitation_subject = mail_builder.membership_invitation(
        invitation.email, {"membership": invitation}).subject
    assert invitation_subject != deployment_invitation_subject
