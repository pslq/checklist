from . import debug_post_msg, get_list_avg_and_diff
from .entstat import parser as entstat_parser
from .netstat import parser as netstat_parser
from .Base_collector import Base_collector
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
        'transmit_stats' : ( 'transmit_errors', 'receive_errors', 'transmit_packets_dropped',
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


    return(None)

#######################################################################################################################
  def load_from_db(self, db, days_to_fetch:int=1) -> dict :
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
        if i['_field'] in entstat_check_groups[i['stats_type']] :
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
            stat_data[0], stat_data[1], stat_data[2] = get_list_avg_and_diff(stat_data[3])
    return(values_from_db)

#######################################################################################################################
  def health_check_data_from_db(self,db, days_to_fetch:int=45, stationary_treshold:float=0.5, \
                                just_check_groups:bool=True, change_tolerance:float=0.1) -> list :
    messages = []
    for dev,dev_data in self.load_from_db(db, days_to_fetch=days_to_fetch).items() :
      for stat_type,stats in dev_data.items() :
        for stat_name, stat_data in stats.items() :
          if stat_name in self.entstat_check_groups[stat_type] or not just_check_groups :
            if len(stat_data[3]) > 1 :
              if stat_data[3][-1] != stat_data[3][-2] :
                base_message = 'The %s at %s session on interface %s incremented from %d to %d'%(
                    stat_name,stat_type,dev,stat_data[3][-2],stat_data[3][-1])
                if stat_data[2] < stationary_treshold :
                  messages.append('%s and this is not commom'%base_message)
                elif abs(stat_data[1]/stat_data[0][-1]) > change_tolerance :
                  messages.append('%s which is above usual increment rate of %f'%( base_message,float(stat_data[1])))
    return(messages)

#######################################################################################################################
  def health_check(self,update_from_system:bool = True, db=None, debug:bool=False,\
                   stationary_treshold:float=0.5, just_check_groups:bool=True, change_tolerance:float=0.1) -> list :
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
    values_from_db = self.load_from_db(db)

    # Validate counters
    for dev in entstat['stats'].keys() :
      for check_group, checks in self.entstat_check_groups.items() :
        try :
          for stat in checks :
            try :
              if entstat['stats'][dev]['transmit_stats'][stat] > 0 :
                try :
                  if values_from_db[dev][check_group][stat][3][-1] != entstat['stats'][dev]['transmit_stats'][stat][-1] :
                    base_message = 'The %s at %s session on interface $s changed from %d to %d'%(
                        stat,check_group,dev, values_from_db[dev][check_group][stat][3][-1],
                        entstat['stats'][dev]['transmit_stats'][stat])
                    if values_from_db[dev][check_group][stat][2] < stationary_treshold :
                      messages.append('%s and is stationary on %f of the time'%(base_message,values_from_db[dev][check_group][stat][2]))
                    elif abs(values_from_db[dev][check_group][stat][1]/entstat['stats'][dev]['transmit_stats'][stat][-1]) > change_tolerance :
                      messages.append('%s and is above treshold of %f'%(base_message,values_from_db[dev][check_group][stat][1]))
                    elif debug :
                      messages.append('The %s counter at %s is at %d on interface $s'%(stat,check_group, entstat['stats'][dev]['transmit_stats'][stat],dev))
                except :
                  messages.append('The %s counter at %s is at %d on interface $s and no check to the database were possible'%(stat,check_group, entstat['stats'][dev]['transmit_stats'][stat],dev))
            except Exception as e :
              if debug :
                debug_post_msg(self.logger, "%s : Error parsing %s : %s"%(__file__, stat,e))
              pass
        except Exception as e :
          if debug :
            debug_post_msg(self.logger, "%s : Error parsing %s : %s"%(__file__, stat,e))
          pass
      # LACP stats have non numerical checks
      if 'lacp_port_stats' in entstat['stats'][dev] :
        if not ( entstat['stats'][dev]['lacp_port_stats']['partner_state']['synchronization']  == \
                 entstat['stats'][dev]['lacp_port_stats']['actor_state']['synchronization'] == 'IN_SYNC' ) :
          messages.append('LACP Error at interface %s'%dev)

    return(messages)
