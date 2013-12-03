alter table base_site rename to domains_domain;
alter table base_sitemember rename to domains_domainmember;
delete from south_migrationhistory;
