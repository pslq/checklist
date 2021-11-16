#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from . import avg_list, debug_post_msg, pq_round_number
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)

    comms = { 'aix' : "iostat -DRTl %d %d"%(self.interval, self.samples),
              'linux' : "iostat -d -k -N -p ALL -t -x -y %d %d"%(self.interval, self.samples)
              }

    self.commands[bos_data['bos']['os']]['stats'] = comms[self.bos_data.data['bos']['os']]

    self.functions['aix'] = { 'stats' : self.parse_iostat_stats }
    self.functions['linux'] = { 'stats' : self.parse_iostat_stats }

    self.file_sources = {
        'iostat_AIX' : self.parse_iostat_stats,
        'iostat_LINUX' : self.parse_iostat_stats
        }


    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)

#######################################################################################################################
  def update_commands(self) :
    comms = { 'aix' : [ 'stats', "iostat -DRTl %d %d"%(self.interval, self.samples) ],
              'linux' : [ 'stats', "iostat -d -k -N -p ALL -t -x -y %d %d"%(self.interval, self.samples) ]
    }
    self.commands = { k : { v[0] : v[1] } for k,v in comms.items() }
    return(None)

#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    ret = []
    cur_time = datetime.datetime.utcnow().isoformat()
    if update_from_system or len(self.__stats_keys__) < 1 :
      self.update_from_system(elements = elements)

    keys = list(self.data['stats'].keys())
    keys.remove('disk')
    if self.bos_data['bos']['os'] == "aix" :
      keys.remove('time')


    for p,dsk in enumerate(self.data['stats']['disk']) :
      tmp_dict = {}
      for i in keys :
        tmp_dict[i] = consolidate_function(self.data['stats'][i][p])

      if self.bos_data['bos']['os'] == "aix" :
        tmp_dict['bps'] = pq_round_number(tmp_dict['x_bps'])
        try :
          tmp_dict['xfer_block_size'] = pq_round_number(tmp_dict['x_bps']/tmp_dict['x_tps'])
        except :
          tmp_dict['xfer_block_size'] = 0.0
        try :
          tmp_dict['read_ratio']      = pq_round_number((tmp_dict['x_bread']+tmp_dict['x_bwrtn'])/tmp_dict['x_bread']*100)
        except :
          tmp_dict['read_ratio']      = 0.0
        tmp_dict['q_full']          = pq_round_number(tmp_dict['q_serv_qfull'])

      elif self.bos_data['bos']['os'] == "linux" :
        tmp_dict['bps'] = pq_round_number(tmp_dict['rkbs']+tmp_dict['wkss'])
        try :
          tmp_dict['xfer_block_size'] = pq_round_number((tmp_dict['rareq-sz']+tmp_dict['wareq-sz'])/2)
        except :
          tmp_dict['xfer_block_size'] = 0.0
        try :
          tmp_dict['read_ratio']      = pq_round_number((tmp_dict['rs']+tmp_dict['ws'])/tmp_dict['rs']*100)
        except :
          tmp_dict['read_ratio']      = 0.0
        tmp_dict['q_full']          = pq_round_number(tmp_dict['aqu-sz'])

      ret.append({'measurement' : 'iostat_disks',
                  'tags' : { 'host' : self.bos_data['bos']['hostname'], 'disk' : dsk },
                  'fields' : tmp_dict,
                  'time' : cur_time
                 })
    return(ret)


#######################################################################################################################
  def parse_iostat_stats(self, data:list, os='') :
    if 'aix' in [ self.bos_data['bos']['os'], os ] :
      keys = [ 'disk',
               'x_act', 'x_bps', 'x_tps', 'x_bread', 'x_bwrtn',
               'r_rps', 'r_avg_serv', 'r_min_serv', 'r_max_serv', 'r_timeouts', 'r_fail',
               'w_wps', 'w_avg_serv', 'w_min_serv', 'w_max_serv', 'w_timeouts', 'w_fail',
               'q_avg_time', 'q_min_time', 'q_max_time', 'q_avg_wqsz', 'q_avg_sqsz', 'q_serv_qfull', 'time' ]
    elif 'linux' in [ self.bos_data['bos']['os'], os ] :
      keys = [ 'disk',
               'rs', 'rkbs', 'rrqms', 'pct_rrqm', 'rawait', 'rareq-sz',
               'ws', 'wkss', 'wrqms', 'pct_wrqm', 'wawait', 'wareq-sz',
               'ds', 'dkBs', 'drqms', 'pct_drqm', 'dawait', 'dareq-sz',
               'aqu-sz', 'pct_util' ]

    l_stats,self.__stats_keys__ = self.parse_sar_stats(data, keys=keys, specific_reading={})


    self.data['stats'] = {}
    for i in self.__stats_keys__ :
      self.data['stats'][i] = []


    keys.remove('disk')

    for p,dsk in enumerate(l_stats['disk']) :
      try :
        g_p = self.data['stats']['disk'].index(dsk)
        for other_items in keys :
          self.data['stats'][other_items][g_p].append(l_stats[other_items][p])
      except :
        self.data['stats']['disk'].append(dsk)
        for other_items in keys :
          self.data['stats'][other_items].append([l_stats[other_items][p]])

    return(self.data['stats'])


#######################################################################################################################
#######################################################################################################################
