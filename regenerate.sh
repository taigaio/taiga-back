#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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

read -p 'Specify a Postgres user [default: taiga]: ' dbuser
read -p 'Specify database name [default: taiga]: ' dbname
read -p 'Specify host [default: 127.0.0.1]: ' dbhost
read -p 'Specify port [default: 5432]: ' dbport
dbuser=${dbuser:-taiga}
dbname=${dbname:-taiga}
dbhost=${dbhost:-127.0.0.1}
dbport=${dbport:-5432}

echo "-> Remove '${dbname}' DB"
dropdb -U $dbuser -h $dbhost -p $dbport $dbname
echo "-> Create '${dbname}' DB"
createdb -U $dbuser -h $dbhost -p $dbport $dbname

if [ "$?" -ne "0" ]; then
    echo && echo "Error accessing the database, aborting."
else
    echo "-> Load migrations"
    python manage.py migrate
    python manage.py createcachetable
    echo "-> Load initial user (admin/123123)"
    python manage.py loaddata initial_user --traceback
    echo "-> Load initial project_templates (scrum/kanban)"
    python manage.py loaddata initial_project_templates --traceback
    echo "-> Generate sample data"
    python manage.py sample_data --traceback
    echo "-> Rebuilding timeline"
    python manage.py rebuild_timeline --purge
fi
