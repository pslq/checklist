#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime



# All imports used
from .stats_parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', preserv_stats = False) :
    '''
    '''
    super().__init__()
    self.preserv_stats  = preserv_stats
    self.commands = {
        'stats_general' : "netstat -s"
        'stats_sockets' : "netstat -aon"

        }
    self.functions = {
        'stats_general' : self.parse_netstat_s
        }

    # Internal list to hold all keys used when parsing lparstat data
    self.__stats_keys__ = []

    return(None)


  def get_latest_measurements(self, elements = [ 'stats_general' ], consolidate_function = avg_list, use_existent:bool=True) :
    if not use_existent or len(self.__stats_keys__) < 1 :
      self.collect(elements = elements)

    data = self.collect(elements = elements)
    to_be_added = {'measurement' : 'lparstat', 'tags' : { 'host' : self.data['info']['node_name'] }, 'fields' : { 'time' : int(datetime.datetime.now().timestamp()) } }
    for key in self.data['stats'].keys() :
      to_be_added['fields'][key] = consolidate_function(self.data['stats'][key])

    return(to_be_added)


  def parse_netstat_s(self, data:list) :
    try :
      self.data['stats_general'] = self.parse_net_v_stat_stats(data, has_paragraphs=True)
    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing info : %s'%e, err=True)
    return(self.data['stats_general'])


#######################################################################################################################
#######################################################################################################################
