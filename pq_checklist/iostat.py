#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from . import avg_list
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, cwd = cwd)

    self.bos_data = bos_data
    self.commands = {
        'stats' : "iostat -DRTl %d %d"%(self.interval, self.samples)
        }
    self.functions = {
        'stats' : self.parse_iostat_stats
        }

    self.file_sources = {
        'iostat_drtl' : self.parse_iostat_stats
        }


    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)


#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    ret = []
    if update_from_system or len(self.__stats_keys__) < 1 :
      self.update_from_system(elements = elements)

    return(ret)


#######################################################################################################################
  def parse_iostat_stats(self, data:list) :
    keys = [ 'disk',
             'x_act', 'x_bps', 'x_tps', 'x_bread', 'x_bwrtn',
             'r_rps', 'r_avg_serv', 'r_min_serv', 'r_max_serv', 'r_timeouts', 'r_fail',
             'w_wps', 'w_avg_serv', 'w_min_serv', 'w_max_serv', 'w_timeouts', 'w_fail',
             'q_avg_time', 'q_min_time', 'q_max_time', 'q_avg_wqsz', 'q_avg_sqsz', 'q_serv_qfull', 'time' ]

    self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, keys=keys, specific_reading={})
    return(self.data['stats'])


#######################################################################################################################
#######################################################################################################################
