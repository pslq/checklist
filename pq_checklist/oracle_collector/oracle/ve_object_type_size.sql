SELECT SEGMENT_TYPE, SUM(BYTES)/1024/1024/1024 
FROM DBA_SEGMENTS 
WHERE OWNER NOT IN ( PQ_NOTOWNERS )
GROUP BY SEGMENT_TYPE 
ORDER BY SEGMENT_TYPE;
