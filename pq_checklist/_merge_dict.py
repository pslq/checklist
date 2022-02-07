def merge_dict(*dcts) :
  '''
  Merge too dictionaries together recursively.
    If a list if found as value, it can append values
    If a tuple is found, it will be converted to list

  :type dcts: dict
  :param dcts: dictionaries to be merged togehter

  Returns:
    The merged dictionary
  '''
  def __handle_kv__(elm,v) :
    if isinstance(v, tuple) :
      nv = list(v)
    elif isinstance(v, str) :
      nv = v
    else :
      try :
        iter(v)
        nv = v
      except :
        nv = [ v ]

    try :
      elm += nv
    except :
      elm = nv
    return(elm)

  ret = {}

  for dc in dcts :
    for k,v in dc.items() :
      if k not in ret :
        ret[k] = None
      ret[k] = __handle_kv__(ret[k],v)

  return(ret)
