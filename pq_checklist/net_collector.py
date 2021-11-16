from . import debug_post_msg
from .entstat import parser as entstat_parser
from .netstat import parser as netstat_parser
from .Base_collector import Base_collector

class collector(Base_collector) :
  def __init__(self, config = None, logger = None, bos_data = None ) :
    '''
    General net data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    super().__init__( config = config, logger = logger, bos_data = bos_data)

    self.providers = { 'entstat' : entstat_parser(**self.general_parameters),
                       'netstat' : netstat_parser(**self.general_parameters) }


    self.file_sources = {
        'entstat'     : self.providers['entstat'].parse_entstat_d,
        'netstat_s'   : self.providers['netstat'].parse_netstat_s
        }

    return(None)

#######################################################################################################################
  def health_check(self,update_from_system:bool = True) -> list :
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    # update stored stats
    if update_from_system :
      self.update_from_system()

    messages = []
    entstat = self.providers['entstat']

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
    for dev in entstat['stats'].keys() :
      for check_group, checks in entstat_check_groups.items() :
        try :
          for stat in checks :
            try :
              if entstat['stats'][dev]['transmit_stats'][stat] > 0 :
                messages.append('The %s counter at %s is at %d on interface $s'%(stat,check_group, entstat['stats'][dev]['transmit_stats'][stat],dev))
            except :
              pass
        except :
          pass
      # LACP stats have non numerical checks
      if 'lacp_port_stats' in entstat['stats'][dev] :
        if not ( entstat['stats'][dev]['lacp_port_stats']['partner_state']['synchronization']  == \
                 entstat['stats'][dev]['lacp_port_stats']['actor_state']['synchronization'] == 'IN_SYNC' ) :
          messages.append('LACP Error at interface %s'%dev)


    return(messages)
