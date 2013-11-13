CREATE LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION unpickle (data text)
  RETURNS text[]
AS $$
    import base64
    import pickle

    return pickle.loads(base64.b64decode(data))
$$ LANGUAGE plpythonu IMMUTABLE;

CREATE INDEX issues_unpickle_tags_index ON issues_issue USING btree (unpickle(tags));
