# PostgreSQL upgrade guide

## Supported versions

Taiga backend is tested against PostgreSQL 13 and PostgreSQL 18. CI runs the test suite on both versions. The full test suite, including `tests/integration/test_postgres_compat.py`, passes on PostgreSQL 18.6 and 13.23. Fresh databases need no code or migration changes. Existing databases created by an older Taiga release may need one preparatory step on the old server (see "Before you start").

Caveat: Django 3.2 is end of life and its official documentation lists PostgreSQL 9.6 as the minimum supported version. It makes no official claim about PostgreSQL 18. Support here rests on Taiga's own test results, not on Django's.

Versions between 13 and 18 are expected to work but are not part of the CI matrix.

## Before you start

- Take a backup and keep the old server available until you have verified the new one.
- Remove the legacy `array_agg_mult` aggregate from the OLD server, before the dump or `pg_upgrade`. Installs migrated by a Taiga release older than 6.7.0 (before commit `a46da85e`, migration 0046 `_delete_unused_function`) still contain `array_agg_mult(anyarray)`, defined with `SFUNC = array_cat`. PostgreSQL 18 cannot restore it (`ERROR:  function array_cat(anyarray, anyarray) does not exist`), and `pg_upgrade` from PostgreSQL 13 or older aborts in `check_for_incompatible_polymorphics`. Taiga does not use it. Check for it with `\da array_agg_mult` or `SELECT * FROM pg_aggregate a JOIN pg_proc p ON p.oid = a.aggfnoid WHERE p.proname = 'array_agg_mult';`, and if present:

  ```sql
  DROP AGGREGATE IF EXISTS array_agg_mult(anyarray);
  ```

- Taiga's database settings in `docker/config.py` are read from the same environment variables as before: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_SSLMODE` and `POSTGRES_DISABLE_SERVER_SIDE_CURSORS`. Nothing changes on the Taiga side.

## Upgrade path 1: dump and restore

Stop Taiga, then dump the database from the old server:

```bash
pg_dump -Fc -h OLD_HOST -U taiga taiga > taiga.dump
```

Create an empty database on the new PostgreSQL 18 server and restore into it:

```bash
createdb -h NEW_HOST -U taiga taiga
pg_restore -h NEW_HOST -U taiga -d taiga --no-owner taiga.dump
```

Drop `--no-owner` if you want to keep the original object owners (the roles must exist on the new server). Indexes are rebuilt by the restore itself, so no `REINDEX` is needed. Refresh statistics:

```sql
ANALYZE;
```

## Upgrade path 2: pg_upgrade

`pg_upgrade` upgrades the cluster in place and is faster for large databases:

```bash
pg_upgrade -b OLD_BINDIR -B NEW_BINDIR -d OLD_DATADIR -D NEW_DATADIR --link --check
pg_upgrade -b OLD_BINDIR -B NEW_BINDIR -d OLD_DATADIR -D NEW_DATADIR --link
```

Run `--check` first, with the same mode flag as the real run. `--link` uses hard links instead of copying files; this is much faster, but the old cluster cannot be used once the new one has started, and both data directories must be on the same file system.

Data checksums: PostgreSQL 18 `initdb` enables data checksums by default, and `pg_upgrade` requires the old and new clusters to have matching checksum settings. If the old cluster has no checksums, either initialise the new cluster with the opt-out flag:

```bash
initdb --no-data-checksums -D NEW_DATADIR
```

or enable checksums on the old cluster before upgrading.

After `pg_upgrade` finishes, regenerate the statistics that were not transferred, as described in the PostgreSQL documentation:

```bash
vacuumdb --all --analyze-in-stages --missing-stats-only
vacuumdb --all --analyze-only
```

`--missing-stats-only` can only be run by a superuser and only together with `--analyze-only` or `--analyze-in-stages`.

If the old cluster's default collation provider was ICU or builtin (clusters created on PostgreSQL 15 or later), the PostgreSQL 18 release notes recommend reindexing all full-text search indexes after `pg_upgrade`, because some full-text search functions may behave differently. For Taiga that is:

```sql
REINDEX INDEX projects_project_textquery_idx;
```

Clusters using the libc provider do not need this.

After `pg_upgrade`, roles keep their existing password hashes, so roles with MD5 passwords still have MD5 hashes. The official Docker image (14 and later) uses `scram-sha-256` in `pg_hba.conf` (initdb default), so reset the passwords (`ALTER ROLE taiga PASSWORD '...'` with `password_encryption = 'scram-sha-256'`) before pointing Taiga at the new server.

## Docker

The official `postgres` image changed its data layout in version 18. `PGDATA` is now version specific (`/var/lib/postgresql/18/docker`) and the image `VOLUME` is `/var/lib/postgresql`. Mount your volume at `/var/lib/postgresql`, not at `/var/lib/postgresql/data`:

```yaml
services:
  taiga-db:
    image: postgres:18
    volumes:
      - taiga-db-data:/var/lib/postgresql
```

For PostgreSQL 17 and older images, the volume must still be mounted at `/var/lib/postgresql/data`.

The 18 image refuses to start on a data directory from the old layout, so do not point it at an existing PostgreSQL 13 volume. Use dump and restore into a fresh volume. Setting `PGDATA=/var/lib/postgresql/data` explicitly keeps the old layout, but only for a NEW empty volume: PostgreSQL 18 cannot open PostgreSQL 13 data files, so it never makes an existing PostgreSQL 13 volume usable.

## Passwords

PostgreSQL 18 deprecates MD5 password authentication. `CREATE ROLE` and `ALTER ROLE` now warn when setting an MD5 password, and MD5 support will be removed in a future major version. The recommended replacement is `scram-sha-256`. Before switching, make sure every client library in use supports SCRAM (including the libpq that your `psycopg2` build uses), then:

1. Set `password_encryption = 'scram-sha-256'` in `postgresql.conf`.
2. Set new passwords for the database roles, including the Taiga role.
3. Change the methods in `pg_hba.conf` to `scram-sha-256`.

## After the upgrade

Point Taiga at the new server, then run:

```bash
python manage.py migrate
python manage.py check
```

`migrate` should report nothing to apply on a correctly restored database. Then open Taiga and verify that projects, user stories and attachments load.

## References

- PostgreSQL 18 release notes (initdb checksums, `--no-data-checksums`, MD5 deprecation): https://www.postgresql.org/docs/18/release-18.html
- PostgreSQL 18 password authentication: https://www.postgresql.org/docs/18/auth-password.html
- PostgreSQL 18 pg_upgrade: https://www.postgresql.org/docs/18/pgupgrade.html
- Official Docker image (PGDATA and VOLUME change in 18): https://hub.docker.com/_/postgres
- docker-library/postgres pull request 1259 (new data layout): https://github.com/docker-library/postgres/pull/1259
