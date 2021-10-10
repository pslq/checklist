#!/opt/freeware/bin/python3

# All imports used
from __future__ import absolute_import, division, print_function
from . import get_command_output, debug_post_msg, try_conv_complex, line_cleanup, avg_list
from collections import defaultdict
import concurrent.futures




class StatsParser() :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None ):
    '''
    General class with main parsers for stats commands
    '''
    self.samples        = int(samples)
    self.interval       = int(interval)
    self.logger         = logger
    self.cwd            = cwd
    self.ansible_module = ansible_module
    self.bos_data       = bos_data
    self.commands       = {}
    self.functions      = {}
    self.data           = { 'info' : defaultdict(lambda: -1), 'stats' : defaultdict(lambda: -1) }
    self.file_sources   = {}
    self.only_on_localhost = False # Load the collector only on localnode

    # Internal list to hold all keys used when parsing lparstat data
    self.__stats_keys__ = []

    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)

#######################################################################################################################
  def __getitem__(self,key):
    '''
    Return dict like results
    '''
    ret = self.data

    # Auto update itself in case the key is empty
    if key not in self.data :
      debug_post_msg(self.logger, '%s not initialized yet, please feed data to it'%__file__, raise_type=Exception)
    else :
      ret = self.data[key]
    return(ret)

#######################################################################################################################
  def keys(self) :
    '''
    Return keys within data directory
    '''
    return(self.data.keys())

#######################################################################################################################
  def update_from_dict(self, data:dict) -> None :
    '''
    Instead of load data from the local system, parse data gattered through ansible in order to issue measurements

    Parameters:
      data: dict -> dict of data to be parsed ( output from an ansible playbook )

      Possible keys so far can be found at self.file_sources

    Returns:
      None
    '''
    for element in data :
      if element['task'] in self.file_sources :
        self.file_sources[element['task']](element['stdout_lines'])

    return(None)

#######################################################################################################################
  def update_from_system(self, elements:list = [] ) :
    '''
    Collect data from the system for specific elements ( objects )
    '''
    # In case bos still empty
    try :
      if len(self.bos_data.data['dev_class']) == 0 :
        self.bos_data.update_from_system()
    except :
      pass
    # In case commands dict still not initialized
    if len(self.commands.keys()) == 0 and "update_commands" in self.__dir__() :
      self.update_commands()
    # If no element is passed, collect data from all of them
    if len(elements) == 0 :
      elements = [ c for c in self.commands.keys() if c in self.functions ]

    for i in elements :
      self.load_from_system(command_id = i)
    return(self.data)

#######################################################################################################################
  def load_from_system(self, command_id = None, parse_function = None ) :
    '''
    Load stats from the system, if an ansible module is passed during class initialization,
      the ansible module will be used to execute the code.

    Parameters :
      command_id -> [info,stats] : string with the type of information that will be fetch, the actual commands executed are stored at the dict commands within the class
      parse_function -> function -> Function that will be used to parse data out of the command, if left as None, it will pick one based on the comnmand_id

    Returns :
      dict, retcode
        dict -> Dictionary with the parsed output of the command
        retcode -> Return code of the actual command executed, if != 0, the dict ovject might be empty
    '''
    ret = None
    cmd_out = { 'retcode' : -1 }

    if command_id :
      if not parse_function and command_id in self.functions :
        parse_function = self.functions[command_id]

      cmd_out = get_command_output(command        =self.commands[command_id],
                                   cwd            = self.cwd,
                                   pq_logger      = self.logger,
                                   ansible_module = self.ansible_module)
      if cmd_out['retcode'] == 0 :
        ret = parse_function(cmd_out['stdout'])
    else :
      debug_post_msg(self.logger,'Empty command_id, command execution not possible, possible command ids: %s'%(str(self.functions.keys())), raise_type=Exception)

    return(ret, cmd_out['retcode'])

#######################################################################################################################
  def get_latest_measurements(self, debug=False, update_from_system:bool = True) :
    '''
    Get in influxdb format latest cpu utilization measurements from the lpar

    Parameters:
      debug : bool -> [True,False] Log into syslog amount of time that took to get the measurements
      update_from_system: bool = Get latest data from the local system before give any measurement


    Returns:
      list of measurements
    '''
    print('ASASASASASSA')
    from time import time
    st = time()
    if update_from_system:
      self.update_from_system()

    ret = [ i.get_latest_measurements(update_from_system = update_from_system) for i in self.measurement_providers ]
    if debug :
      duration = time() - st
      debug_post_msg(self.logger,'Collect Task Duration: %d seconds'%int(duration))

    return(ret)



#######################################################################################################################
  def load_from_file(self,filename:str, parse_function = None) -> list :
    '''
    Load text file into a list that will be proccessed by the parser function
    Parameter:
      filename       : str -> Full path of the file that will be loaded
      parse_function : obj -> Function that can be used to parse the list

    Returns:
      list
    '''
    ret = []
    try :
      with open(filename, mode='r', encoding='utf-8') as f :
        ret = [ l for l in f ]
        if parse_function :
          ret = parse_function(ret)
    except Exception as e :
      debug_post_msg(self.logger, 'Error opening %s : %s'%(filename,e))
    return(ret)

#######################################################################################################################
  def parse_entstat_stats(self,data:list, only_numeric:bool=True) -> dict :
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
      debug_post_msg(self.logger, 'Error in parse_entstat_stats : %s'%e)
    return(ret)
#######################################################################################################################
  def parse_net_v_stat_stats(self, data:list, has_paragraphs:bool=True) -> dict:
    '''
    Parse aix's "netstat -s" like files

    Parameters:
      data           : list -> List of strings to be parsed ( loaded from either command output of file )
      has_paragraphs : bool -> If the file contents has paragraphs ( like netstat -s )

    Returns:
      dict
    '''
    ret = {}
    cur_key = ''
    exclude = ( '(', '<', '>', ')', '/', '\'' )
    for ln in line_cleanup(data, remove_endln=True) :
      sp = ln.split(' ')
      if len(sp) == 1 and sp[0].endswith(':') and has_paragraphs :
        cur_key = sp[0].rstrip(':')
      else :
        key,val = 1,0
        if sp[-1].isnumeric() :
          key,val = 0,-1
        kt = '_'.join([ sp[v] for v in range(key,len(sp)-abs(val)) if not any([ Z in sp[v] for Z in exclude]) ]).lower().replace('.', '').replace(':','').replace(',','')
        vn = try_conv_complex(sp[val])
        if len(kt) > 0 and len(str(vn)) > 0 :
          # Quick fix due the miss behavior of netstat
          if 'ack' in kt and kt[-1].isalnum() :
            kt = 'ack_for_bytes'
          if has_paragraphs :
            try :
              ret[cur_key][kt] = vn
            except :
              ret[cur_key] = { kt : vn }
          else :
            ret[kt] = vn
    return(ret)

#######################################################################################################################
  def parse_sar_stats(self, data:list, key_heading:str='cpu', \
                            specific_reading:dict = { 'key_position' : 0, 'key_value' : 'ALL' }, \
                            readings_to_ignore:dict={ 'key_position' : 0, 'key_value' : '-----'}) :
    ret = {}
    keys = []
    try :
      for dt in line_cleanup(data, remove_endln=True) :
        if dt.startswith(key_heading) :
          keys = dt.replace('%', '').split(' ')
        elif len(keys) > 0 :
          elms = dt.split(' ')
          if len(elms) == len(keys) :
            to_add = True
            if len(specific_reading.keys()) > 0 :
              if elms[specific_reading['key_position']] != specific_reading['key_value'] :
                to_add = False
            if len(readings_to_ignore.keys()) > 0 :
              if elms[readings_to_ignore['key_position']] == readings_to_ignore['key_value'] :
                to_add = False
            if to_add :
              for p,v in enumerate(elms) :
                val = try_conv_complex(v.replace(',', '.'))
                try :
                  if val == '-' :
                    val = 0
                except :
                  pass
                try :
                  ret[keys[p]].append(val)
                except :
                  ret[keys[p]] = [ val ]
    except Exception as e :
      debug_post_msg(self.logger, 'Error during parse_sar_stats: %s'%e)
    return(ret,keys)

#######################################################################################################################
