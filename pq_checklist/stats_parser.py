#!/opt/freeware/bin/python3

# All imports used
from __future__ import absolute_import, division, print_function
from . import get_command_output, debug_post_msg, try_conv_complex, line_cleanup, avg_list
from collections import defaultdict



class StatsParser() :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, rundir = '/tmp' ):
    '''
    General class with main parsers for stats commands
    '''
    self.samples        = int(samples)
    self.interval       = int(interval)
    self.logger         = logger
    self.rundir         = rundir
    self.ansible_module = ansible_module
    self.commands       = defaultdict(lambda: -1)
    self.functions      = defaultdict(lambda: -1)
    self.data           = { 'info' : defaultdict(lambda: -1), 'stats' : defaultdict(lambda: -1) }

    return(None)

  def collect(self, elements:list = [] ) :
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
    if not parse_function :
      parse_function = self.functions[command_id]

    cmd_out = get_command_output(command=self.commands[command_id], rundir=self.rundir,
                                      pq_logger = self.logger, ansible_module = self.ansible_module)
    if cmd_out['retcode'] == 0 :
      ret = parse_function(cmd_out['stdout'])

    return(ret, cmd_out['retcode'])


  def load_from_file(self,filename, parse_function = None) :
    ret = []
    try :
      with open(filename, mode='r', encoding='utf-8') as f :
        ret = [ l for l in f ]
        if parse_function :
          ret = parse_function(ret)
    except Exception as e :
      debug_post_msg(self.logger, 'Error opening %s : %s'%(filename,e), err=True)
    return(ret)

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
      debug_post_msg(self.logger, 'Error during parse_sar_stats: %s'%e, err=True)
    return(ret,keys)

#######################################################################################################################
#######################################################################################################################
