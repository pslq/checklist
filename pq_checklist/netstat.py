#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime



# All imports used
from .stats_parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', preserv_stats = False, bos_info = None) :
    '''
    '''
    super().__init__()
    self.bos_info      = bos_info
    self.preserv_stats = preserv_stats
    self.commands      = {
                           'stats_general' : "netstat -s",
                           'stats_sockets' : "netstat -aon"
                          }
    self.functions     = {
                           'stats_general' : self.parse_netstat_s
                         }

    self.data = { 'stats_general' : {} }

    return(None)

  def get_latest_measurements(self) :
    ret = []
    self.collect()
    for k,v in self.data['stats_general'].items() :
      ret.append({'measurement' : 'netstat_general', 'tags' : { 'host' : self.bos_info['bos']['hostname'], 'protocol' : k }, 'fields' : { **v,  **{ 'time' : int(datetime.datetime.now().timestamp()) } }})
    return(ret)


  def parse_netstat_s(self, data:list) :
    try :
      self.data['stats_general'] = self.parse_net_v_stat_stats(data, has_paragraphs=True)
    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing info : %s'%e, err=True)
    return(self.data['stats_general'])


#######################################################################################################################
#######################################################################################################################
