#!/bin/bash

# Copyright (C) 2014-present Taiga Agile LLC
#
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

echo "Specify database name:"
read database
if [ -z "$database" ]; then
    exit 1
fi

echo "-> Remove taiga DB" $database
dropdb $database
echo "-> Create taiga DB"
createdb $database

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
