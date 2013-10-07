# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_user(id, save=True):
    model = get_model("users", "User")

    instance = model(
       username="user{0}".format(id),
       email="user{0}@greenmine.com",
       first_name="Foo{0}".format(id),
       last_name="Bar{0}".format(id)
    )
    instance.set_password(instance.username)

    if save:
        instance.save()
    return instance
