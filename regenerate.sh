#!/bin/bash

# For postgresql
echo "-> Remove taiga DB"
dropdb taiga
echo "-> Create taiga DB"
createdb taiga

echo "-> Load migrations"
python manage.py migrate
echo "-> Load initial user (admin/123123)"
python manage.py loaddata initial_user --traceback
echo "-> Load initial project_templates (scrum/kanban)"
python manage.py loaddata initial_project_templates --traceback
echo "-> Generate sample data"
python manage.py sample_data --traceback
echo "-> Rebuilding timeline"
python manage.py rebuild_timeline --purge
