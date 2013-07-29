#!/bin/bash

# For postgresql
dropdb greenmine
createdb greenmine

python manage.py syncdb --migrate --noinput --traceback
python manage.py loaddata initial_user --traceback
python manage.py loaddata initial_role --traceback
python manage.py sample_data --traceback
python manage.py createinitialrevisions --traceback

