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

Taiga only runs with python 3.4+

Initial auth data: admin/123123

If you want a complete environment for production usage, you can try the taiga bootstrapping
scripts https://github.com/taigaio/taiga-scripts (warning: alpha state)

## Community ##

[Taiga has a mailing list](http://groups.google.com/d/forum/taigaio). Feel free to join it and ask any questions you may have.

To subscribe for announcements of releases, important changes and so on, please follow [@taigaio](https://twitter.com/taigaio) on Twitter.

## Donations ##

We are grateful for your emails volunteering donations to Taiga. We feel comfortable accepting them under these conditions: The first that we will only do so while we are in the current beta / pre-revenue stage and that whatever money is donated will go towards a bounty fund. Starting Q2 2015 we will be engaging much more actively with our community to help further the development of Taiga, and we will use these donations to reward people working alongside us.

If you wish to make a donation to this Taiga fund, you can do so via paypal using the email: eposner@taiga.io

<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
<input type="hidden" name="cmd" value="_s-xclick">
<input type="hidden" name="hosted_button_id" value="HM3BBRQXY2BHN">
<input type="image" src="https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
<img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
</form>

