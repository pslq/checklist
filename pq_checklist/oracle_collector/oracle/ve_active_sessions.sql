select
  rpad(S.USERNAME,18) USR,
  S.STATUS,
  LOCKWAIT,
  rpad(DECODE (S.COMMAND, 0, 'NONE', NVL(A.NAME, 'UNKNOWN')),15) CMD,
  rpad(s.sid,8) SID,
  rpad(s.serial#,8) SERIAL,
  s.inst_id,
  sql.HASH_VALUE,
  s.sql_id,
  sql.sql_text
FROM
  GV$SESSION S, GV$PROCESS P, AUDIT_ACTIONS A, GV$SQLAREA SQL
WHERE
  S.PADDR = P.ADDR AND A.ACTION (+) = S.COMMAND and
  S.STATUS not like 'INACTIVE' and s.sql_id = sql.sql_id

