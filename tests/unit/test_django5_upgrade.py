# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
Tests verifying Django 5.x compatibility.

Covers:
 - Django version >= 5.0 is in use.
 - Migration files no longer import the removed django.utils.timezone.utc.
 - SEND_BROKEN_LINK_EMAILS (removed in Django 4.0) is absent from settings.
 - Migration files use datetime.timezone.utc for timezone-aware defaults.
 - django.http.multipartparser.parse_header compat shim works correctly (removed in Django 5.0).
 - Model Meta no longer uses index_together (removed in Django 5.1).
 - taiga.auth.utils no longer imports the removed django.utils.timezone.utc.
"""

import ast
import datetime
import importlib
import sys

import django
import pytest


# ---------------------------------------------------------------------------
# Django version guard
# ---------------------------------------------------------------------------

def test_django_version_is_5_or_higher():
    """Regression: repo must run on Django >= 5 (3.2 reached EOL April 2024)."""
    major = django.VERSION[0]
    assert major >= 5, (
        f"Django {django.get_version()} is installed but >= 5.0 is required. "
        "Django 3.2 reached end-of-life in April 2024."
    )


# ---------------------------------------------------------------------------
# Migration file regressions (django.utils.timezone.utc removed in 5.0)
# ---------------------------------------------------------------------------

MIGRATION_FILES_UNDER_TEST = [
    "taiga.projects.votes.migrations.0002_auto_20150805_1600",
    "taiga.projects.migrations.0030_auto_20151128_0757",
]


@pytest.mark.parametrize("module_path", MIGRATION_FILES_UNDER_TEST)
def test_migration_does_not_import_removed_django_timezone_utc(module_path):
    """
    Regression: django.utils.timezone.utc was removed in Django 5.0.
    Migration files must not import it.
    """
    module = importlib.import_module(module_path)
    source_file = module.__file__

    with open(source_file, encoding="utf-8") as fh:
        source = fh.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "django.utils.timezone":
                imported_names = [alias.name for alias in node.names]
                assert "utc" not in imported_names, (
                    f"{source_file}: found 'from django.utils.timezone import utc' "
                    "which was removed in Django 5.0. "
                    "Use datetime.timezone.utc instead."
                )


@pytest.mark.parametrize("module_path", MIGRATION_FILES_UNDER_TEST)
def test_migration_module_imports_cleanly(module_path):
    """The migration module must be importable without errors under Django 5.x."""
    # Force a fresh import to surface any ImportError at collection time.
    if module_path in sys.modules:
        del sys.modules[module_path]
    try:
        importlib.import_module(module_path)
    except ImportError as exc:
        pytest.fail(f"{module_path} failed to import: {exc}")


@pytest.mark.parametrize("module_path", MIGRATION_FILES_UNDER_TEST)
def test_migration_default_datetimes_use_stdlib_utc(module_path):
    """
    DateTimeField defaults that embed a fixed datetime must use
    datetime.timezone.utc (stdlib), not the removed django.utils.timezone.utc.
    """
    module = importlib.import_module(module_path)
    migration = module.Migration

    for operation in migration.operations:
        field = getattr(operation, "field", None)
        if field is None:
            continue
        default = field.default
        if isinstance(default, datetime.datetime) and default.tzinfo is not None:
            assert default.tzinfo is datetime.timezone.utc, (
                f"{module_path}: field default {default!r} uses tzinfo="
                f"{default.tzinfo!r} instead of datetime.timezone.utc."
            )


# ---------------------------------------------------------------------------
# Settings regression
# ---------------------------------------------------------------------------

def test_settings_does_not_contain_removed_send_broken_link_emails():
    """
    Regression: SEND_BROKEN_LINK_EMAILS was removed in Django 4.0.
    It must not appear in the project settings to avoid confusion.
    """
    from django.conf import settings as django_settings

    assert not hasattr(django_settings, "SEND_BROKEN_LINK_EMAILS"), (
        "SEND_BROKEN_LINK_EMAILS was removed from Django in 4.0 "
        "and must be removed from settings/common.py."
    )


def test_settings_common_py_does_not_reference_send_broken_link_emails():
    """
    Source-level check: the literal string must not appear in settings/common.py,
    preventing accidental re-introduction.
    """
    import os

    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "settings",
        "common.py",
    )
    with open(settings_path, encoding="utf-8") as fh:
        content = fh.read()

    assert "SEND_BROKEN_LINK_EMAILS" not in content, (
        "settings/common.py still references SEND_BROKEN_LINK_EMAILS "
        "which was removed in Django 4.0."
    )


# ---------------------------------------------------------------------------
# parse_header compat shim (django.http.multipartparser.parse_header removed in 5.0)
# ---------------------------------------------------------------------------

def test_parse_header_compat_shim_basic():
    """
    Regression: parse_header was removed from django.http.multipartparser in
    Django 5.0. The compat shim must parse a simple content-type header correctly.
    """
    from taiga.base.api.utils.mediatypes import _MediaType

    mt = _MediaType("application/json; charset=utf-8")
    assert mt.main_type == "application"
    assert mt.sub_type == "json"
    assert mt.params.get("charset") == "utf-8"


def test_parse_header_compat_shim_no_params():
    """Compat shim handles headers with no parameters."""
    from taiga.base.api.utils.mediatypes import _MediaType

    mt = _MediaType("application/json")
    assert mt.main_type == "application"
    assert mt.sub_type == "json"
    assert mt.params == {}


def test_parse_header_compat_shim_wildcard():
    """Compat shim handles wildcard media types."""
    from taiga.base.api.utils.mediatypes import _MediaType

    mt = _MediaType("*/*")
    assert mt.main_type == "*"
    assert mt.sub_type == "*"


def test_media_type_matches_exact():
    """media_type_matches returns True for identical types."""
    from taiga.base.api.utils.mediatypes import media_type_matches

    assert media_type_matches("application/json", "application/json") is True


def test_media_type_matches_wildcard():
    """media_type_matches returns True when rhs is a wildcard."""
    from taiga.base.api.utils.mediatypes import media_type_matches

    assert media_type_matches("application/json", "*/*") is True


def test_is_form_media_type():
    """is_form_media_type works correctly after the parse_header shim."""
    from taiga.base.api.request import is_form_media_type

    assert is_form_media_type("application/x-www-form-urlencoded") is True
    assert is_form_media_type("multipart/form-data") is True
    assert is_form_media_type("application/json") is False


# ---------------------------------------------------------------------------
# index_together removed from model Meta (Django 5.1)
# ---------------------------------------------------------------------------

INDEX_TOGETHER_MODEL_FILES = [
    "taiga/projects/attachments/models.py",
    "taiga/projects/models.py",
    "taiga/projects/custom_attributes/models.py",
]


@pytest.mark.parametrize("rel_path", INDEX_TOGETHER_MODEL_FILES)
def test_model_does_not_use_index_together(rel_path):
    """
    Regression: index_together was removed from Django model Meta in 5.1.
    Model files must use indexes = [models.Index(...)] instead.
    """
    import os

    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    abs_path = os.path.join(base, rel_path)

    with open(abs_path, encoding="utf-8") as fh:
        source = fh.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Meta":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "index_together":
                            pytest.fail(
                                f"{abs_path}: class Meta still uses 'index_together' "
                                "which was removed in Django 5.1. "
                                "Use 'indexes = [models.Index(...)]' instead."
                            )


# ---------------------------------------------------------------------------
# taiga.auth.utils must not import removed django.utils.timezone.utc
# ---------------------------------------------------------------------------

def test_auth_utils_does_not_import_removed_utc():
    """
    Regression: django.utils.timezone.utc was removed in Django 5.0.
    taiga/auth/utils.py must not import it.
    """
    import os

    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    abs_path = os.path.join(base, "taiga", "auth", "utils.py")

    with open(abs_path, encoding="utf-8") as fh:
        source = fh.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "django.utils.timezone":
                imported_names = [alias.name for alias in node.names]
                assert "utc" not in imported_names, (
                    f"{abs_path}: imports 'utc' from 'django.utils.timezone' "
                    "which was removed in Django 5.0. "
                    "Use datetime.timezone.utc instead."
                )
