select round(sum(bytes)/1024/1024/1024,2) "DB Size(GB)" from v$datafile;
