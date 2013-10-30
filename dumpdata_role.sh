#!/bin/bash

python ./manage.py dumpdata -n --indent=4 users.Role > greenmine/base/users/fixtures/initial_role.json
