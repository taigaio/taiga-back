# Taiga Backend #

![Kaleidos Project](http://kaleidos.net/static/img/badge.png "Kaleidos Project")

[![Travis Badge](https://img.shields.io/travis/taigaio/taiga-back.svg?style=flat)](https://travis-ci.org/taigaio/taiga-back "Travis Badge")

[![Coveralls](http://img.shields.io/coveralls/taigaio/taiga-back.svg?style=flat)](https://travis-ci.org/taigaio/taiga-back "Coveralls")

## Setup development environment ##

Just execute these commands in your virtualenv(wrapper):

```
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py loaddata initial_user
python manage.py loaddata initial_project_templates
python manage.py loaddata initial_role
python manage.py sample_data
```

Taiga only runs with python 3.3+.

Initial auth data: admin/123123

If you want a complete environment for production usage, you can try the taiga bootstrapping
scripts https://github.com/taigaio/taiga-script (warning: alpha state)

## Community ##

[Taiga has a mailing list](http://groups.google.com/d/forum/taigaio). Feel free to join it and ask any questions you may have.

To subscribe for announcements of releases, important changes and so on, please follow [@taigaio](https://twitter.com/taigaio) on Twitter.
