from .. import try_conv_complex, debug_post_msg, line_cleanup

# Small function to cleanup the string that wull be used as key
def construct_key(st:str) -> str :
  c_key = st
  for str_to_replace in ( '(', '<', '>', ')', '/', '\'', ' ', '[', ']', '+') :
    st = st.replace(str_to_replace,'_')
  c_key = st.lower()
  return(c_key)

# Small function to create a string out of a list
def contruct_string(lst:list,st:int,ed:int) -> str:
  ret = ' '.join([ lst[v] for v in range(st,len(lst)-abs(ed)) ]).strip()
  return(ret)

def parse_entstat_stats(logger,data:list, only_numeric:bool=True) -> dict :
  '''
  Parse entstat like files
  Parameters :
    data -> list : list with all lines of entstat contents
    only_numeric -> bool : [True,False] Add only numeric values into the return dict

  Returns:
    dict with entstat contents
  '''
  ret = {}
  cur_ent = ''
  inner_key = ''
  inner_keys = {
      "Transmit Statistics:" : 'transmit_stats',
      "General Statistics:" : 'general_stats',
      'Statistics for every adapter in the IEEE 802.3ad Link Aggregation' : 'general_lacp',
      "IEEE 802.3ad Port Statistics" : "lacp_port_stats",
      'Device Statistics' : 'dev_stats',
      "Additional Statistics" : 'addon_stats',
      "Virtual I/O Ethernet Adapter (l-lan) Specific Statistics:" : 'veth_stats'
      }
  append_prefix = {
      'transmit_stats' : [ 'transmit', 'receive' ],
      'general_stats' : [],
      'general_lacp' : [],
      "lacp_port_stats" : [ "actor_state", "partner_state"],
      'dev_stats' : [],
      'addon_stats' : [],
      'veth_stats' : []
      }

  # Begin process the list
  try :
    inner_key = ''
    lacp_key_index = 0
    for ln in line_cleanup(data, remove_endln=True) :
      inner_finder = False
      key,val = [],[]
      lp = ln.split(':')
      # Get inner key
      for k in inner_keys.keys() :
        if k in ln :
          inner_key = inner_keys[k]
          inner_finder = True
          break
      if not inner_finder :
        # Get interface name
        if ln.startswith("ETHERNET STATISTICS") :
          cur_ent = ln.split(' ')[2].replace('(','').replace(')','')
          ret[cur_ent] = {}
        # Get hwaddr
        elif ln.startswith("Hardware Address") :
          inner_lp = ln.split(' ')
          key.append(construct_key("Hardware Address"))
          val.append(inner_lp[2].strip())
        # If : into the line, likely is a line with dev stats
        elif ln.count(':') == 2 :
          key.append(construct_key(lp[0].strip()))
          inner_lp = lp[1].strip().split(' ')

          if inner_lp[0].isnumeric() :
            val.append(try_conv_complex(inner_lp[0].strip()))
            key.append(construct_key(contruct_string(inner_lp,1,0)))
          else :
            val.append(try_conv_complex(inner_lp[-1].strip()))
            key.append(construct_key(contruct_string(inner_lp,0,-1)))
          val.append(try_conv_complex(lp[-1].strip()))
          if len(key) > 1 and len(set(key)) == 1 :
            for p,v in enumerate(append_prefix[inner_key]) :
              if v not in key[p] :
                key[p] = v+'_'+key[p]

        # If : into the line, likely is a line with dev stats
        elif ln.count(':') == 1 :
          if lp[0].isnumeric() :
            val.append(try_conv_complex(lp[0].strip()))
            key.append(construct_key(contruct_string(lp,1,0)))
          else :
            val.append(try_conv_complex(lp[1].strip()))
            key.append(construct_key(contruct_string(lp,0,-1)))

          # Hack to properly handle LACP session
          if inner_key == "lacp_port_stats" :
            if inner_key not in ret[cur_ent] :
              ret[cur_ent][inner_key] = {}
            if "Actor State" in ln :
              lacp_key_index = 0
            elif "Partner State" in ln :
              lacp_key_index = 1
            if not any([ v in ln for v in ( "Partner", "Actor" ) ]) :
              for k,v in zip(key,val) :
                if v != '' or ( only_numeric and not isinstance(v, str) ):
                  try :
                    ret[cur_ent][inner_key][append_prefix[inner_key][lacp_key_index]][k] = v
                  except :
                    ret[cur_ent][inner_key][append_prefix[inner_key][lacp_key_index]] = { k : v }
              key,val = [],[]

      # Populate return dict
      for k,v in zip(key,val) :
        if len(k) > 0 and ((not only_numeric and len(v) > 0) or ( only_numeric and isinstance(v, (int, float, complex)) and not isinstance(v, bool))) :
          if len(inner_key) > 0 :
            try :
              ret[cur_ent][inner_key][k] = v
            except :
              ret[cur_ent][inner_key] = { k : v }
          else :
            try :
              ret[cur_ent][k] = v
            except :
              ret[cur_ent] = { k : v }

  except Exception as e :
    debug_post_msg(logger, 'Error in parse_entstat_stats : %s'%e)
  return(ret)
