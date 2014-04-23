# -*- coding: utf-8 -*-

# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
