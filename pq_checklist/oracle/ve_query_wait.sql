select
  rpad(S.USERNAME,11) USR,
  S.STATUS,
  LOCKWAIT,
  rpad(DECODE (S.COMMAND, 0, 'NONE', NVL(A.NAME, 'UNKNOWN')),15) COMD,
  rpad(s.sid,4) SID,
  rpad(s.serial#,6) SERIAL,
  s.inst_id,
  s.sql_hash_value,
  w.event WAIT_EVENT
FROM
  GV$SESSION S, GV$PROCESS P, AUDIT_ACTIONS A, GV$SESSION_WAIT W
WHERE
  S.PADDR = P.ADDR
  AND      A.ACTION (+) = S.COMMAND
  AND      S.STATUS not like 'INACTIVE'
  AND      w.sid = s.sid
  AND      w.inst_id = s.inst_id

