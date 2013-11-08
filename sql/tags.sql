CREATE OR REPLACE FUNCTION unpickle (data text)
  RETURNS text[]
AS $$
    import base64
    import pickle

    return pickle.loads(base64.b64decode(data))
$$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION array_uniq_join (data text[], data2 text[])
  RETURNS text[]
AS $$
    tmp = set(data)
    tmp.update(data2)
    return tuple(tmp)
$$ LANGUAGE plpythonu;

DROP AGGREGATE array_uniq_concat (text[]);
CREATE AGGREGATE array_uniq_concat (text[])
(
    sfunc = array_uniq_join,
    stype = text[],
    initcond = '{}'
);
