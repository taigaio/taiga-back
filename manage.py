#!/usr/bin/env python
"""
Entry point for running Django management commands.

This script sets the default Django settings module and
executes command line instructions using Django's
management utility.
"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Copyright (c) 2021-present Kaleidos INC

import os
import sys


def main():
    """
    Configure Django settings and run management commands.
    """
    # Set default settings module for the Django project
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.common")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed or not available in the environment."
        ) from exc

    # Execute command-line arguments
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
