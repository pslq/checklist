#!/opt/freeware/bin/python3

'''
Test routines to validate that main components are working
'''
import pytest

from .mpstat import parser as mpstat_parser
from .lparstat import parser as lparstat_parser
from .netstat import parser as netstat_parser
from .bos_info import bos as bos_parser


class TestClass:

  def test_bos_info_lsdev_class(self):
    parser = bos_parser()
    expected_ret = {
      'L2cache0': {'class': 'memory', 'subclass': 'sys', 'type': 'L2cache_rspc'}, 'arch': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'cd0': {'class': 'cdrom', 'subclass': 'vscsi', 'type': 'vopt'}, 'cluster0': {'class': 'pseudo', 'subclass': 'node', 'type': 'cluster'},
      'en0': {'class': 'if', 'subclass': 'EN', 'type': 'en'}, 'ent0': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,l-lan'},
      'ent1': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,l-lan'}, 'fcs0': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,vfc-client'},
      'fcs1': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,vfc-client'}, 'fcs2': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,vfc-client'},
      'fcs3': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,vfc-client'}, 'flr0': {'class': 'driver', 'subclass': 'fsf', 'type': 'flr'},
      'fscsi0': {'class': 'driver', 'subclass': 'vio_npiv', 'type': 'emfscsi'}, 'fscsi1': {'class': 'driver', 'subclass': 'vio_npiv', 'type': 'emfscsi'},
      'fscsi2': {'class': 'driver', 'subclass': 'vio_npiv', 'type': 'emfscsi'}, 'fscsi3': {'class': 'driver', 'subclass': 'vio_npiv', 'type': 'emfscsi'},
      'gghome': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'gghomedirdat': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'hdisk0': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk1': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk2': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk99': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk101': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk102': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk110': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk111': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk112': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk113': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk201': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk202': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk203': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk204': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk205': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk206': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk207': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk208': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk209': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk210': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk211': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk212': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk213': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk214': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk215': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk216': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk217': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk218': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk219': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk220': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk221': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk222': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk223': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk224': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk225': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk226': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk227': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk228': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk229': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk250': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk251': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk252': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk253': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk254': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk255': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk256': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk257': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk258': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk259': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk260': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk261': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk262': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk263': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk264': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk265': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk880': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk881': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk882': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk883': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk884': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk885': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk886': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk887': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk888': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk889': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'hdisk890': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'},
      'hdisk891': {'class': 'disk', 'subclass': 'fcp', 'type': 'mpioosdisk'}, 'inet0': {'class': 'tcpip', 'subclass': 'TCPIP', 'type': 'inet'},
      'iocp0': {'class': 'iocp', 'subclass': 'node', 'type': 'iocp'}, 'iscsi0': {'class': 'driver', 'subclass': 'node', 'type': 'iscsi'},
      'lo0': {'class': 'if', 'subclass': 'LO', 'type': 'lo'}, 'loglv00': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'lv01': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'lvdd': {'class': 'lvm', 'subclass': 'lvm', 'type': 'lvdd'},
      'mem0': {'class': 'memory', 'subclass': 'sys', 'type': 'totmem'}, 'mlgA': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'mlgB': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'nsmb0': {'class': 'network', 'subclass': 'pseudo', 'type': 'smb'},
      'nsmbc0': {'class': 'network', 'subclass': 'pseudo', 'type': 'smbc'}, 'olgA': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'olgB': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'pkcs11': {'class': 'adapter', 'subclass': 'pseudo', 'type': 'ibm_pkcs11'},
      'proc0': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc8': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc16': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc24': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc32': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc40': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc48': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc56': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc64': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc72': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc80': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc88': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc96': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc104': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc112': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc120': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc128': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc136': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc144': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc152': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc160': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc168': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc176': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc184': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc192': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc200': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc208': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc216': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'proc224': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'}, 'proc232': {'class': 'processor', 'subclass': 'sys', 'type': 'proc_rspc'},
      'pty0': {'class': 'pty', 'subclass': 'pty', 'type': 'pty'}, 'sfw0': {'class': 'driver', 'subclass': 'storfwork', 'type': 'module'},
      'sfwcomm0': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'}, 'sfwcomm1': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'},
      'sfwcomm2': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'}, 'sfwcomm3': {'class': 'driver', 'subclass': 'fcp', 'type': 'storfwork'},
      'sys0': {'class': 'sys', 'subclass': 'node', 'type': 'chrp'}, 'sysplanar0': {'class': 'planar', 'subclass': 'sys', 'type': 'sysplanar_rspc'},
      'vgdata-EP0_ctrl': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgdata-EP0_dt1': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgdata-EP0_dt2': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgdata-EP0_dt3': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgdata-EP0_dt4': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgdata-EP0_dt5': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgdata-EP0_dt6': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgdata-EP0_dt7': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgdata-EP0_dt8': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgdata-EP0_dt9': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgdata-EP0_dt10': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgexp-EP0_arch': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgexp-EP0_sm': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgexp-stable': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgora-EP0_bin': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgora-EP0_orac': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgora-EP0_reor': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgsap-EP0_ascs': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vgsap-EP0_ers': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'}, 'vgsap-EP0_pas': {'class': 'logical_volume', 'subclass': 'lvsubclass', 'type': 'lvtype'},
      'vio0': {'class': 'bus', 'subclass': 'chrp', 'type': 'vdevice'}, 'vsa0': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'hvterm1'},
      'vscsi0': {'class': 'adapter', 'subclass': 'vdevice', 'type': 'IBM,v-scsi'}, 'vty0': {'class': 'tty', 'subclass': 'vcon', 'type': 'tty'}}
    assert parser.load_from_file('pq_checklist/test_data/lsdev_class', parse_function=parser.parse_lsdev_class) == expected_ret

  def test_netstat_stats(self):
    coll_netstat = netstat_parser()
    expected_ret = {
        'icmp': {
          'calls_to_icmp_error': 20320, 'errors_not_generated_because_old_message_was_icmp': 0, 'histogram': 'Input', 'echo_reply': 14, 'destination_unreachable': 6,
          'echo': 131, 'messages_with_bad_code_fields': 0, 'messages_minimum_length': 0, 'bad_checksums': 0, 'messages_with_bad_length': 0, 'message_responses_generated': 131
          },
        'igmp': {
          'messages_received': 820, 'messages_received_with_too_few_bytes': 0, 'messages_received_with_bad_checksum': 0, 'membership_queries_received': 820,
          'membership_queries_received_with_invalid': 0, 'membership_reports_received': 0, 'membership_reports_received_with_invalid': 0,
          'membership_reports_received_for_groups_to_which_we_belong': 0, 'membership_reports_sent': 10
          },
        'tcp': {
          'packets_sent': 1312834, 'data_packets': 683602, 'data_packets_retransmitted': 41, 'ack-only_packets': 344234,
          'urg_only_packets': 0, 'window_probe_packets': 0, 'window_update_packets': 52686, 'control_packets': 230075,
          'large_sends': 6217, 'bytes_sent_using_largesend': 33470074, 'bytes_is_the_biggest_largesend': 56472,
          'packets_received': 1053051, 'acks_2864107953': 569618, 'duplicate_acks': 130065, 'acks_for_unsent_data': 0, 'packets_received_in-sequence': 378409,
          'completely_duplicate_packets': 3819, 'old_duplicate_packets': 0, 'packets_with_some_dup_data_bytes': 0,
          'out-of-order_packets': 100861, 'packets_of_data_after_window': 0, 'window_probes': 0, 'packets_received_after_close': 3460,
          'packets_with_bad_hardware_assisted_checksum': 0, 'discarded_for_bad_checksums': 0, 'discarded_for_bad_header_offset_fields': 0, 'discarded_because_packet_too_short': 0,
          'discarded_by_listeners': 332, 'discarded_due_to_queue_full': 0, 'ack_packet_headers_correctly_predicted': 8517, 'data_packet_headers_correctly_predicted': 125024,
          'connection_requests': 95346, 'connection_accepts': 54003, 'connections_established': 149329, 'connections_closed_11198': 149695, 'connections_with_ecn_capability': 0,
          'times_responded_to_ecn': 0, 'embryonic_connections_dropped': 4, 'segments_updated_rtt_652233': 660984, 'segments_with_congestion_window_reduced_bit_set': 0,
          'segments_with_congestion_experienced_bit_set': 0, 'resends_due_to_path_mtu_discovery': 0, 'path_mtu_discovery_terminations_due_to_retransmits': 23, 'retransmit_timeouts': 473,
          'connections_dropped_by_rexmit_timeout': 2, 'fast_retransmits': 0, 'when_congestion_window_less_than_4_segments': 0, 'newreno_retransmits': 0,
          'times_avoided_false_fast_retransmits': 0, 'persist_timeouts': 0, 'connections_dropped_due_to_persist_timeout': 0, 'keepalive_timeouts': 2730, 'keepalive_probes_sent': 2730,
          'connections_dropped_by_keepalive': 0, 'times_sack_blocks_array_is_extended': 0, 'times_sack_holes_array_is_extended': 0, 'packets_dropped_due_to_memory_allocation_failure': 0,
          'connections_in_timewait_reused': 0, 'delayed_acks_for_syn': 0, 'delayed_acks_for_fin': 0, 'send_and_disconnects': 0, 'spliced_connections': 0,
          'spliced_connections_closed': 0, 'spliced_connections_reset': 0, 'spliced_connections_timeout': 0, 'spliced_connections_persist_timeout': 0, 'spliced_connections_keepalive_timeout': 0,
          'tcp_checksum_offload_disabled_during_retransmit': 0, 'connections_dropped_due_to_bad_acks': 0, 'connections_dropped_due_to_duplicate_syn_packets': 0,
          'fastpath_loopback_connections': 0, 'fastpath_loopback_sent_packets': 0, 'fastpath_loopback_received_packets': 0, 'fake_syn_segments_dropped': 0, 'fake_rst_segments_dropped': 0,
          'data_injection_segments_dropped': 0, 'tcptr_max_connections_dropped': 0, 'tcptr_connections_dropped_for_no_memory': 0, 'tcptr_maximum_per_host_connections_dropped': 0,
          'connections_dropped_due_to_max_assembly_queue_depth': 0
          },
        'udp': {
          'datagrams_received': 34599107, 'incomplete_headers': 0, 'bad_data_length_fields': 0, 'bad_checksums': 9759, 'dropped_due_to_no_socket': 22678,
          'datagrams_dropped_due_to_no_socket': 248363, 'socket_buffer_overflows': 0, 'delivered': 34318307, 'datagrams_output': 32386042
          },
        'ip': {
          'total_packets_received': 35864466, 'bad_header_checksums': 0, 'with_size_smaller_than_minimum': 0, 'with_data_size_data_length': 0, 'with_header_length_data_size': 0,
          'with_data_length_header_length': 0, 'with_bad_options': 0, 'with_incorrect_version_number': 0, 'fragments_received': 281676, 'fragments_dropped_or_out_of': 0,
          'fragments_dropped_after_timeout': 0, 'packets_reassembled_ok': 75232, 'packets_for_this_host': 35246755, 'packets_for_protocol': 823, 'packets_forwarded': 0,
          'packets_not_forwardable': 1953, 'redirects_sent': 0, 'packets_sent_from_this_host': 33320333, 'packets_sent_with_fabricated_ip_header': 7,
          'output_packets_dropped_due_to_no_bufs,_etc': 0, 'output_packets_discarded_due_to_no_route': 0,
          'output_datagrams_fragmented': 162544, 'fragments_created': 580428, 'datagrams_that_be_fragmented': 4, 'ip_multicast_packets_dropped_due_to_no_receiver': 0,
          'successful_path_mtu_discovery_cycles': 0, 'path_mtu_rediscovery_cycles_attempted': 0, 'path_mtu_discovery_no-response_estimates': 0, 'path_mtu_discovery_response_timeouts': 0,
          'path_mtu_discovery_decreases_detected': 0, 'path_mtu_discovery_packets_sent': 0, 'path_mtu_discovery_memory_allocation_failures': 0,
          'ipintrq_overflows': 0, 'with_illegal_source': 0, 'packets_processed_by_threads': 25533704, 'packets_dropped_by_threads': 0,
          'packets_dropped_due_to_the_full_socket_receive_buffer': 0, 'dead_gateway_detection_packets_sent': 0, 'dead_gateway_detection_packet_allocation_failures': 0,
          'dead_gateway_detection_gateway_allocation_failures': 0, 'incoming_packets_dropped_due_to_mls_filters': 0, 'packets_not_sent_due_to_mls_filters': 0,
          '': ''},
        'ipv6': {
          'total_packets_received': 408491, 'histogram': 'Input', 'tcp': 403074, 'udp': 2477, 'icmp_v6': 2358, 'with_size_smaller_than_minimum': 0,
          'with_data_size_data_length': 0, 'with_incorrect_version_number': 0, 'with_illegal_source': 0, 'input_packets_without_enough_memory': 0, 'fragments_received': 0,
          'fragments_dropped_or_out_of': 0, 'fragments_dropped_after_timeout': 0, 'packets_reassembled_ok': 0, 'packets_for_this_host': 407909,
          'packets_for_protocol': 0, 'packets_forwarded': 0, 'packets_not_forwardable': 582, 'too_big_packets_not_forwarded': 0, 'packets_sent_from_this_host': 407909,
          'packets_sent_with_fabricated_ipv6_header': 0, 'output_packets_dropped_due_to_no_bufs,_etc': 0, 'output_packets_without_enough_memory': 0,
          'output_packets_discarded_due_to_no_route': 0, 'output_datagrams_fragmented': 0, 'fragments_created': 0, 'packets_dropped_due_to_the_full_socket_receive_buffer': 0,
          'packets_not_delivered_due_to_bad_raw_ipv6_checksum': 0, 'incoming_packets_dropped_due_to_mls_filters': 0, 'packets_not_sent_due_to_mls_filters': 0},
        'icmpv6': {
            'calls_to_icmp6_error': 2358, 'errors_not_generated_because_old_message_was_icmpv6': 0, 'histogram': 'Input', 'unreachable': 2358, 'packets_too_big': 0, 'time_exceeded': 0,
            'parameter_problems': 0, 'redirects': 0, 'echo_requests': 0, 'echo_replies': 0, 'group_queries': 0, 'group_reports': 0, 'group_terminations': 0, 'router_solicitations': 0,
            'router_advertisements': 0, 'neighbor_solicitations': 0, 'neighbor_advertisements': 0, 'messages_with_bad_code_fields': 0, 'messages_minimum_length': 0, 'bad_checksums': 0,
            'messages_with_bad_length': 0, 'bad_group_queries': 0, 'bad_group_reports': 0, 'our_reports': 0, 'bad_group_terminations': 0, 'bad_router_solicitations': 0,
            'bad_router_advertisements': 0, 'bad_neighbor_solicitations': 0, 'bad_neighbor_advertisements': 0, 'bad_redirects': 0, 'mobility_calls_when_not_started': 0,
            'home_agent_address_discovery_requests': 0, 'bad_home_agent_address_discovery_requests': 0, 'home_agent_address_discovery_replies': 0,
            'bad_home_agent_address_discovery_replies': 0, 'prefix_solicitations': 0, 'bad_prefix_solicitations': 0, 'prefix_advertisements': 0, 'bad_prefix_advertisements': 0, 'message_responses_generated': 0}
        }
    assert coll_netstat.load_from_file('pq_checklist/test_data/netstat_s', parse_function=coll_netstat.parse_netstat_s) == expected_ret



  def test_lparstat_stats(self) :
    coll_lparstat = lparstat_parser()
    expected_ret = {'user': [0.9, 0.4], 'sys': [0.7, 0.3], 'wait': [0.0, 0.0], 'idle': [98.4, 99.3],
                    'physc': [0.34, 0.17], 'entc': [4.2, 2.1], 'lbusy': [1.1, 0.2],
                    'app': [15.3, 15.37], 'vcsw': [3760, 3111], 'phint': [0, 0], 'nsp': [113, 101],
                    'utcyc': [11.19, 1.06]}
    assert coll_lparstat.load_from_file('pq_checklist/test_data/lparstat_1_2', parse_function=coll_lparstat.parse_lparstat_stats) == expected_ret


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

    assert coll_lparstat.load_from_file('pq_checklist/test_data/lparstat_i', parse_function=coll_lparstat.parse_lparstat_i) == expected_ret

  def test_mpstat_stats(self):
    coll_mpstat = mpstat_parser()
    expected_ret = {'cpu'  : ['ALL', 'ALL'], 'min':    [9655, 3358], 'maj':   [0, 0],     'mpcs':  [0, 0],
                    'mpcr' : [0, 0],         'dev':    [42, 84],     'soft':  [112, 112], 'dec':   [2886, 2868],
                    'ph'   : [0, 0],         'cs':     [3364, 3370], 'ics':   [18, 16],   'bound': [2, 1],
                    'push' : [0, 0],         'S3pull': [0, 0],       'S3grd': [0, 0],     'S0rd':  [94.6, 95.8],
                    'S2rd' : [0.0, 0.0],     'S3rd':   [5.4, 4.2],   'S4rd':  [0.0, 0.0], 'S5rd':  [0.0, 0.0],
                    'sysc' : [11929, 6945],  'us':     [0.9, 0.6],   'sy':    [0.6, 0.3], 'wa':    [0.0, 0.0],
                    'pc'   : [0.27, 0.25],   'ec':     [3.3, 3.1],   'ilcs':  [1, 0],     'vlcs':  [3302, 3305],
                    'S3hrd': [98.9, 99.1],   'S4hrd':  [1.1, 0.9],   'S5hrd': [0.0, 0.0], 'nsp':   [0, 0],
                    'rq'   : [2, 1],         'S1rd':   [0.0, 0.0],   'id':    [98.5, 99.1]}

    assert coll_mpstat.load_from_file('pq_checklist/test_data/mpstat_a_1_2', parse_function=coll_mpstat.parse_mpstat_stats) == expected_ret

