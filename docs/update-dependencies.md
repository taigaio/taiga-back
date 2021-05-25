# Update dependencies

We can check [Dependabot](https://github.com/taigaio/taiga-back/security/dependabot) to keep updated on dependencies alerts.

To update major dependencies:
- edit `requirements.in` and `requirements-devel.in` to update the version scopes if needed
- activate virtualenv
- launch `./scripts/upgrade` script

This script will:
- update `requirement` files with the latest versiones acording to the `.in` files
- install these latest versions in the virtualenv
- test the new dependencies and commit them when they are ready
