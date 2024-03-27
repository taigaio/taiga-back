# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from contextlib import contextmanager


@contextmanager
def without_signals(*disablers):
    for disabler in disablers:
        if not (isinstance(disabler, list) or isinstance(disabler, tuple)) or len(disabler) == 0:
            raise ValueError("The parameters must be lists of at least one parameter (the signal).")

        signal, *ids = disabler
        signal.backup_receivers = signal.receivers
        signal.receivers = list(filter(lambda x: x[0][0] not in ids, signal.receivers))

    try:
        yield
    except Exception as e:
        raise e
    finally:
        for disabler in disablers:
            signal, *ids = disabler
            signal.receivers = signal.backup_receivers
