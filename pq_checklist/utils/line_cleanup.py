def line_cleanup(iterable, split=False, delimiter='', cleanup = True, remove_endln = False) :
  '''
  Cleanup the contents of a iterable of a string in order to facilitate processing
  Parameters:
    iterable  : iterable or string to be processed
    split     : if attempt to split the cleaned string into a list
    delimiter : delimiter to be used when tryping to split the output string
    cleanup   : if really try to cleanup duplicated spaces and tabs
    remove_endln : If line terminator will be removed along with the cleanup ( no cr, just lf )

  Returns :
    Iterable
  '''
  import unicodedata
  ret = iterable

  for ln in iterable :
    if isinstance(ln, bytes) :
      ln = ln.decode()
    try :
      if cleanup :
        ln = ''.join(c for c in ln if not unicodedata.category(c).startswith('C'))
        while '  ' in ln :
          ln = ln.strip().replace('\t',' ').replace('  ', ' ')
      if remove_endln :
        lp = ln.split('\n')
        ln = ''.join(lp)
      if split :
        yield(ln.split(delimiter))
      else :
        yield(ln)
    except :
      yield(ln)

