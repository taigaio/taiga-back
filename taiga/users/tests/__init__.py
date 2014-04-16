# -*- coding: utf-8 -*-

from django.db.models.loading import get_model


def create_user(id, save=True, is_superuser=False):
    model = get_model("users", "User")
    domain_member_model = get_model("domains", "DomainMember")
    domain_model = get_model("domains", "Domain")

    instance = model(
       username="user{0}".format(id),
       email="user{0}@taiga.io".format(id),
       first_name="Foo{0}".format(id),
       last_name="Bar{0}".format(id)
    )

    instance.set_password(instance.username)
    if is_superuser:
        instance.is_staff = True
        instance.is_superuser = True

    instance.save()

    domain = domain_model.objects.get(pk=1)
    dm = domain_member_model.objects.create(user=instance,
                                            email=instance.email,
                                            domain=domain)
    if id == 1:
        dm.is_owner = True
        dm.is_staff = True
        dm.save()

    return instance


def create_domain(name, public_register=False):
    domain_model = get_model("domains", "Domain")

    instance = domain_model(name=name,
                            domain=name,
                            public_register=public_register)

    instance.save()
    return instance
