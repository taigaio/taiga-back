# -*- coding: utf-8 -*-
from . import throttling


class ImportThrottlingPolicyMixin:
    throttle_classes = (throttling.ImportModeRateThrottle,)
