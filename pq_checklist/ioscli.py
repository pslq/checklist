#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime



# All imports used
from .Stats_Parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, cwd = '/tmp', bos_data = None):
    '''
    '''
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)
    self.commands = { }
    self.functions = { }

    self.data = { 'stats' : {} }

    self.file_sources = {
        'entstat' : self.parse_entstat_d_from_dict,
    }

    self.commands = /usr/ios/cli/ioscli

    self.commands = {
        'stats_fcstat_client' : "/usr/ios/cli/ioscli fcstat -client"
        }
    self.functions = {
        'stats' : self.parse_mpstat_stats
        }

    self.file_sources = {
        'mpstat_a' : self.parse_mpstat_stats
        }

/usr/sbin/vnicstat [-b][-d][-r] <vnicserverX>


    return(None)

  def update_commands(self) :
    '''
    Update commands and functions dict
    '''
    try :
      # In case self.commands and self.functions hasn't been populated yet
      for dev in self.bos_data['dev_class']['adapter'] :
        if 'ent' in dev and :
          key = 'stats_seastat_%s'%dev
          self.commands[key] = "/usr/ios/cli/ioscli seastat -d %s -n"%dev
          self.functions[key] = self.parse_seastat
    except Exception as e :
      debug_post_msg(self.logger, 'Error loading device specific commands, possibly bos_data not initialized : %s'%e, raise_type=Exception)

    return(None)

  def get_measurements(self, update_from_system:bool=True) :
    ret = []
    if update_from_system :
      self.update_from_system()

    for ent, ent_data in self.data['stats'].items() :
      for tag in ( 'transmit_stats', 'general_stats', 'dev_stats' ) :
        if tag in ent_data :
          ret.append({'measurement' : 'entstat',
                      'tags' : { 'host' : self.bos_data['bos']['hostname'], 'stats_type' : tag, 'interface' : ent },
                      'fields' : ent_data[tag],
                      'time' : datetime.datetime.utcnow().isoformat()
                     })
    return(ret)


  def parse_entstat_d_from_dict(self, data:dict) :
    for adapter,adapter_data in data.items() :
      self.parse_entstat_d(adapter_data.split('\n'))
    return(None)

  def parse_entstat_d(self, data:list) :
    try :
      self.data['stats'].update(self.parse_entstat_stats(data))

    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing parse_entstat_d: %s'%e)
    return(self.data['stats'])


#######################################################################################################################
#######################################################################################################################
