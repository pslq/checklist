SELECT
  ID,
  parent_id,
  LPAD (' ', LEVEL - 1) || operation || ' ' || options operation,
  object_name,
  NVL (BYTES, 0) BYTES,
   CASE
          WHEN cardinality > 1000000
          THEN    TO_CHAR (TRUNC (cardinality / 1000000))|| 'M'
          WHEN cardinality > 1000
          THEN TO_CHAR (TRUNC (cardinality / 1000)) || 'K'
          ELSE cardinality || ''
    END no_of_rows,
   CASE
          WHEN COST > 1000000
          THEN TO_CHAR (TRUNC (COST / 1000000)) || 'M'
          WHEN COST > 1000
          THEN TO_CHAR (TRUNC (COST / 1000)) || 'K'
          ELSE COST || ''
    END COST
   FROM gv$sql_plan
  WHERE hash_value  = 'PQ_HASH_VALUE'
  START WITH ID     = 0 AND hash_value         = 'PQ_HASH_VALUE'
CONNECT BY PRIOR ID = parent_id AND hash_value = 'PQ_HASH_VALUE'
