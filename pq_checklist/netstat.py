#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
from .Stats_Parser import StatsParser
import csv, datetime

class parser(StatsParser) :
  def __init__(self, logger = None, cwd = '/tmp', preserv_stats = False, bos_data = None, samples = 2, interval = 1) :
    '''
    '''
    super().__init__(logger = logger, cwd = cwd, bos_data=bos_data)
    self.bos_data      = bos_data
    self.preserv_stats = preserv_stats
    self.commands['aix']      = {
                           'stats_general' : "netstat -s",
                           'stats_sockets' : "netstat -aon"
                          }
    self.functions['aix']     = {
                           'stats_general' : self.parse_netstat_s
                         }

    self.data['stats_general'] = {}

    self.file_sources = {
        'netstat_s' : self.parse_netstat_s,
    }


    return(None)

  def get_measurements(self, update_from_system:bool=True) -> list:
    ret = []
    if update_from_system :
      self.update_from_system()

    cur_time = datetime.datetime.utcnow().isoformat()

    for proto,proto_data in self.data['stats_general'].items() :
      fields = {}
      for tag_name, tag_data in proto_data.items() :
        if isinstance(tag_data,dict) :
          tag_fields = {}
          for subtag_name, subtag_data in tag_data.items() :
            if isinstance(subtag_data, dict) :
              ret.append({'measurement' : 'netstat_general',
                'tags' : { 'host' : self.bos_data['bos']['hostname'], 'protocol' : proto, 'session_group' : subtag_name, 'session' : tag_name },
                'fields' : subtag_data,
                'time' : cur_time
                })
            else :
              tag_fields[subtag_name] = subtag_data
          ret.append({'measurement' : 'netstat_general',
                'tags' : { 'host' : self.bos_data['bos']['hostname'], 'protocol' : proto, 'session' : tag_name },
                'fields' : tag_fields,
                'time' : cur_time
               })
        else :
          fields[tag_name] = tag_data
      ret.append({'measurement' : 'netstat_general',
                  'tags' : { 'host' : self.bos_data['bos']['hostname'], 'protocol' : proto },
                  'fields' : fields,
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
