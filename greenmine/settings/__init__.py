# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os

if "GREENMINE_ENVIRON" in os.environ:
    if os.environ["GREENMINE_ENVIRON"] in ('production', 'development', 'local'):
        print "importing %s" % os.environ["GREENMINE_ENVIRON"]
        eval("from .%s import *" % (os.environ["GREENMINE_ENVIRON"]))

else:
    try:
        print "Trying import local.py settings..."
        from .local import *
    except ImportError:
        print "Trying import development.py settings..."
        from .development import *
