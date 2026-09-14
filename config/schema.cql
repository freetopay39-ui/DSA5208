CREATE KEYSPACE IF NOT EXISTS dsa5208
WITH replication = {'class':'NetworkTopologyStrategy', 'dc1':3};

CREATE TABLE IF NOT EXISTS dsa5208.items (
  history text,
  k text,
  value text,
  PRIMARY KEY ((history, k))
) WITH read_repair = 'BLOCKING'
  AND speculative_retry = 'NONE';
