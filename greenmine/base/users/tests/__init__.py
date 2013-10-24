# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_user(id, save=True, is_superuser=False):
    model = get_model("users", "User")

    instance = model(
       username="user{0}".format(id),
       email="user{0}@greenmine.com".format(id),
       first_name="Foo{0}".format(id),
       last_name="Bar{0}".format(id)
    )

    instance.set_password(instance.username)
    if is_superuser:
        instance.is_staff = True
        instance.is_superuser = True

    if save:
        instance.save()
    return instance
