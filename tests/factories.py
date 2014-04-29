# -*- coding: utf-8 -*-
import factory

from taiga.domains import models


class DomainFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Domain

    public_register = False
    scheme = None
    name = "localhost"
    domain = "localhost"
