import copy
def merge_dict(*dcts, append_strings:bool=False) :
  '''
  Merge too dictionaries together recursively.
    If a list is found as value, values will be appended
    If a tuple is found, it will be converted to list
    If a int/float,str is found, it will be converted to a list and values will be appended
    If a str is found, the behavior can be changed to append the strings instead of convert to a list through the parameter append_strings

  :type dcts: dict
  :param dcts: dictionaries to be merged togehter

  :type append_strings: bool
  :param append_strings: when dealing with strings in the values if those will be appended together or if only the last one will remain

  Returns:
    The merged dictionary
  '''
  ret = {}

  def __handle_kv__(elm,v) :
    if isinstance(v, tuple) :
      nv = list(v)
    elif isinstance(v, str) :
      if append_strings :
        nv = v
      else :
        nv = [ v ]
    else :
      try :
        iter(v)
        nv = v
      except :
        nv = [ v ]
    if elm :
      n_elm = copy.deepcopy(elm)
    else :
      n_elm = elm

    try :
      n_elm += nv
    except :
      n_elm = nv
    return(n_elm)

  for dc in dcts :
    for k,v in dc.items() :
      if k not in ret :
        ret[k] = None
      ret[k] = __handle_kv__(ret[k],v)

  return(ret)
