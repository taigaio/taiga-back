CREATE OR REPLACE LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION unpickle (data text)
  RETURNS text[]
AS $$
    import base64
    import pickle

    return pickle.loads(base64.b64decode(data))
$$ LANGUAGE plpython3u IMMUTABLE;

DROP INDEX IF EXISTS issues_unpickle_tags_index;
CREATE INDEX issues_unpickle_tags_index ON issues_issue USING btree (unpickle(tags));
