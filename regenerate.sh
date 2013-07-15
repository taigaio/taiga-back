#!/bin/bash

dropdb greenmine
createdb greenmine

python manage.py syncdb --migrate --noinput
python manage.py loaddata initial_user
python manage.py sample_data
