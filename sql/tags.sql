CREATE OR REPLACE LANGUAGE plpython2u;

CREATE OR REPLACE FUNCTION unpickle (data text)
  RETURNS text[]
AS $$
    import base64
    import pickle

    return pickle.loads(base64.b64decode(data))
$$ LANGUAGE plpython2u IMMUTABLE;
