#!/bin/bash

python ./manage.py dumpdata -n --indent=4 users.Role > taiga/users/fixtures/initial_role.json
