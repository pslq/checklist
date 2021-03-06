from ..utils.avg_list import avg_list
from ..utils.debug_post_msg import debug_post_msg
from ..utils.get_list_avg_and_diff import get_list_avg_and_diff
from ..utils.pq_round_number import pq_round_number

from .entstat import parser as entstat_parser
from .netstat import parser as netstat_parser
from ..Base_collector import Base_collector
import datetime


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

    self.entstat_check_groups = {
        'transmit_stats' : ( 'transmit_errors',
                             'receive_errors',
                             'transmit_packets_dropped',
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
        'veth_stats'    : ('send_errors', 'invalid_vlan_id_packets', 'receiver_failures',
                           'platform_large_send_packets_dropped')
    }

    self.entstat_group_messages = { 'veth_stats' : { 'send_errors' : 'Error sending packages to VIOS, If buffers are maxedout please check VIOS resources',
                                                     'receiver_failures' : 'Error possible starvation errors at the server, If buffers are maxedout please check CPU capabilities',
                                                     'platform_large_send_packets_dropped' : 'Error sending PLSO packages to VIOS, If buffers are maxedout and no backend error at physical adapters, please check VIOS resources' },
                                    'addon_stats' : { 'rx_pause_frames' : 'Possible saturation at switch side',
                                                      'tx_pause_frames' : 'Possible saturation at server side, Queues or CPU saturation is likely' },
                                    'dev_stats' : { 'number_of_xoff_packets_transmitted' : 'Possible saturation at server side, Queues or CPU saturation is likely',
                                                    'number_of_xoff_packets_received' : 'Possible saturation at server side, Queues or CPU saturation is likely',
                                                    'transmit_q_no_buffers' : 'Buffer Saturation, possible more TX queues are advisable',
                                                    'transmit_swq_dropped_packets' : 'Buffer Saturation, possible bigger queues are advisable',
                                                    'receive_q_no_buffers' : 'Buffer Saturation, possible more RX queues are advisable' },
                                    'general_stats' : { 'no_mbuf_errors' : 'Network stack lack of memory buffers, possible check of thewall is advisable'}
                                  }



    return(None)

#######################################################################################################################
  def load_from_db(self, db, days_to_fetch:int=1, append_dict:dict={}) -> dict :
    '''
    Returned data for each field:
      just_changes,avg_list(just_changes), change_rate
        [ difference between elements in list ], average_value, rate_in_which_elements changed, [ raw values within the database ]
    '''
    values_from_db = {}

    if db :
      now = datetime.datetime.utcnow()
      start_analysis = now - datetime.timedelta(days=days_to_fetch)
      extra_filters = [ '|> filter(fn: (r) => r["host"] == "%s")'%(self.bos_data.data['bos']['hostname']) ]
      for i in db.query("entstat", start_analysis.timestamp(), now.timestamp(), extra_filters=extra_filters) :
        if i['_field'] in self.entstat_check_groups[i['stats_type']] :
          try :
            values_from_db[i['interface']][i['stats_type']][i['_field']][3].append(i['_value'])
          except :
            val_to_add = [ [], 0, 0, [ i['_value'] ] ]
            try :
              values_from_db[i['interface']][i['stats_type']][i['_field']] = val_to_add
            except :
              try :
                values_from_db[i['interface']][i['stats_type']] = { i['_field'] : val_to_add }
              except :
                values_from_db[i['interface']] = { i['stats_type'] : { i['_field'] : val_to_add } }

    for dev, dev_data in values_from_db.items() :
      for stat_type,stats in dev_data.items() :
        for stat_name, stat_data in stats.items() :
          try :
            t_val = append_dict[dev][stat_type][stat_name]
            values_from_db[dev][stat_type][stat_name][3].append(tval)
          except :
            pass

    for dev, dev_data in values_from_db.items() :
      for stat_type,stats in dev_data.items() :
        for stat_name, stat_data in stats.items() :
          stat_data[0], stat_data[1], stat_data[2] = get_list_avg_and_diff(stat_data[3])

    if len(values_from_db) == 0 :
      for dev, dev_data in append_dict.items() :
        values_from_db[dev] = {}
        for stat_type,stats in dev_data.items() :
          values_from_db[dev][stat_type] = {}
          for stat_name, stat_data in stats.items() :
            values_from_db[dev][stat_type][stat_name] = [ [], 0, 0, [ stat_data ] ]
    return(values_from_db)

#######################################################################################################################
  def health_check(self,update_from_system:bool = True, db=None, debug:bool=False,\
                   stationary_treshold:float=0.5, days_to_fetch_back:int=45, just_check_groups:bool=True, change_tolerance:float=0.1) -> list :
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    messages = []

    # Load stats from memory or system
    if update_from_system :
      self.update_from_system()

    # Load data from memory and influxdb
    entstat = self.providers['entstat']
    values_from_db = self.load_from_db(db, days_to_fetch=days_to_fetch_back, append_dict=entstat['stats'])

    # Do the actual checks
    for dev,dev_data in values_from_db.items() :
      for stat_type,stats in dev_data.items() :
        for stat_name, stat_data in stats.items() :
          msg_to_append = self.custom_monitor(stat_name, stat_data)
          if not msg_to_append :
            if stat_name in self.entstat_check_groups[stat_type] or not just_check_groups :
              if len(stat_data[3]) > 1 :
                if stat_data[3][-1] != stat_data[3][-2] :
                  base_message = 'The %s at %s session on interface %s incremented from %d to %d'%(
                      stat_name,stat_type,dev,stat_data[3][-2],stat_data[3][-1])
                  if stat_data[2] < stationary_treshold :
                    msg_to_append = '%s and this is not commom'%base_message
                  elif abs(stat_data[1]/stat_data[0][-1]) > change_tolerance :
                    msg_to_append = '%s which is above usual increment rate of %f'%( base_message,float(stat_data[1]))
          if msg_to_append :
            messages.append(msg_to_append)


      if 'lacp_port_stats' in entstat['stats'][dev] :
        if not ( entstat['stats'][dev]['lacp_port_stats']['partner_state']['synchronization']  == \
                 entstat['stats'][dev]['lacp_port_stats']['actor_state']['synchronization'] == 'IN_SYNC' ) :
          messages.append('LACP Error ( possible switch port mismatch ) at interface %s'%dev)

    return(messages)
