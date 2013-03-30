# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os

try:
    print "Trying import local.py settings..."
    from .local import *
except ImportError:
    print "Trying import development.py settings..."
    from .development import *
