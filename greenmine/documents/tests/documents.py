# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core import mail
from django.core.urlresolvers import reverse
import json

from django.contrib.auth.models import User
from ..models import *


