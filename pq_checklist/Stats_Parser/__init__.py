#!/opt/freeware/bin/python3

# All imports used
from __future__ import absolute_import, division, print_function
from .. import get_command_output, debug_post_msg, try_conv_complex, line_cleanup, avg_list
from collections import defaultdict
from ._parse_net_v_stat_stats import parse_net_v_stat_stats
from ._parse_entstat_stats import parse_entstat_stats
import os




class StatsParser() :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None ):
    '''
    General class with main parsers for stats commands
    '''
    self.samples        = int(samples)
    self.interval       = int(interval)
    self.logger         = logger
    self.cwd            = cwd
    self.bos_data       = bos_data
    self.iambos         = False
    self.commands       = { 'linux' : defaultdict(lambda: '/bin/true'), 'aix' : defaultdict(lambda: '/bin/true') }
    self.functions      = { 'linux' : defaultdict(lambda: '/bin/true'), 'aix' : defaultdict(lambda: '/bin/true') }
    self.data           = {}
    self.file_sources   = {}
    self.only_on_localhost = False # Load the collector only on localnode

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
  def parse_net_v_stat_stats(self, data:list, has_paragraphs:bool=True) -> dict:
    return(parse_net_v_stat_stats(self.logger,data,has_paragraphs=has_paragraphs))

  def parse_entstat_stats(self,data:list, only_numeric:bool=True) -> dict :
    return(parse_entstat_stats(self.logger,data, only_numeric=only_numeric))


#######################################################################################################################
  def update_from_dict(self, data:dict, debug:bool=False) -> None :
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
      elif debug :
        debug_post_msg(self.logger, '%s not present into file_sources'%element['task'])

    return(None)

#######################################################################################################################
  def update_from_system(self, elements:list = [] ) :
    '''
    Collect data from the system for specific elements ( objects )
    '''
    # In case bos still empty
    run_os = None
    if self.bos_data :
      run_os = self.bos_data.data['bos']['os']
    elif self.iambos :
      run_os = 'aix' if 'aix' in os.sys.platform else os.sys.platform
    if run_os :
      if self.bos_data :
        if len(self.bos_data.data['dev_class']) == 0 :
          self.bos_data.update_from_system()
      if len(self.commands[run_os].keys()) == 0 and "update_commands" in self.__dir__() :
        self.update_commands()

      for i in elements if len(elements) > 0 else self.commands[run_os].keys() :
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
    run_os = None

    if command_id :
      if self.bos_data :
        run_os = self.bos_data.data['bos']['os']
      elif self.iambos :
        run_os = 'aix' if 'aix' in os.sys.platform else os.sys.platform
    if run_os :
      if not parse_function and command_id in self.functions[run_os] :
        parse_function = self.functions[run_os][command_id]

      if parse_function :
        cmd_out = get_command_output(command        =self.commands[run_os][command_id],
                                     cwd            = self.cwd,
                                     pq_logger      = self.logger)
        if cmd_out['retcode'] == 0 :
          try :
            ret = parse_function(cmd_out['stdout'])
          except Exception as e :
            debug_post_msg(self.logger,'Error during parsing function : %s : %s : %s'%(e,run_os,command_id))
        else :
          debug_post_msg(self.logger,'Error executing command %s : %s : %s'%(self.commands[run_os][command_id],str(cmd_out['stdout']), str(cmd_out['stderr'])))
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
  def parse_sar_stats(self, data:list, key_heading:str='cpu', \
                            specific_reading:dict = { 'key_position' : 0, 'key_value' : 'ALL' }, \
                            readings_to_ignore:list=[{ 'key_position' : 0, 'key_value' : ['-----']}], \
                            keys:list=[]) :
    ret = {}
    try :
      for dt in line_cleanup(data, remove_endln=True) :
        if len(keys) > 0 :
          elms = dt.split(' ')
          if len(elms) == len(keys) :
            to_add = True
            if len(specific_reading.keys()) > 0 :
              if elms[specific_reading['key_position']] != specific_reading['key_value'] :
                to_add = False
            if len(readings_to_ignore) > 0 :
              for dt in readings_to_ignore :
                if elms[dt['key_position']] in dt ['key_value'] :
                  to_add = False
                  break
            if to_add :
              for p,v in enumerate(elms) :
                tmp_val = v.replace(',', '.')
                if tmp_val[-1].lower() == 'k' :
                  val = try_conv_complex(tmp_val[:-1])*1024
                elif tmp_val[-1].lower() == 'm' :
                  val = try_conv_complex(tmp_val[:-1])*1024*1024
                else :
                  val = try_conv_complex(tmp_val)
                try :
                  if val == '-' :
                    val = 0
                except :
                  pass
                try :
                  ret[keys[p]].append(val)
                except :
                  ret[keys[p]] = [ val ]
        elif dt.startswith(key_heading) :
          keys = dt.replace('%', '').split(' ')
    except Exception as e :
      debug_post_msg(self.logger, 'Error during parse_sar_stats: %s'%e)
    return(ret,keys)

#######################################################################################################################
