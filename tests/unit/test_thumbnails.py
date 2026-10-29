# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import io

import pytest
from PIL import Image
from psd_tools import PSDImage

from taiga.base.utils.thumbnails import psd_image_factory


def _psd_file(size, color):
    data = io.BytesIO()
    PSDImage.new("RGB", size, color=color).save(data)
    data.seek(0)
    return data


def test_psd_image_factory_composites_the_document():
    image = psd_image_factory(_psd_file((8, 4), (255, 0, 0)))

    assert isinstance(image, Image.Image)
    assert image.size == (8, 4)
    assert image.convert("RGB").getpixel((0, 0)) == (255, 0, 0)


def test_psd_image_factory_rejects_invalid_data():
    with pytest.raises(TypeError):
        psd_image_factory(io.BytesIO(b"not a psd file"))
