def debug_post_msg(logger, msg:str, screen_only:bool=False, no_screen:bool = False, end:str='\n', \
                           flush:bool=False, raise_type=None,
                           pre_str:str = "") -> None:
  '''
  Parameters :
    logger      = pq_logger class or None
    msg         = Message to be send
    err         = If the message is a error or not
    screen_only = If the message shall not be sent to logger... but to stdout instead
    no_screen   = False

  Helper function to either send messages to the correct logging destionation or....
    write to a file without logger assistance

  If raise_type is defined to something different than None, it will assume that a "raise" call must be called
    at end of the function and the parameter itself is the raise parameter, tested raise_types:
      TypeError
      ValueError
      Exception
  '''
  from sys import stderr as sys_stderr
  from sys import stdout as sys_stdout

  to_send = '%s%s'%(pre_str, msg)

  try :
    if logger and not screen_only :
      cur_level = logger.getEffectiveLevel()
      if   cur_level >= 40 :
        logger.error(to_send)
      elif cur_level >= 30 :
        logger.warning(to_send)
      elif cur_level >= 20 :
        logger.info(to_send)
      elif cur_level >= 10 :
        logger.debug(to_send)

    if not no_screen :
      print(to_send, file=sys_stderr, end=end, flush=flush)

    if raise_type :
      raise raise_type(to_send)

  except Exception as e:
    raise Exception(e)
  return(None)

