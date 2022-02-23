#!/opt/freeware/bin/python3

'''
Test routines to validate that main components are working
'''
import pytest

from pq_checklist.cpu_collector.mpstat import parser as mpstat_parser
from pq_checklist.cpu_collector.lparstat import parser as lparstat_parser
from pq_checklist.net_collector.netstat import parser as netstat_parser
from pq_checklist.net_collector.entstat import parser as entstat_parser
from pq_checklist.ioscli import parser as ioscli_parser
from pq_checklist.bos_info import bos as bos_data
from pq_checklist.mem_collector.vmstat import parser as vmstat_parser
from pq_checklist.utils.merge_dict import merge_dict

class TestClass:
  def test_merge_dict_append_strings(self) :
    x = { 'a': 1, 'b' : [ 1,2,3 ], 'c' : 'aaa' }
    y = { 'a': 1, 'b' : [ 1,2,3 ], 'c' : 'aaa' }
    ret = {'a': [1, 1], 'b': [1, 2, 3, 1, 2, 3], 'c': 'aaaaaa'}
    assert ret ==  merge_dict(x,y, append_strings=True)

  def test_merge_dict(self) :
    x = { 'a': 1, 'b' : [ 1,2,3 ], 'c' : 'aaa' }
    y = { 'a': 1, 'b' : [ 1,2,3 ], 'c' : 'aaa' }
    ret = {'a': [1, 1], 'b': [1, 2, 3, 1, 2, 3], 'c': ['aaa', 'aaa']}
    assert ret ==  merge_dict(x,y, append_strings=False)

  def test_parse_ioo(self) :
    parser = bos_data()
    expected_ret = {'aio_active': 0, 'aio_maxreqs': 131072, 'aio_maxservers': 30, 'aio_minservers': 3,
                    'aio_server_inactivity': 300, 'dk_closed_path_recovery': 0, 'dk_lbp_buf_size': 512,
                    'dk_lbp_enabled': 1, 'dk_lbp_num_bufs': 64, 'j2_atimeUpdateSymlink': 0,
                    'j2_dynamicBufferPreallocation': 16, 'j2_inodeCacheSize': 200, 'j2_maxPageReadAhead': 128,
                    'j2_maxRandomWrite': 0, 'j2_metadataCacheSize': 200, 'j2_minPageReadAhead': 2,
                    'j2_nPagesPerRBNACluster': 32, 'j2_nPagesPerWriteBehindCluster': 32, 'j2_nRandomCluster': 0,
                    'j2_recoveryMode': 1, 'j2_syncByVFS': 0, 'j2_syncConcurrency': 4, 'j2_syncDelayReport': 600,
                    'j2_syncPageCount': 0, 'j2_syncPageLimit': 16, 'lvm_bufcnt': 9, 'maxpgahead': 8, 'maxrandwrt': 0,
                    'numclust': 1, 'numfsbufs': 196, 'pd_npages': 4096, 'posix_aio_active': 0, 'posix_aio_maxreqs': 131072,
                    'posix_aio_maxservers': 30, 'posix_aio_minservers': 3, 'posix_aio_server_inactivity': 300, 'spec_accessupdate': 2,
                    'aio_affinity': 7, 'aio_fastpath': 1, 'aio_fsfastpath': 1, 'aio_kprocprio': 39, 'aio_multitidsusp': 1,
                    'aio_sample_rate': 5, 'aio_samples_per_cycle': 6, 'iodone_distr_all_bufs': 0, 'iodone_distr_disable': 0,
                    'iodone_distr_sib_check': 1, 'iodone_distr_trace_iodone': 0, 'j2_maxPageLocks': 64, 'j2_maxUsableMaxTransfer': 512,
                    'j2_nBufferPerPagerDevice': 512, 'j2_nonFatalCrashesSystem': 0, 'j2_syncMappedLimit': 0,
                    'j2_syncModifiedMapped': 1, 'j2_syncdLogSyncInterval': 1, 'j2_unmarkComp': 0, 'j2_zombieGC_enabled': 1,
                    'jfs_clread_enabled': 0, 'jfs_use_read_lock': 1, 'memory_frames': 4194304, 'minpgahead': 2,
                    'pcibus_dma_memory_protect': 1, 'pcibus_eeh_perm_timeout': 300, 'pcibus_max_dma_window': 512,
                    'pgahd_scale_thresh': 0, 'posix_aio_affinity': 7, 'posix_aio_fastpath': 1, 'posix_aio_fsfastpath': 1,
                    'posix_aio_kprocprio': 39, 'posix_aio_sample_rate': 5, 'posix_aio_samples_per_cycle': 6,
                    'pv_min_pbuf': 512, 'sync_release_ilock': 0}
    assert parser.load_from_file('tests/test_data/ioo_aF', parse_function=parser.parse_ioo) == expected_ret


  def test_parse_vmstat_linux(self) :
    parser = vmstat_parser(bos_data = bos_data())
    ret = parser.load_from_file('tests/test_data/vmstat_sSB', parse_function=parser.parse_vmstat_s)
    expected_ret = {'b_total_memory': 50295533568.0, 'b_used_memory': 8225038336.0, 'b_active_memory': 10827042816.0,
                    'b_inactive_memory': 35691974656.0, 'b_free_memory': 1932533760.0, 'b_buffer_memory': 1778040832.0,
                    'b_swap_cache': 38359920640.0, 'b_total_swap': 1023406080.0, 'b_used_swap': 964182016.0,
                    'b_free_swap': 59224064.0, 'non-nice_user_cpu_ticks': 194932976.0, 'nice_user_cpu_ticks': 423850.0,
                    'system_cpu_ticks': 54865747.0, 'idle_cpu_ticks': 557921475.0, 'io-wait_cpu_ticks': 541766.0,
                    'irq_cpu_ticks': 0.0, 'softirq_cpu_ticks': 21830334.0, 'stolen_cpu_ticks': 0.0,
                    'pages_paged_in': 15426866472.0, 'pages_paged_out': 738683673.0, 'pages_swapped_in': 390236.0,
                    'pages_swapped_out': 1124052.0, 'interrupts': 1582425031.0, 'cpu_context_switches': 4187179471.0,
                    'boot_time': 1640489302.0, 'forks': 12822370.0}
    assert ret == expected_ret

  def test_parse_vmstat_aix(self) :
    parser = vmstat_parser(bos_data = bos_data())
    ret = parser.load_from_file('tests/test_data/vmstat_sv', parse_function=parser.parse_vmstat_s)
    expected_ret = { 'total_address_trans_faults': 3352336647.0, 'page_ins': 139878.0, 'page_outs': 17594103.0,
                     'paging_space_page_ins': 0.0, 'paging_space_page_outs': 0.0, 'total_reclaims': 0.0,
                     'zero_filled_pages_faults': 1131950778.0, 'executable_filled_pages_faults': 7046.0,
                     'pages_examined_by_clock': 0.0, 'revolutions_of_the_clock_hand': 0.0,
                     'pages_freed_by_the_clock': 0.0, 'backtracks': 33281569.0, 'free_frame_waits': 0.0,
                     'extend_xpt_waits': 0.0, 'pending_io_waits': 30009.0, 'start_ios': 17733981.0,
                     'iodones': 4210944.0, 'cpu_context_switches': 10142679014.0, 'device_interrupts': 2319873329.0,
                     'software_interrupts': 3118662390.0, 'decrementer_interrupts': 3320348089.0,
                     'mpc-sent_interrupts': 1103.0, 'mpc-receive_interrupts': 1111.0, 'phantom_interrupts': 624.0,
                     'traps': 0.0, 'syscalls': 6656428359.0, 'memory_pages': 4194304.0, 'lruable_pages': 3984032.0,
                     'free_pages': 2510739.0, 'memory_pools': 1.0, 'pinned_pages': 1502261.0,
                     'maxpin_percentage': 900.0, 'minperm_percentage': 30.0, 'maxperm_percentage': 900.0,
                     'numperm_percentage': 31.0, 'file_pages': 125079.0, 'compressed_percentage': 0.0,
                     'compressed_pages': 0.0, 'numclient_percentage': 31.0, 'maxclient_percentage': 900.0,
                     'client_pages': 125079.0, 'remote_pageouts_scheduled': 0.0,
                     'pending_disk_ios_blocked_with_no_pbuf': 0.0, 'paging_space_ios_blocked_with_no_psbuf': 0.0,
                     'filesystem_ios_blocked_with_no_fsbuf': 1972.0, 'client_filesystem_ios_blocked_with_no_fsbuf': 385.0,
                     'external_pager_filesystem_ios_blocked_with_no_fsbuf': 0.0,
                     'percentage_of_memory_used_for_computational_pages': 372.0}

    assert ret == expected_ret


  def test_parse_seastat_d(self):
    parser = ioscli_parser()
    expected_ret = {'ent63': {'vlan': {706: {'tx': {'pkg': 163435, 'bytes': 116046901},
                                             'rx': {'pkg': 110381, 'bytes': 39672311}}},
                              'mac': {'5a:0e:e6:d2:e2:c2': {'tx': {'pkg': 20, 'bytes': 2905},
                                                            'rx': {'pkg': 23, 'bytes': 3099},
                                                            'ipaddr': '10.29.12.13',
                                                            'hostname': 'frodo-g.dominio.com',
                                                            'vlan': 706, 'vlan_prio': 0},
                                      'b6:19:22:cc:7f:0c': {'tx': {'pkg': 163415, 'bytes': 116043996},
                                                            'rx': {'pkg': 110358, 'bytes': 39669212},
                                                            'ipaddr': '10.29.12.7',
                                                            'hostname': 'cuiaba-sapo.dominio.com',
                                                            'vlan': 706, 'vlan_prio': 0}}}}
    assert parser.load_from_file('tests/test_data/seastat_d_ent63', parse_function=parser.parse_seastat_d) == expected_ret


  def test_parse_vnicstat_d(self) :
    parser = ioscli_parser()
    expected_ret = {'vnicserver1': {'crq':
                                     {'main': {'tx': {'state': 'open', 'commands_received': 5944454,
                                                      'commands_sent': 5944653, 'interrupts': 5944461,
                                                      'command_response_errors': 191, 'link_state_indications': 4,
                                                      'acl_change_indications': 0, 'login_requests': 4, 'reboots': 3,
                                                      'client_descriptors': 8824135891, 'vf_descriptors': 8686674162,
                                                      'max_vf_descriptors_queued': 4092, 'client_completions': 135729282,
                                                      'vf_completions': 135729282, 'client_completions_error': 0, 'vf_completions_error': 0,
                                                      'tce_passed_to_vf': 8686674162, 'tce_mappings': 0,
                                                      'tce_unmappings': 0, 'descriptors_pool_full': 0, 'nb_sub-crq': 4, 'queue_size': 1023},
                                               'rx': {'error_indications': 191, 'adapter_problem': 0, 'firmware_problem': 0,
                                                      'device_driver_problem': 191, 'eeh_recovery': 0, 'firmware_updated': 0,
                                                      'low_memory': 0, 'client_descriptors': 139036407211,
                                                      'vf_descriptors': 139036407211, 'client_completions': 139036403115,
                                                      'vf_completions': 139036403115, 'client_completions_error': 0,
                                                      'vf_completions_error': 0, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                      'descriptors_pool_empty': 43001, 'nb_sub-crq': 4, 'queue_size': 2048,
                                                      'buffer_size': 9146}
                                               },
                                      '1': {'tx': {'current_queue_length': 2, 'client_descriptors': 2279569749,
                                                   'vf_descriptors': 2256133250, 'max_vf_descriptors_queued': 1023,
                                                   'client_completions': 35252082, 'vf_completions': 35252082,
                                                   'client_completions_error': 0, 'vf_completions_error': 0,
                                                   'tce_passed_to_vf': 2256133250, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_full': 0},
                                            'rx': {'current_queue_length': 1024, 'client_descriptors': 289774030,
                                                   'vf_descriptors': 289774030, 'client_completions': 289773006,
                                                   'vf_completions': 289773006, 'client_completions_error': 0,
                                                   'vf_completions_error': 0, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_empty': 0}},
                                      '2': {'tx': {'current_queue_length': 41, 'client_descriptors': 2514986132,
                                                   'vf_descriptors': 2437188009, 'max_vf_descriptors_queued': 1023,
                                                   'client_completions': 38081062, 'vf_completions': 38081062,
                                                   'client_completions_error': 0, 'vf_completions_error': 0,
                                                   'tce_passed_to_vf': 2437188009, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_full': 0},
                                            'rx': {'current_queue_length': 1024, 'client_descriptors': 64911548311,
                                                   'vf_descriptors': 64911548311, 'client_completions': 64911547287,
                                                   'vf_completions': 64911547287, 'client_completions_error': 0,
                                                   'vf_completions_error': 0, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_empty': 42381}},
                                      '3': {'tx': {'current_queue_length': 43, 'client_descriptors': 2090385606,
                                                   'vf_descriptors': 2071266795, 'max_vf_descriptors_queued': 1023,
                                                   'client_completions': 32363543, 'vf_completions': 32363543,
                                                   'client_completions_error': 0, 'vf_completions_error': 0,
                                                   'tce_passed_to_vf': 2071266795, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_full': 0},
                                            'rx': {'current_queue_length': 1024, 'client_descriptors': 34858603713,
                                                   'vf_descriptors': 34858603713, 'client_completions': 34858602689,
                                                   'vf_completions': 34858602689, 'client_completions_error': 0,
                                                   'vf_completions_error': 0, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_empty': 236}},
                                      '4': {'tx': {'current_queue_length': 28, 'client_descriptors': 1939194404,
                                                   'vf_descriptors': 1922086108, 'max_vf_descriptors_queued': 1023,
                                                   'client_completions': 30032595, 'vf_completions': 30032595,
                                                   'client_completions_error': 0, 'vf_completions_error': 0,
                                                   'tce_passed_to_vf': 1922086108, 'tce_mappings': 0,
                                                   'tce_unmappings': 0, 'descriptors_pool_full': 0},
                                            'rx': {'current_queue_length': 1024, 'client_descriptors': 38976481157,
                                                   'vf_descriptors': 38976481157, 'client_completions': 38976480133,
                                                   'vf_completions': 38976480133, 'client_completions_error': 0,
                                                   'vf_completions_error': 0, 'tce_mappings': 0, 'tce_unmappings': 0,
                                                   'descriptors_pool_empty': 384}}
                                    }, 'state': 'active', 'backing_device_name': 'ent34', 'failover_state': 'active',
                                       'failover_readiness': 'operational', 'failover_priority': 50, 'client_partition_id': 32,
                                       'client_partition_name': 'ppa1tsm00010', 'client_operating_system': 'aix',
                                       'client_device_name': 'ent1', 'client_device_location_code': 'u9080.m9s.8205c8t-v32-c2'}}
    assert parser.load_from_file('tests/test_data/vnicstat_d', parse_function=parser.parse_vnicstat_d) == expected_ret

  def test_entstat_veth(self) :
    parser = entstat_parser()
    expected_ret = {'en18': {'transmit_stats': {'transmit_packets': 62580431, 'receive_packets': 81684846, 'transmit_bytes': 85978411810, 'receive_bytes': 225230719246, 'transmit_interrupts': 0, 'receive_interrupts': 71373617, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 0, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0, 'transmit_broadcast_packets': 255, 'receive_broadcast_packets': 265, 'transmit_multicast_packets': 2545, 'receive_multicast_packets': 2581, 'no_carrier_sense': 0, 'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0}, 'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 0, 'adapter_data_rate': 20000}, 'veth_stats': {'rq_length': 10689, 'filters': 255, 'hypervisor_send_failures': 0, 'receiver_failures': 0, 'send_errors': 0, 'hypervisor_receive_failures': 0, 'invalid_vlan_id_packets': 0, 'port_vlan_id': 10, 'platform_large_send_packets_transmitted': 0, 'total_large_send_packets_transmitted': 0, 'platform_large_send_packets_dropped': 0}}}
    assert parser.load_from_file('tests/test_data/entstat_veth', parse_function=parser.parse_entstat_d) == expected_ret


  def test_entstat_etherchannel(self) :
    parser = entstat_parser()
    expected_ret = {'en4': {'transmit_stats': {'transmit_packets': 1743505, 'receive_packets': 11042941, 'transmit_bytes': 197535808, 'receive_bytes': 802353777, 'transmit_interrupts': 1659977, 'receive_interrupts': 9377269, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 6, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0, 'transmit_broadcast_packets': 217, 'receive_broadcast_packets': 9484363, 'transmit_multicast_packets': 18663, 'receive_multicast_packets': 95215, 'no_carrier_sense': 0, 'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0}, 'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 0, 'adapter_data_rate': 2000}, 'general_lacp': {'number_of_primary_adapters': 2, 'number_of_backup_adapters': 0, 'longreceived': 18551, 'transmitted_lacpdus': 18548, 'received_marker_pdus': 0, 'transmitted_marker_pdus': 0, 'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0, 'received_illegal_pdus': 0}}, 'ent2': {'transmit_stats': {'transmit_packets': 832572, 'receive_packets': 5565555, 'transmit_bytes': 78310552, 'receive_bytes': 417092344, 'transmit_interrupts': 799252, 'receive_interrupts': 3979897, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 3, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0, 'transmit_broadcast_packets': 0, 'receive_broadcast_packets': 4829138, 'transmit_multicast_packets': 9276, 'receive_multicast_packets': 35921, 'no_carrier_sense': 0, 'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0}, 'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 1, 'adapter_data_rate': 2000}, 'dev_stats': {'version': 1, 'tlp_size': 512, 'mrr_size': 4096, 'assigned_interrupt_source_numbers': 5, 'unassigned_interrupt_source_numbers': 27, 'multicast_addresses_enabled': 3, 'maximum_exact_match_multicast_filters': 0, 'maximum_inexact_match_multicast_filters': 256, 'physical_port_mtu': 1514, 'logical_port_mtu': 1514, 'maximum_dma_page_size': 4096, 'number_of_xoff_packets_transmitted': 0, 'number_of_xon_packets_transmitted': 0, 'number_of_xoff_packets_received': 0, 'number_of_xon_packets_received': 0, 'receive_tcp_segment_aggregation_large_packets_created': 1024, 'receive_tcp_packets_aggregated_into_large_packets': 1513, 'receive_tcp_payload_bytes_aggregated_into_large_packets': 2109032, 'receive_tcp_segment_aggregation_average_packets_aggregated': 1, 'receive_tcp_segment_aggregation_maximum_packets_aggregated': 3, 'transmit_tcp_segmentation_offload_packets_transmitted': 279, 'transmit_tcp_segmentation_offload_maximum_packet_size': 59950, 'transmit_padded_packets': 0, 'transmit_q_packets': 832575, 'transmit_q_multicast_packets': 9276, 'transmit_q_broadcast_packets': 0, 'transmit_q_flip_and_run_packets': 383872, 'transmit_q_bytes': 78311310, 'transmit_q_no_buffers': 0, 'transmit_q_dropped_packets': 0, 'transmit_swq_cur_packets': 0, 'transmit_swq_max_packets': 3, 'transmit_swq_dropped_packets': 0, 'transmit_ofq_cur_packets': 0, 'transmit_ofq_max_packets': 0, 'receive_q_packets': 197960, 'receive_q_multicast_packets': 8104, 'receive_q_broadcast_packets': 26813, 'receive_q_bytes': 21933062, 'receive_q_no_buffers': 0, 'receive_q_errors': 0, 'receive_q_dropped_packets': 0}, 'addon_stats': {'rx_bytes': 439349280, 'rx_error_bytes': 0, 'rx_ucast_packets': 700496, 'rx_mcast_packets': 35921, 'rx_bcast_packets': 4829063, 'rx_crc_errors': 0, 'rx_align_errors': 0, 'rx_undersize_packets': 0, 'rx_oversize_packets': 0, 'rx_fragments': 0, 'rx_jabbers': 0, 'rx_discards': 0, 'rx_filtered_packets': 1319190, 'rx_mf_tag_discard': 0, 'pfc_frames_received': 0, 'pfc_frames_sent': 0, 'rx_brb_discard': 0, 'rx_brb_truncate': 0, 'rx_pause_frames': 0, 'rx_mac_ctrl_frames': 0, 'rx_constant_pause_events': 0, 'rx_phy_ip_err_discards': 0, 'rx_csum_offload_errors': 0, 'tx_bytes': 81730588, 'tx_error_bytes': 0, 'tx_ucast_packets': 824729, 'tx_mcast_packets': 9276, 'tx_bcast_packets': 0, 'tx_mac_errors': 0, 'tx_carrier_errors': 0, 'tx_single_collisions': 0, 'tx_multi_collisions': 0, 'tx_deferred': 0, 'tx_excess_collisions': 0, 'tx_late_collisions': 0, 'tx_total_collisions': 0, 'tx_64_byte_packets': 10203, 'tx_65_to_127_byte_packets': 766278, 'tx_128_to_255_byte_packets': 36714, 'tx_256_to_511_byte_packets': 12741, 'tx_512_to_1023_byte_packets': 4926, 'tx_1024_to_1522_byte_packets': 3142, 'tx_1523_to_9022_byte_packets': 0, 'tx_pause_frames': 0, 'recoverable_errors': 0, 'unrecoverable_errors': 0, 'tx_lpi_entry_count': 0}, 'lacp_port_stats': {'actor_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False'}, 'partner_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False', 'received_lacpdus': 9276, 'transmitted_lacpdus': 9274, 'received_marker_pdus': 0, 'transmitted_marker_pdus': 0, 'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0, 'received_illegal_pdus': 0}}}, 'ent3': {'lacp_port_stats': {'partner_state': {'device_type': 'PCIe2 4-Port Adapter (1GbE RJ45) (e4148a1614109404)', 'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False', 'received_lacpdus': 9275, 'transmitted_lacpdus': 9274, 'received_marker_pdus': 0, 'transmitted_marker_pdus': 0, 'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0, 'received_illegal_pdus': 0}, 'actor_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False'}}, 'transmit_stats': {'transmit_packets': 910936, 'receive_packets': 5477386, 'transmit_bytes': 119226222, 'receive_bytes': 385261433, 'transmit_interrupts': 860728, 'receive_interrupts': 5397372, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 3, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0, 'transmit_broadcast_packets': 217, 'receive_broadcast_packets': 4655225, 'transmit_multicast_packets': 9387, 'receive_multicast_packets': 59294, 'no_carrier_sense': 0, 'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0}, 'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 1, 'adapter_data_rate': 2000}, 'dev_stats': {'version': 1, 'tlp_size': 512, 'mrr_size': 4096, 'assigned_interrupt_source_numbers': 5, 'unassigned_interrupt_source_numbers': 27, 'multicast_addresses_enabled': 3, 'maximum_exact_match_multicast_filters': 0, 'maximum_inexact_match_multicast_filters': 256, 'physical_port_mtu': 1514, 'logical_port_mtu': 1514, 'maximum_dma_page_size': 4096, 'number_of_xoff_packets_transmitted': 0, 'number_of_xon_packets_transmitted': 0, 'number_of_xoff_packets_received': 0, 'number_of_xon_packets_received': 0, 'receive_tcp_segment_aggregation_large_packets_created': 28011, 'receive_tcp_packets_aggregated_into_large_packets': 28705, 'receive_tcp_payload_bytes_aggregated_into_large_packets': 39506685, 'receive_tcp_segment_aggregation_average_packets_aggregated': 1, 'receive_tcp_segment_aggregation_maximum_packets_aggregated': 3, 'transmit_tcp_segmentation_offload_packets_transmitted': 6249, 'transmit_tcp_segmentation_offload_maximum_packet_size': 56538, 'transmit_padded_packets': 0, 'transmit_q_packets': 910936, 'transmit_q_multicast_packets': 9387, 'transmit_q_broadcast_packets': 217, 'transmit_q_flip_and_run_packets': 355346, 'transmit_q_bytes': 119226222, 'transmit_q_no_buffers': 0, 'transmit_q_dropped_packets': 0, 'transmit_swq_cur_packets': 0, 'transmit_swq_max_packets': 3, 'transmit_swq_dropped_packets': 0, 'transmit_ofq_cur_packets': 0, 'transmit_ofq_max_packets': 0, 'receive_q_packets': 219490, 'receive_q_multicast_packets': 7031, 'receive_q_broadcast_packets': 48388, 'receive_q_bytes': 26029655, 'receive_q_no_buffers': 0, 'receive_q_errors': 0, 'receive_q_dropped_packets': 0}, 'addon_stats': {'rx_bytes': 407162874, 'rx_error_bytes': 0, 'rx_ucast_packets': 762828, 'rx_mcast_packets': 59294, 'rx_bcast_packets': 4655211, 'rx_crc_errors': 0, 'rx_align_errors': 0, 'rx_undersize_packets': 0, 'rx_oversize_packets': 0, 'rx_fragments': 0, 'rx_jabbers': 0, 'rx_discards': 0, 'rx_filtered_packets': 1221689, 'rx_mf_tag_discard': 0, 'pfc_frames_received': 0, 'pfc_frames_sent': 0, 'rx_brb_discard': 0, 'rx_brb_truncate': 0, 'rx_pause_frames': 0, 'rx_mac_ctrl_frames': 0, 'rx_constant_pause_events': 0, 'rx_phy_ip_err_discards': 0, 'rx_csum_offload_errors': 0, 'tx_bytes': 124256253, 'tx_error_bytes': 0, 'tx_ucast_packets': 922697, 'tx_mcast_packets': 9387, 'tx_bcast_packets': 217, 'tx_mac_errors': 0, 'tx_carrier_errors': 0, 'tx_single_collisions': 0, 'tx_multi_collisions': 0, 'tx_deferred': 0, 'tx_excess_collisions': 0, 'tx_late_collisions': 0, 'tx_total_collisions': 0, 'tx_64_byte_packets': 11305, 'tx_65_to_127_byte_packets': 801552, 'tx_128_to_255_byte_packets': 75756, 'tx_256_to_511_byte_packets': 12367, 'tx_512_to_1023_byte_packets': 4963, 'tx_1024_to_1522_byte_packets': 26357, 'tx_1523_to_9022_byte_packets': 0, 'tx_pause_frames': 0, 'recoverable_errors': 0, 'unrecoverable_errors': 0, 'tx_lpi_entry_count': 0}}}

    assert parser.load_from_file('tests/test_data/entstat_etherchannel', parse_function=parser.parse_entstat_d) == expected_ret


  def test_bos_info_lsdev_class(self):
    parser = bos_data()
    expected_ret = {
      'L2cache0': {'class': 'memory', 'subclass': 'sys', 'type': 'L2cache_rspc'}, 'advmctl': {'class': 'driver', 'subclass': 'advm', 'type': 'advmctl'},
      'cluster0': {'class': 'pseudo', 'subclass': 'node', 'type': 'cluster'}, 'en4': {'class': 'if', 'subclass': 'EN', 'type': 'en'},
      'en18': {'class': 'if', 'subclass': 'EN', 'type': 'en'}, 'ent0': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'},
      'ent1': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'}, 'ent2': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'},
      'ent3': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'}, 'ent4': {'class': 'adapter', 'subclass': 'pseudo', 'type': 'ibm_ech'},
      'ent10': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'}, 'ent11': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'},
      'ent12': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'}, 'ent13': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'},
      'ent14': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'}, 'ent15': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169304'},
      'ent16': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'}, 'ent17': {'class': 'adapter', 'subclass': 'pciex', 'type': 'e4148a169404'},
      'ent18': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,l-lan'}, 'exa_dump_vol-113': {'class': 'driver', 'subclass': 'advm', 'type': 'advmvol'},
      'fcs0': {'class': 'adapter', 'subclass': 'pciex', 'type': 'df1000e21410f10'}, 'fcs1': {'class': 'adapter', 'subclass': 'pciex', 'type': 'df1000e21410f10'},
      'fcs2': {'class': 'adapter', 'subclass': 'pciex', 'type': 'df1000e21410f10'}, 'fcs3': {'class': 'adapter', 'subclass': 'pciex', 'type': 'df1000e21410f10'},
      'fscsi0': {'class': 'driver', 'subclass': 'emfc', 'type': 'emfscsi'}, 'fscsi1': {'class': 'driver', 'subclass': 'emfc', 'type': 'emfscsi'},
      'fscsi2': {'class': 'driver', 'subclass': 'emfc', 'type': 'emfscsi'}, 'fscsi3': {'class': 'driver', 'subclass': 'emfc', 'type': 'emfscsi'},
      'hdcrypt': {'class': 'adapter', 'subclass': 'pseudo', 'type': 'hdcrypt'}, 'hdisk0': {'class': 'disk', 'subclass': 'nvme', 'type': 'nvmdisk'},
      'hdisk1': {'class': 'disk', 'subclass': 'nvme', 'type': 'nvmdisk'}, 'hdisk2': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk3': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk4': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk5': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk6': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk7': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_0': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_1': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_2': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_3': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_4': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_5': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_6': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_7': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_8': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_9': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_asm_10': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_asm_11': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_ocr_0': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk_ocr_1': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk_ocr_2': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'inet0': {'class': 'tcpip', 'subclass': 'TCPIP', 'type': 'inet'}, 'iocp0': {'class': 'iocp', 'subclass': 'node', 'type': 'iocp'}, 'iscsi0': {'class': 'driver', 'subclass': 'node', 'type': 'iscsi'},
      'lo0': {'class': 'if', 'subclass': 'LO', 'type': 'lo'}, 'loop0': {'class': 'loopback', 'subclass': 'node', 'type': 'loopback'}, 'lvdd': {'class': 'lvm', 'subclass': 'lvm', 'type': 'lvdd'},
      'mem0': {'class': 'memory', 'subclass': 'sys', 'type': 'totmem'}, 'nvme0': {'class': 'adapter', 'subclass': 'pciex', 'type': 'nvme'}, 'nvme1': {'class': 'adapter', 'subclass': 'pciex', 'type': 'nvme'},
      'ofsctl': {'class': 'driver', 'subclass': 'acfs', 'type': 'acfsctl'}, 'pci0': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci1': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'},
      'pci2': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci3': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci4': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'},
      'pci5': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci9': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci11': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'},
      'pci12': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci14': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'}, 'pci15': {'class': 'bus', 'subclass': 'chrp', 'type': 'pciex'},
      'pkcs11': {'class': 'adapter', 'subclass': 'pseudo', 'type': 'ibm_pkcs11'}, 'proc0': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc8': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc16': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc24': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc32': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc40': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc48': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc56': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc64': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'pty0': {'class': 'pty', 'subclass': 'pty', 'type': 'pty'}, 'sfw0': {'class': 'driver', 'subclass': 'storfwork', 'type': 'module'},
      'sfwcomm0': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'}, 'sfwcomm1': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'}, 'sfwcomm2': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'},
      'sfwcomm3': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'}, 'sys0': {'class': 'sys', 'subclass': 'node', 'type': 'chrp'},
      'sysplanar0': {'class': 'planar', 'subclass': 'sys', 'type': 'sysplanar_rspc'}, 'usb0': {'class': 'usb', 'subclass': 'node', 'type': 'usb'}, 'usbhc0': {'class': 'adapter', 'subclass': 'pciex', 'type': '4c1041821410b20'},
      'vio0': {'class': 'bus', 'subclass': 'chrp', 'type': 'vdevice'}, 'vsa0': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'hvterm1'}, 'vty0': {'class': 'tty', 'subclass': 'vcon', 'type': 'tty'}}
    assert parser.load_from_file('tests/test_data/lsdev_class', parse_function=parser.parse_lsdev_class) == expected_ret

  def test_netstat_stats(self):
    coll_netstat = netstat_parser()
    expected_ret = {'icmp': {'calls_to_icmp_error': 1122655, 'errors_not_generated_because_old_message_was_icmp': 0,
                             'output_histogram': {'echo_reply': 9584, 'destination_unreachable': 1113605, 'echo': 506},
                             'messages_with_bad_code_fields': 0, 'messages_minimum_length': 0, 'bad_checksums': 0,
                             'messages_with_bad_length': 0,
                             'input_histogram': {'echo_reply': 490, 'destination_unreachable': 112, 'echo': 9590},
                             'message_responses_generated': 9584},
                    'igmp': {'messages_received': 48624, 'messages_received_with_too_few_bytes': 0,
                             'messages_received_with_bad_checksum': 0, 'membership_queries_received': 48624,
                             'membership_queries_received_with_invalid_fields': 0, 'membership_reports_received': 0,
                             'membership_reports_received_with_invalid_fields': 0,
                             'membership_reports_received_for_groups_to_which_we_belong': 0, 'membership_reports_sent': 10},
                    'tcp': {'packets_sent': {'count': 3751054047, 'data': {'count': 3654373215, 'bytes': 1539047027855},
                            'retransmitted': {'count': 407, 'bytes': 495274},
                            'ack_only': {'count': 30286332, 'delayed': 6191028}, 'urg_only_packets': 0,
                            'window_probe_packets': 0, 'window_update_packets': 47533710, 'control_packets': 18860395,
                            'large_sends': 6937177, 'bytes_sent_using_largesend': 197466219261,
                            'bytes_is_the_biggest_largesend': 65160},
                            'packets_received': {'count': 3810732476, 'acks': {'count': 3676979824, 'bytes': 1539051893033},
                              'duplicate_acks': 10393414, 'acks_for_unsent_data': 0,
                              'received_in_sequence': {'count': 3699041286, 'bytes': 1277742909129},
                              'completely_duplicate': {'count': 352072, 'bytes': 3715009}, 'old_duplicate_packets': 27,
                              'with_some_duplicates': {'count': 1, 'bytes': 1240}, 'out_of_order': {'count': 8526035, 'bytes': 74213212},
                            'data_after_window': {'count': 6, 'bytes': 0}, 'window_probes': 0, 'window_update_packets': 7452031,
                            'packets_received_after_close': 227223, 'packets_with_bad_hardware_assisted_checksum': 0,
                            'discarded_for_bad_checksums': 0, 'discarded_for_bad_header_offset_fields': 0, 'discarded_because_packet_too_short': 0,
                            'discarded_by_listeners': 31173, 'discarded_due_to_listeners_queue_full': 0, 'ack_packet_headers_correctly_predicted': 48436410,
                            'data_packet_headers_correctly_predicted': 103232740}, 'connection_requests': 8294587,
                            'connection_accepts': 2682721, 'connections_established_including_accepts': 10977131,
                            'connections_closed_including_drops': {}, 'connections_closed': {'count': 11000738, 'drop': 175000},
                            'connections_with_ecn_capability': 0, 'times_responded_to_ecn': 0, 'embryonic_connections_dropped': 11,
                            'segments_updated_rtt': {'count': 3684801668, 'attempts': 3644028535},
                            'segments_with_congestion_window_reduced_bit_set': 0, 'segments_with_congestion_experienced_bit_set': 0,
                            'resends_due_to_path_mtu_discovery': 0, 'path_mtu_discovery_terminations_due_to_retransmits': 313,
                            'retransmit_timeouts': {'count': 20336, 'connections_dropped_by_rexmit_timeout': 23},
                            'fast_retransmits': {'count': 0, 'congestion_window_less_than_4_segments': 0}, 'newreno_retransmits': 0,
                            'times_avoided_false_fast_retransmits': 0, 'persist_timeouts': {'count': 0, 'connections_dropped_due_to_persist_timeout': 0},
                            'keepalive_timeouts': {'count': 255858, 'keepalive_probes_sent': 255848, 'connections_dropped_by_keepalive': 10},
                            'times_sack_blocks_array_is_extended': 2, 'times_sack_holes_array_is_extended': 0, 'packets_dropped_due_to_memory_allocation_failure': 0,
                            'connections_in_timewait_reused': 0, 'delayed_acks_for_syn': 0, 'delayed_acks_for_fin': 0, 'send_and_disconnects': 0,
                            'spliced_connections': 0, 'spliced_connections_closed': 0, 'spliced_connections_reset': 0, 'spliced_connections_timeout': 0,
                            'spliced_connections_persist_timeout': 0, 'spliced_connections_keepalive_timeout': 0, 'tcp_checksum_offload_disabled_during_retransmit': 0,
                            'connections_dropped_due_to_bad_acks': 1278, 'connections_dropped_due_to_duplicate_syn_packets': 0, 'fastpath_loopback_connections': 0,
                            'fastpath_loopback': {'sent': 0, 'received': 0}, 'fake_syn_segments_dropped': 0, 'fake_rst_segments_dropped': 0,
                            'data_injection_segments_dropped': 0, 'tcptr_max_connections_dropped': 0, 'tcptr_connections_dropped_for_no_memory': 0,
                            'tcptr_maximum_per_host_connections_dropped': 0, 'connections_dropped_due_to_max_assembly_queue_depth': 0},
                    'udp': {'datagrams_received': 2110127794, 'incomplete_headers': 0, 'bad_data_length_fields': 0, 'bad_checksums': 373980,
                            'dropped_due_to_no_socket': 1263094, 'broadcast_multicast_datagrams_dropped_due_to_no_socket': 21727513, 'socket_buffer_overflows': 0,
                            'delivered': 2086763207, 'datagrams_output': 2037595684},
                    'ip': {'total_packets_received': 1670553137, 'bad_header_checksums': 0, 'with_size_smaller_than_minimum': 0, 'with_data_size_data_length': 0,
                           'with_header_length_data_size': 0, 'with_data_length_header_length': 0, 'with_bad_options': 0, 'with_incorrect_version_number': 0,
                           'fragments_received': 66338768, 'fragments_dropped_dup_or_out_of_space': 0, 'fragments_dropped_after_timeout': 0, 'packets_reassembled_ok': 22027253,
                           'packets_for_this_host': 1601689633, 'packets_for_unknown_unsupported_protocol': 48733, 'packets_forwarded': 0,
                           'packets_not_forwardable': 109260, 'redirects_sent': 0, 'packets_sent_from_this_host': 1471106881, 'packets_sent_with_fabricated_ip_header': 7,
                           'output_packets_dropped_due_to_no_bufs_etc.': 0, 'output_packets_discarded_due_to_no_route': 0, 'output_datagrams_fragmented': 11883952,
                           'fragments_created': 41588842, 'datagrams_that_cant_be_fragmented': 4, 'ip_multicast_packets_dropped_due_to_no_receiver': 2,
                           'successful_path_mtu_discovery_cycles': 0, 'path_mtu_rediscovery_cycles_attempted': 0, 'path_mtu_discovery_no_response_estimates': 0,
                           'path_mtu_discovery_response_timeouts': 0, 'path_mtu_discovery_decreases_detected': 0, 'path_mtu_discovery_packets_sent': 0,
                           'path_mtu_discovery_memory_allocation_failures': 0, 'ipintrq_overflows': 0, 'with_illegal_source': 4, 'packets_processed_by_threads': 1298795897,
                           'packets_dropped_by_threads': 0, 'packets_dropped_due_to_the_full_socket_receive_buffer': 0, 'dead_gateway_detection_packets_sent': 0,
                           'dead_gateway_detection_packet_allocation_failures': 0, 'dead_gateway_detection_gateway_allocation_failures': 0,
                           'incoming_packets_dropped_due_to_mls_filters': 0, 'packets_not_sent_due_to_mls_filters': 0},
                    'ipv6': {'total_packets_received': 24394102, 'input_histogram': {'tcp': 24073505, 'udp': 140806, 'icmp_v6': 140372},
                           'with_size_smaller_than_minimum': 0, 'with_data_size_data_length': 0, 'with_incorrect_version_number': 0, 'with_illegal_source': 0, 'input_packets_without_enough_memory': 0,
                           'fragments_received': 0, 'fragments_dropped_dup_or_out_of_space': 0, 'fragments_dropped_after_timeout': 0, 'packets_reassembled_ok': 0, 'packets_for_this_host': 24354683,
                           'packets_for_unknown_unsupported_protocol': 0, 'packets_forwarded': 0, 'packets_not_forwardable': 39419, 'too_big_packets_not_forwarded': 0,
                           'packets_sent_from_this_host': 24354683, 'packets_sent_with_fabricated_ipv6_header': 0, 'output_packets_dropped_due_to_no_bufs_etc.': 0,
                           'output_packets_without_enough_memory': 0, 'output_packets_discarded_due_to_no_route': 0, 'output_datagrams_fragmented': 0, 'fragments_created': 0,
                           'packets_dropped_due_to_the_full_socket_receive_buffer': 0, 'packets_not_delivered_due_to_bad_raw_ipv6_checksum': 0, 'incoming_packets_dropped_due_to_mls_filters': 0,
                           'packets_not_sent_due_to_mls_filters': 0},
                    'icmpv6': {'calls_to_icmp6_error': 140439, 'errors_not_generated_because_old_message_was_icmpv6': 0, 'output_histogram': {'unreachable': 140372, 'packets_too_big': 0,
                           'time_exceeded': 0, 'parameter_problems': 0, 'redirects': 0, 'echo_requests': 0, 'echo_replies': 0, 'group_queries': 0, 'group_reports': 0,
                           'group_terminations': 0, 'router_solicitations': 0, 'router_advertisements': 0, 'neighbor_solicitations': 0, 'neighbor_advertisements': 0},
                           'messages_with_bad_code_fields': 0, 'messages_minimum_length': 0, 'bad_checksums': 0, 'messages_with_bad_length': 0,
                           'input_histogram': {'unreachable': 140372, 'packets_too_big': 0, 'time_exceeded': 0, 'parameter_problems': 0, 'echo_requests': 0,
                             'echo_replies': 0, 'group_queries': 0, 'bad_group_queries': 0, 'group_reports': 0, 'bad_group_reports': 0, 'our_groups_reports': 0,
                             'group_terminations': 0, 'bad_group_terminations': 0, 'router_solicitations': 0, 'bad_router_solicitations': 0, 'router_advertisements': 0, 'bad_router_advertisements': 0,
                             'neighbor_solicitations': 0, 'bad_neighbor_solicitations': 0, 'neighbor_advertisements': 0, 'bad_neighbor_advertisements': 0, 'redirects': 0,
                             'bad_redirects': 0, 'mobility_calls_when_not_started': 0, 'home_agent_address_discovery_requests': 0, 'bad_home_agent_address_discovery_requests': 0,
                             'home_agent_address_discovery_replies': 0, 'bad_home_agent_address_discovery_replies': 0, 'prefix_solicitations': 0, 'bad_prefix_solicitations': 0,
                             'prefix_advertisements': 0, 'bad_prefix_advertisements': 0}, 'message_responses_generated': 0}}


    assert coll_netstat.load_from_file('tests/test_data/netstat_s_aix', parse_function=coll_netstat.parse_netstat_s) == expected_ret



  def test_lparstat_stats(self) :
    coll_lparstat = lparstat_parser()
    expected_ret = {'user': [0.9, 0.4], 'sys': [0.7, 0.3], 'wait': [0.0, 0.0], 'idle': [98.4, 99.3],
                    'physc': [0.34, 0.17], 'entc': [4.2, 2.1], 'lbusy': [1.1, 0.2],
                    'app': [15.3, 15.37], 'vcsw': [3760, 3111], 'phint': [0, 0], 'nsp': [113, 101],
                    'utcyc': [11.19, 1.06]}
    assert coll_lparstat.load_from_file('tests/test_data/lparstat_1_2', parse_function=coll_lparstat.parse_lparstat_stats) == expected_ret


  def test_lparstat_info(self) :
    coll_lparstat = lparstat_parser()
    expected_ret = {'node_name': 'oracle1', 'partition_name': 'oracle-1', 'partition_number': 1,
                    'type': 'shared-smt-4', 'mode': 'uncapped', 'entitled_capacity': 8.0,
                    'partition_group-id': 32769, 'shared_pool_id': 0, 'online_virtual_cpus': 9,
                    'maximum_virtual_cpus': 16, 'minimum_virtual_cpus': 1, 'online_memory': 921600,
                    'maximum_memory': 921600, 'minimum_memory': 1024, 'variable_capacity_weight': 128,
                    'minimum_capacity': 0.05, 'maximum_capacity': 16.0, 'capacity_increment': 0.01,
                    'maximum_physical_cpus_in_system': 16, 'active_physical_cpus_in_system': 16,
                    'active_cpus_in_pool': 16, 'shared_physical_cpus_in_system': 16,
                    'maximum_capacity_of_pool': 1600, 'entitled_capacity_of_pool': 1600, 'unallocated_capacity': 0.0,
                    'physical_cpu_percentage': 88.89, 'unallocated_weight': 0, 'memory_mode': 'dedicated',
                    'total_i_o_memory_entitlement': 0, 'variable_memory_capacity_weight': 0, 'memory_pool_id': 0,
                    'physical_memory_in_the_pool': 0, 'hypervisor_page_size': 0,
                    'unallocated_variable_memory_capacity_weight': 0, 'unallocated_i_o_memory_entitlement': 0,
                    'memory_group_id_of_lpar': 0, 'desired_virtual_cpus': 9, 'desired_memory': 921600,
                    'desired_variable_capacity_weight': 128, 'desired_capacity': 8.0, 'target_memory_expansion_factor': 0,
                    'target_memory_expansion_size': 0, 'power_saving_mode': 'dynamic power savings (favor performance)', 'sub_processor_mode': 0}

    assert coll_lparstat.load_from_file('tests/test_data/lparstat_i', parse_function=coll_lparstat.parse_lparstat_i) == expected_ret

  def test_mpstat_stats(self):

    coll_mpstat = mpstat_parser(bos_data = bos_data())
    coll_mpstat.bos_data.data = { 'bos' : { 'os' : 'aix' }}
    expected_ret = {'cpu'  : ['ALL', 'ALL'], 'min':    [9655, 3358], 'maj':   [0, 0],     'mpcs':  [0, 0],
                    'mpcr' : [0, 0],         'dev':    [42, 84],     'soft':  [112, 112], 'dec':   [2886, 2868],
                    'ph'   : [0, 0],         'cs':     [3364, 3370], 'ics':   [18, 16],   'bound': [2, 1],
                    'push' : [0, 0],         'S3pull': [0, 0],       'S3grd': [0, 0],     'S0rd':  [94.6, 95.8],
                    'S2rd' : [0.0, 0.0],     'S3rd':   [5.4, 4.2],   'S4rd':  [0.0, 0.0], 'S5rd':  [0.0, 0.0],
                    'sysc' : [11929, 6945],  'us':     [0.9, 0.6],   'sy':    [0.6, 0.3], 'wa':    [0.0, 0.0],
                    'pc'   : [0.27, 0.25],   'ec':     [3.3, 3.1],   'ilcs':  [1, 0],     'vlcs':  [3302, 3305],
                    'S3hrd': [98.9, 99.1],   'S4hrd':  [1.1, 0.9],   'S5hrd': [0.0, 0.0], 'nsp':   [0, 0],
                    'rq'   : [2, 1],         'S1rd':   [0.0, 0.0],   'id':    [98.5, 99.1]}

    assert coll_mpstat.load_from_file('tests/test_data/mpstat_a_1_2', parse_function=coll_mpstat.parse_mpstat_stats) == expected_ret

