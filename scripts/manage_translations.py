#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# NOTE: This script is based on django's manage_translations.py script
#       (https://github.com/django/django/blob/master/scripts/manage_translations.py)
#
# This python file contains utility scripts to manage taiga translations.
# It has to be run inside the taiga-back git root directory.
#
# The following commands are available:
#
# * update_catalogs: check for new strings in taiga-back catalogs, and
#                    output how much strings are new/changed.
#
# * lang_stats: output statistics for each catalog/language combination
#
# * fetch: fetch translations from transifex.com
#
# * commit: update resources in transifex.com with the local files
#
# Each command support the --languages and --resources options to limit their
# operation to the specified language or resource. For example, to get stats
# for Spanish in contrib.admin, run:
#
#  $ python scripts/manage_translations.py lang_stats --language=es --resources=taiga

import os, errno
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

from subprocess import PIPE, Popen, call

from django.core.management import call_command
from django_jinja.management.commands import makemessages

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.common')
django.setup()


SOURCE_LANG = "en"

def _get_locale_dirs(resources):
    """
    Return a tuple (app name, absolute path) for all locale directories.
    If resources list is not None, filter directories matching resources content.
    """
    contrib_dir = os.getcwd()
    dirs = []

    # Collect all locale directories
    for contrib_name in os.listdir(contrib_dir):
        path = os.path.join(contrib_dir, contrib_name, "locale")
        if os.path.isdir(path):
            dirs.append((contrib_name, path))

    # Filter by resources, if any
    if resources is not None:
        res_names = [d[0] for d in dirs]
        dirs = [ld for ld in dirs if ld[0] in resources]
        if len(resources) > len(dirs):
            print("You have specified some unknown resources. "
                  "Available resource names are: {0}".format(", ".join(res_names)))
            exit(1)

    return dirs


def _tx_resource_for_name(name):
    """ Return the Transifex resource name """
    return "taiga-back.{}".format(name)


def _check_diff(cat_name, lang, base_path):
    """
    Output the approximate number of changed/added strings in the en catalog.
    """
    po_path = "{path}/{lang}/LC_MESSAGES/django.po".format(path=base_path, lang=lang)
    p = Popen("git diff -U0 {0} | egrep '^[-+]msgid' | wc -l".format(po_path),
              stdout=PIPE, stderr=PIPE, shell=True)
    output, errors = p.communicate()
    num_changes = int(output.strip())
    print("{0} changed/added messages in '{1}' for catalog '{2}'".format(num_changes, lang, cat_name))


def _makemessages(languages):
    cmd = makemessages.Command()
    opts = {
        "locale": languages,
        "extensions": ["py", "jinja"],
    }
    call_command(cmd, **opts)


def add_lang(resources=None, languages=None):
    """
    Create .po files for new language(s)
    """
    if not languages:
        print("ERROR: Specify at least one language")
        exit(1)

    locale_dirs = _get_locale_dirs(None)
    errors = []

    for name, dir_ in locale_dirs:
        # check if langs exists
        catalog_langs = sorted([d for d in os.listdir(dir_) if not d.startswith("_") and os.path.isdir(os.path.join(dir_, d))])
        if existing_langs := list(set(catalog_langs) & set(languages)):
            print(f"ERROR: Lang(s) {existing_langs} just exist.")
            exit(1)

    _makemessages(languages)


def update_catalogs(resources=None, languages=None):
    """
    Update the existing .po files with
    new/updated translatable strings.
    """
    os.chdir(os.getcwd())

    # Update all catalog
    locale_dirs = _get_locale_dirs(None)
    for name, dir_ in locale_dirs:
        langs = languages or sorted([d for d in os.listdir(dir_) if not d.startswith("_") and os.path.isdir(os.path.join(dir_, d))])
        _makemessages(langs)

        for lang in langs:
            _check_diff(name, lang, dir_)


def regenerate(resources=None, languages=None):
    """
    Wrap long lines and generate mo files.
    """
    locale_dirs = _get_locale_dirs(resources)
    errors = []

    for name, dir_ in locale_dirs:
        if languages is None:
            languages = sorted([d for d in os.listdir(dir_) if not d.startswith("_") and os.path.isdir(os.path.join(dir_, d)) and d != SOURCE_LANG])

        for lang in languages:
            po_path = "{path}/{lang}/LC_MESSAGES/django.po".format(path=dir_, lang=lang)

            if not os.path.exists(po_path):
                print("No {lang} translation for resource {res}".format(lang=lang, res=name))
                continue

            call("msgcat -o {0} {0}".format(po_path), shell=True)
            res = call("msgfmt -c -o {0}.mo {1}".format(po_path[:-3], po_path), shell=True)

            if res != 0:
                errors.append((name, lang))

    if errors:
        print("\nWARNING: Errors have occurred in following cases:")
        for resource, lang in errors:
            print("\tResource {res} for language {lang}".format(res=resource, lang=lang))

        exit(1)


def lang_stats(resources=None, languages=None):
    """
    Output language statistics of committed translation files for each catalog.
    If resources is provided, it should be a list of translation resource to
    limit the output (e.g. ['main', 'taiga']).
    """
    locale_dirs = _get_locale_dirs(resources)

    for name, dir_ in locale_dirs:
        print("\nShowing translations stats for '{res}':".format(res=name))

        langs = []
        for d in os.listdir(dir_):
            if not d.startswith('_') and os.path.isdir(os.path.join(dir_, d)):
                langs.append(d)
        langs = sorted(langs)

        for lang in langs:
            if languages and lang not in languages:
                continue

            # TODO: merge first with the latest en catalog
            p = Popen("msgfmt -vc -o /dev/null {path}/{lang}/LC_MESSAGES/django.po".format(path=dir_, lang=lang),
                      stdout=PIPE, stderr=PIPE, shell=True)
            output, errors = p.communicate()

            if p.returncode == 0:
                # msgfmt output stats on stderr
                print("{0}: {1}".format(lang, errors.strip().decode("utf-8")))
            else:
                print("Errors happened when checking {0} translation for {1}:\n{2}".format(lang, name, errors))


if __name__ == "__main__":
    RUNABLE_SCRIPTS = {
        "add_lang": "Add a new language.",
        "update_catalogs": "update .po files of all (default) or any language(s).",
        "regenerate": "regenerate .mo files.",
        "lang_stats": "get stats of local translations",
    }

    parser = ArgumentParser(description="manage translations in taiga-back between the repo and transifex.",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("cmd", nargs=1,
        help="\n".join(["{0} - {1}".format(c, h) for c, h in RUNABLE_SCRIPTS.items()]))
    parser.add_argument("-r", "--resources", action="append",
        help="limit operation to the specified resources")
    parser.add_argument("-l", "--languages", action="append",
        help="limit operation to the specified languages")
    options = parser.parse_args()

    if options.cmd[0] in RUNABLE_SCRIPTS.keys():
        eval(options.cmd[0])(options.resources, options.languages)
    else:
        print("Available commands are: {}".format(", ".join(RUNABLE_SCRIPTS.keys())))
