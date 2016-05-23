#!/bin/bash

python ./manage.py dumpdata --format json \
                            --indent 4 \
                            --output './taiga/projects/fixtures/initial_project_templates.json' \
                            'projects.ProjectTemplate'
