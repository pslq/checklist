#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime



# All imports used
from .Stats_Parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', preserv_stats = False, bos_data = None) :
    '''
    '''
    super().__init__(logger = logger, cwd = cwd, ansible_module = ansible_module)
    self.bos_data      = bos_data
    self.preserv_stats = preserv_stats
    self.commands      = {
                           'stats_general' : "netstat -s",
                           'stats_sockets' : "netstat -aon"
                          }
    self.functions     = {
                           'stats_general' : self.parse_netstat_s
                         }

    self.data = { 'stats_general' : {} }

    self.file_sources = {
        'netstat_s' : self.parse_netstat_s,
    }


    return(None)

  def get_measurements(self, update_from_system:bool=True) :
    ret = []
    if update_from_system :
      self.update_from_system()

    for k,v in self.data['stats_general'].items() :
      ret.append({'measurement' : 'netstat_general',
                  'tags' : { 'host' : self.bos_data['bos']['hostname'], 'protocol' : k },
                  'fields' : v,
                  'time' : datetime.datetime.utcnow().isoformat()
                 })
    return(ret)


  def parse_netstat_s(self, data:list) :
    try :
      self.data['stats_general'] = self.parse_net_v_stat_stats(data, has_paragraphs=True)
    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing parse_netstat_s : %s'%e)

    return(self.data['stats_general'])


#######################################################################################################################
#######################################################################################################################
