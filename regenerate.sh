#!/bin/bash

# For postgresql
echo "-> Remove taiga DB"
dropdb taiga
echo "-> Create taiga DB"
createdb taiga

echo "-> Run syncdb"
python manage.py migrate
# echo "-> Load initial Site"
# python manage.py loaddata initial_site --traceback
echo "-> Load initial user"
python manage.py loaddata initial_user --traceback
echo "-> Load initial project_templates"
python manage.py loaddata initial_project_templates --traceback
echo "-> Load initial roles"
python manage.py loaddata initial_role --traceback
echo "-> Generate sample data"
python manage.py sample_data --traceback
echo "-> Rebuilding timeline"
python manage.py --purge rebuild_timeline
