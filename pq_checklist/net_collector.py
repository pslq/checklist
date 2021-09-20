from . import debug_post_msg, get_command_output, avg_list
from .bos_info import bos as bos_info
from .entstat import parser as entstat_parser
from .netstat import parser as netstat_parser
from .bos_info import bos as bos_parser

import concurrent.futures
from datetime import datetime
from time import time

class collector :
  def __init__(self, config = None, logger = None ) :
    '''
    General cpu data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    self.config        = config
    self.logger        = logger
    self.cwd           = '/tmp'
    self.bos           = bos_info()
    self.to_collectors = dict(logger = self.logger, cwd=self.cwd, bos_info=self.bos)
    self.entstat       = entstat_parser(**self.to_collectors)
    self.netstat       = netstat_parser(**self.to_collectors)

    # objects that provide measurements
    self.measurement_providers = [ self.entstat, self.netstat ]

    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)

  def update_data(self) :
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
      for i in self.measurement_providers :
        executor.submit(i.collect)
    return(None)

#######################################################################################################################
  def health_check(self) :
    '''
    Send health messages into server's syslog for diag purposes
    '''
    # update stored stats
    self.update_data()
    messages = []

    entstat_check_groups = { 'transmit_stats' : ( 'transmit_errors', 'receive_errors', 'transmit_packets_dropped',
                                                  'receive_packets_dropped', 'bad_packets', 's_w_transmit_queue_overflow',
                                                  'no_carrier_sense', 'crc_errors', 'dma_underrun', 'dma_overrun',
                                                  'lost_cts_errors', 'alignment_errors', 'max_collision_errors',
                                                  'no_resource_errors', 'late_collision_errors', 'receive_collision_errors',
                                                  'packet_too_short_errors', 'packet_too_long_errors', 'timeout_errors',
                                                  'packets_discarded_by_adapter', 'single_collision_count', 'multiple_collision_count'),
                             'general_stats' : ( 'no_mbuf_errors' ),
                             'dev_stats'     : ( 'number_of_xoff_packets_transmitted', 'number_of_xon_packets_transmitted',
                                                 'number_of_xoff_packets_received', 'number_of_xon_packets_received',
                                                 'transmit_q_no_buffers', 'transmit_q_dropped_packets', 'transmit_swq_dropped_packets',
                                                 'receive_q_no_buffers', 'receive_q_errors', 'receive_q_dropped_packets' ),
                             'addon_stats'   : ( 'rx_error_bytes', 'rx_crc_errors', 'rx_align_errors', 'rx_discards',
                                                 'rx_mf_tag_discard', 'rx_brb_discard', 'rx_pause_frames',
                                                 'rx_phy_ip_err_discards', 'rx_csum_offload_errors', 'tx_error_bytes',
                                                 'tx_mac_errors', 'tx_carrier_errors', 'tx_single_collisions', 'tx_deferred',
                                                 'tx_excess_collisions', 'tx_late_collisions', 'tx_total_collisions',
                                                 'tx_pause_frames', 'unrecoverable_errors' ),
                             'veth_stats'    : ('send_errors', 'invalid_vlan_id_packets', 'receiver_failures', 'platform_large_send_packets_dropped')
                             }

    # check entstat data
    for dev in self.entstat['stats'].keys() :
      for check_group, checks in entstat_check_groups.items() :
        try :
          for stat in checks :
            try :
              if self.entstat['stats'][dev]['transmit_stats'][stat] > 0 :
                messages.append('The %s counter at %s is at %d on interface $s'%(stat,check_group, self.entstat['stats'][dev]['transmit_stats'][stat],dev))
            except :
              pass
        except :
          pass
      # LACP stats have non numerical checks
      if 'lacp_port_stats' in self.entstat['stats'][dev] :
        if not ( self.entstat['stats'][dev]['lacp_port_stats']['partner_state']['synchronization']  == \
            coll.entstat['stats'][dev]['lacp_port_stats']['actor_state']['synchronization'] == 'IN_SYNC' ) :
          messages.append('LACP Error at interface %s'%dev)


    for msg in messages :
      debug_post_msg(self.logger,msg)


    return(None)


#######################################################################################################################
  def get_latest_measurements(self, debug=False) :
    '''
    Get in influxdb format latest cpu utilization measurements from the lpar

    Parameters:
      debug : bool -> [True,False] Log into syslog amount of time that took to get the measurements

    Returns:
      list of measurements
    '''
    from time import time
    ret = []
    st = time()
    self.update_data()
    for measurement_provider in self.measurement_providers :
      ret += measurement_provider.get_latest_measurements()
    if debug :
      duration = time() - st
      debug_post_msg(self.logger,'NET Collect Task Duration: %d seconds'%int(duration))

    return(ret)
