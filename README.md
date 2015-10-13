# Taiga Backend #

![Kaleidos Project](http://kaleidos.net/static/img/badge.png "Kaleidos Project")
[![Managed with Taiga.io](https://taiga.io/media/support/attachments/article-22/banner-gh.png)](https://taiga.io "Managed with Taiga.io")
[![Build Status](https://travis-ci.org/taigaio/taiga-back.svg?branch=master)](https://travis-ci.org/taigaio/taiga-back "Build Status")
[![Coverage Status](https://coveralls.io/repos/taigaio/taiga-back/badge.svg?branch=master)](https://coveralls.io/r/taigaio/taiga-back?branch=master "Coverage Status")
[![Dependency Status](https://www.versioneye.com/user/projects/561bd091a193340f32001464/badge.svg?style=flat)](https://www.versioneye.com/user/projects/561bd091a193340f32001464)

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

**IMPORTANT: Taiga only runs with python 3.4+**

Initial auth data: admin/123123

If you want a complete environment for production usage, you can try the taiga bootstrapping
scripts https://github.com/taigaio/taiga-scripts (warning: alpha state). All the information about the different installation methods (production, development, vagrant, docker...) can be found here http://taigaio.github.io/taiga-doc/dist/#_installation_guide. 

## Community ##

[Taiga has a mailing list](http://groups.google.com/d/forum/taigaio). Feel free to join it and ask any questions you may have.

To subscribe for announcements of releases, important changes and so on, please follow [@taigaio](https://twitter.com/taigaio) on Twitter.

## Donations ##

We are grateful for your emails volunteering donations to Taiga. We feel comfortable accepting them under these conditions: The first that we will only do so while we are in the current beta / pre-revenue stage and that whatever money is donated will go towards a bounty fund. Starting Q2 2015 we will be engaging much more actively with our community to help further the development of Taiga, and we will use these donations to reward people working alongside us.

If you wish to make a donation to this Taiga fund, you can do so via http://www.paypal.com using the email: eposner@taiga.io
