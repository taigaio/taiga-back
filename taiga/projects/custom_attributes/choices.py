# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _


TEXT_TYPE = "text"
MULTILINE_TYPE = "multiline"
RICHTEXT_TYPE = "richtext"
DATE_TYPE = "date"
URL_TYPE = "url"
DROPDOWN_TYPE = "dropdown"
CHECKBOX_TYPE = "checkbox"
NUMBER_TYPE = "number"

TYPES_CHOICES = (
    (TEXT_TYPE, _("Text")),
    (MULTILINE_TYPE, _("Multi-Line Text")),
    (RICHTEXT_TYPE, _("Rich text")),
    (DATE_TYPE, _("Date")),
    (URL_TYPE, _("Url")),
    (DROPDOWN_TYPE, _("Dropdown")),
    (CHECKBOX_TYPE, _("Checkbox")),
    (NUMBER_TYPE, _("Number")),
)
