#!/bin/bash

show_answer=true
while [ $# -gt 0 ]; do
  	case "$1" in
    	-y)
    	  	show_answer=false
      	;;
  	esac
	shift
done

if $show_answer ; then
	echo "WARNING!! This script REMOVE your Taiga's database and you LOSE all the data."
	read -p "Are you sure you want to delete all data? (Press Y to continue): " -n 1 -r
	echo    # (optional) move to a new line
	if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
		exit 1
	fi
fi


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
