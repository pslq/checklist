#!/opt/freeware/bin/python3

'''
Test routines to validate that main components are working
'''
import pytest

from pq_checklist.mpstat import parser as mpstat_parser
from pq_checklist.lparstat import parser as lparstat_parser
from pq_checklist.netstat import parser as netstat_parser
from pq_checklist.bos_info import bos as bos_parser
from pq_checklist.entstat import parser as entstat_parser


class TestClass:

  def test_entstat_etherchannel(self) :
    expected_ret = {
      'en4': {'device_type': 'IEEE 802.3ad Link Aggregation', 'hardware_address': '98:be:94:77:bb:7e', 'elapsed_time': '3 days 5 hours 15 minutes 26 seconds', 'transmit_stats':
        {'transmit_packets': 1743505, 'receive_packets': 11042941, 'transmit_bytes': 197535808, 'receive_bytes': 802353777, 'transmit_interrupts': 1659977,
          'receive_interrupts': 9377269, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0,
          'max_packets_on_s_w_transmit_queue': 6, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0, 'transmit_broadcast_packets': 217,
          'receive_broadcast_packets': 9484363, 'transmit_multicast_packets': 18663, 'receive_multicast_packets': 95215, 'no_carrier_sense': 0, 'crc_errors': 0,
          'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0,
          'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0,
          'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0 },
        'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 0, 'adapter_data_rate': 2000, 'driver_flags': 'Up Broadcast Running'},
        'general_lacp': {
          'number_of_primary_adapters': 2, 'number_of_backup_adapters': 0, 'active_channel': 'primary channel', 'operating_mode': 'Standard mode (IEEE 802.3ad)',
          'primary_aggregation_status': 'Aggregated', 'lacpdu_interval': 'LACPDUs', 'longreceived': 18551, 'transmitted_lacpdus': 18548, 'received_marker_pdus': 0,
          'transmitted_marker_pdus': 0, 'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0, 'received_illegal_pdus': 0,
          'hash_mode': 'Source and destination TCP/UDP ports', 'mac_swap': 'disabled' } },
      'ent2': {
        'general_lacp': {'device_type': 'PCIe2 4-Port Adapter (1GbE RJ45) (e4148a1614109404)', 'hardware_address': '98:be:94:77:bb:7e'},
        'transmit_stats': {'transmit_packets': 832572, 'receive_packets': 5565555, 'transmit_bytes': 78310552, 'receive_bytes': 417092344,
          'transmit_interrupts': 799252, 'receive_interrupts': 3979897, 'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0,
          'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 3, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0,
          'transmit_broadcast_packets': 0, 'receive_broadcast_packets': 4829138, 'transmit_multicast_packets': 9276, 'receive_multicast_packets': 35921, 'no_carrier_sense': 0,
          'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0, 'no_resource_errors': 0,
          'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0, 'packet_too_long_errors': 0,
          'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0, 'current_hw_transmit_queue_length': 0},
        'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 1, 'adapter_data_rate': 2000, 'driver_flags': 'Up Broadcast Running'},
        'dev_stats': {
          'device_id': 'e4148a1614109404', 'version': 1, 'physical_port_link_status': 'Up', 'logical_port_link_status': 'Up', 'physical_port_speed': '1 Gbps Full Duplex',
          'pci_mode': 'PCI-Express X8', 'pcie_link_speed': '5.0 GT/s', 'tlp_size': 512, 'mrr_size': 4096, 'relaxed_ordering': 'Enabled', 'assigned_interrupt_source_numbers': 5,
          'unassigned_interrupt_source_numbers': 27, 'external_loopback_changeable': 'No', 'external_loopback': 'Disabled', 'internal_loopback': 'Disabled',
          'physical_port_promiscuous_mode_changeable': 'Yes', 'physical_port_promiscuous_mode': 'Disabled', 'logical_port_promiscuous_mode': 'Disabled',
          'physical_port_all_multicast_mode_changeable': 'Yes', 'physical_port_all_multicast_mode': 'Disabled', 'logical_port_all_multicast_mode': 'Disabled',
          'multicast_addresses_enabled': 3, 'maximum_exact_match_multicast_filters': 0, 'maximum_inexact_match_multicast_filters': 256, 'physical_port_mtu_changeable': 'Yes',
          'physical_port_mtu': 1514, 'logical_port_mtu': 1514, 'jumbo_frames': 'Disabled', 'enabled_vlan_ids': 'None',
          'maximum_dma_page_size': 4096, 'transmit_and_receive_flow_control_status': 'Enabled', 'number_of_xoff_packets_transmitted': 0, 'number_of_xon_packets_transmitted': 0,
          'number_of_xoff_packets_received': 0, 'number_of_xon_packets_received': 0, 'receive_tcp_segment_aggregation': 'Enabled', 'receive_tcp_segment_aggregation_large_packets_created': 1024,
          'receive_tcp_packets_aggregated_into_large_packets': 1513, 'receive_tcp_payload_bytes_aggregated_into_large_packets': 2109032, 'receive_tcp_segment_aggregation_average_packets_aggregated': 1,
          'receive_tcp_segment_aggregation_maximum_packets_aggregated': 3, 'transmit_tcp_segmentation_offload': 'Enabled',
          'transmit_tcp_segmentation_offload_packets_transmitted': 279, 'transmit_tcp_segmentation_offload_maximum_packet_size': 59950, 'minimum_mss_mode': 'Disabled',
          'transmit_padded_packets': 0, 'transmit_q_packets': 832575, 'transmit_q_multicast_packets': 9276, 'transmit_q_broadcast_packets': 0, 'transmit_q_flip_and_run_packets': 383872,
          'transmit_q_bytes': 78311310, 'transmit_q_no_buffers': 0, 'transmit_q_dropped_packets': 0, 'transmit_swq_cur_packets': 0,
          'transmit_swq_max_packets': 3, 'transmit_swq_dropped_packets': 0, 'transmit_ofq_cur_packets': 0, 'transmit_ofq_max_packets': 0, 'receive_q_packets': 197960,
          'receive_q_multicast_packets': 8104, 'receive_q_broadcast_packets': 26813, 'receive_q_bytes': 21933062, 'receive_q_no_buffers': 0, 'receive_q_errors': 0, 'receive_q_dropped_packets': 0},
        'addon_stats': {'rx_bytes': 439349280, 'rx_error_bytes': 0, 'rx_ucast_packets': 700496, 'rx_mcast_packets': 35921, 'rx_bcast_packets': 4829063,
          'rx_crc_errors': 0, 'rx_align_errors': 0, 'rx_undersize_packets': 0, 'rx_oversize_packets': 0, 'rx_fragments': 0, 'rx_jabbers': 0, 'rx_discards': 0,
          'rx_filtered_packets': 1319190, 'rx_mf_tag_discard': 0, 'pfc_frames_received': 0, 'pfc_frames_sent': 0, 'rx_brb_discard': 0, 'rx_brb_truncate': 0, 'rx_pause_frames': 0,
          'rx_mac_ctrl_frames': 0, 'rx_constant_pause_events': 0, 'rx_phy_ip_err_discards': 0, 'rx_csum_offload_errors': 0, 'tx_bytes': 81730588, 'tx_error_bytes': 0, 'tx_ucast_packets': 824729,
          'tx_mcast_packets': 9276, 'tx_bcast_packets': 0, 'tx_mac_errors': 0, 'tx_carrier_errors': 0, 'tx_single_collisions': 0, 'tx_multi_collisions': 0, 'tx_deferred': 0,
          'tx_excess_collisions': 0, 'tx_late_collisions': 0, 'tx_total_collisions': 0, 'tx_64_byte_packets': 10203, 'tx_65_to_127_byte_packets': 766278, 'tx_128_to_255_byte_packets': 36714, 'tx_256_to_511_byte_packets': 12741,
          'tx_512_to_1023_byte_packets': 4926, 'tx_1024_to_1522_byte_packets': 3142, 'tx_1523_to_9022_byte_packets': 0, 'tx_pause_frames': 0,
          'recoverable_errors': 0, 'unrecoverable_errors': 0, 'tx_lpi_entry_count': 0, '_q-0_': 'tx_bcast_packets', '': 0, '_q-1_': 'tx_bcast_packets', '_q-2_': 'tx_bcast_packets', '_q-3_': 'tx_bcast_packets'},
        'lacp_port_stats': {'actor_system_priority': '0x8000', 'actor_system': '98-BE-94-77-BB-7E', 'actor_operational_key': '0xBEEF', 'actor_port_priority': '0x0080', 'actor_port': '0x0003',
          'actor_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False'},
          'partner_system_priority': '0x0000', 'partner_system': '00-04-96-CD-75-1B', 'partner_operational_key': '0x03E9', 'partner_port_priority': '0x0000', 'partner_port': '0x03EB',
          'partner_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled',
            'defaulted': 'False', 'expired': 'False', 'received_lacpdus': 9276, 'transmitted_lacpdus': 9274, 'received_marker_pdus': 0, 'transmitted_marker_pdus': 0,
            'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0, 'received_illegal_pdus': 0}}
        },
      'ent3': {
        'lacp_port_stats': {'partner_state': {'device_type': 'PCIe2 4-Port Adapter (1GbE RJ45) (e4148a1614109404)', 'lacp_activity': 'Active', 'lacp_timeout': 'Long',
          'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False', 'received_lacpdus': 9275,
          'transmitted_lacpdus': 9274, 'received_marker_pdus': 0, 'transmitted_marker_pdus': 0, 'received_marker_response_pdus': 0, 'transmitted_marker_response_pdus': 0, 'received_unknown_pdus': 0,
          'received_illegal_pdus': 0}, 'hardware_address': '98:be:94:77:bb:7e', 'actor_system_priority': '0x8000', 'actor_system': '98-BE-94-77-BB-7E', 'actor_operational_key': '0xBEEF',
          'actor_port_priority': '0x0080', 'actor_port': '0x0004',
        'actor_state': {'lacp_activity': 'Active', 'lacp_timeout': 'Long', 'aggregation': 'Aggregatable', 'synchronization': 'IN_SYNC', 'collecting': 'Enabled', 'distributing': 'Enabled', 'defaulted': 'False', 'expired': 'False'},
          'partner_system_priority': '0x0000', 'partner_system': '00-04-96-CD-75-1B', 'partner_operational_key': '0x03E9', 'partner_port_priority': '0x0000', 'partner_port': '0x03E9'},
        'transmit_stats': {'transmit_packets': 910936, 'receive_packets': 5477386, 'transmit_bytes': 119226222, 'receive_bytes': 385261433, 'transmit_interrupts': 860728, 'receive_interrupts': 5397372,
          'transmit_errors': 0, 'receive_errors': 0, 'transmit_packets_dropped': 0, 'receive_packets_dropped': 0, 'bad_packets': 0, 'max_packets_on_s_w_transmit_queue': 3, 's_w_transmit_queue_overflow': 0, 'current_s_w_h_w_transmit_queue_length': 0,
          'transmit_broadcast_packets': 217, 'receive_broadcast_packets': 4655225, 'transmit_multicast_packets': 9387, 'receive_multicast_packets': 59294,
          'no_carrier_sense': 0, 'crc_errors': 0, 'dma_underrun': 0, 'dma_overrun': 0, 'lost_cts_errors': 0, 'alignment_errors': 0, 'max_collision_errors': 0,
          'no_resource_errors': 0, 'late_collision_errors': 0, 'receive_collision_errors': 0, 'deferred': 0, 'packet_too_short_errors': 0, 'sqe_test': 0,
          'packet_too_long_errors': 0, 'timeout_errors': 0, 'packets_discarded_by_adapter': 0, 'single_collision_count': 0, 'receiver_start_count': 0, 'multiple_collision_count': 0,
          'current_hw_transmit_queue_length': 0},
        'general_stats': {'no_mbuf_errors': 0, 'adapter_reset_count': 1, 'adapter_data_rate': 2000, 'driver_flags': 'Up Broadcast Running'},
        'dev_stats': {'device_id': 'e4148a1614109404', 'version': 1, 'physical_port_link_status': 'Up', 'logical_port_link_status': 'Up',
          'physical_port_speed': '1 Gbps Full Duplex', 'pci_mode': 'PCI-Express X8', 'pcie_link_speed': '5.0 GT/s', 'tlp_size': 512, 'mrr_size': 4096, 'relaxed_ordering': 'Enabled',
          'assigned_interrupt_source_numbers': 5, 'unassigned_interrupt_source_numbers': 27, 'external_loopback_changeable': 'No', 'external_loopback': 'Disabled', 'internal_loopback': 'Disabled',
          'physical_port_promiscuous_mode_changeable': 'Yes', 'physical_port_promiscuous_mode': 'Disabled', 'logical_port_promiscuous_mode': 'Disabled', 'physical_port_all_multicast_mode_changeable': 'Yes',
          'physical_port_all_multicast_mode': 'Disabled', 'logical_port_all_multicast_mode': 'Disabled', 'multicast_addresses_enabled': 3, 'maximum_exact_match_multicast_filters': 0, 'maximum_inexact_match_multicast_filters': 256,
          'physical_port_mtu_changeable': 'Yes', 'physical_port_mtu': 1514, 'logical_port_mtu': 1514, 'jumbo_frames': 'Disabled', 'enabled_vlan_ids': 'None',
          'maximum_dma_page_size': 4096, 'transmit_and_receive_flow_control_status': 'Enabled', 'number_of_xoff_packets_transmitted': 0, 'number_of_xon_packets_transmitted': 0, 'number_of_xoff_packets_received': 0,
          'number_of_xon_packets_received': 0, 'receive_tcp_segment_aggregation': 'Enabled', 'receive_tcp_segment_aggregation_large_packets_created': 28011, 'receive_tcp_packets_aggregated_into_large_packets': 28705,
          'receive_tcp_payload_bytes_aggregated_into_large_packets': 39506685, 'receive_tcp_segment_aggregation_average_packets_aggregated': 1, 'receive_tcp_segment_aggregation_maximum_packets_aggregated': 3,
          'transmit_tcp_segmentation_offload': 'Enabled', 'transmit_tcp_segmentation_offload_packets_transmitted': 6249, 'transmit_tcp_segmentation_offload_maximum_packet_size': 56538, 'minimum_mss_mode': 'Disabled',
          'transmit_padded_packets': 0, 'transmit_q_packets': 910936, 'transmit_q_multicast_packets': 9387, 'transmit_q_broadcast_packets': 217, 'transmit_q_flip_and_run_packets': 355346, 'transmit_q_bytes': 119226222,
          'transmit_q_no_buffers': 0, 'transmit_q_dropped_packets': 0, 'transmit_swq_cur_packets': 0, 'transmit_swq_max_packets': 3, 'transmit_swq_dropped_packets': 0, 'transmit_ofq_cur_packets': 0, 'transmit_ofq_max_packets': 0,
          'receive_q_packets': 219490, 'receive_q_multicast_packets': 7031, 'receive_q_broadcast_packets': 48388, 'receive_q_bytes': 26029655, 'receive_q_no_buffers': 0, 'receive_q_errors': 0, 'receive_q_dropped_packets': 0},
        'addon_stats': {
          'rx_bytes': 407162874, 'rx_error_bytes': 0, 'rx_ucast_packets': 762828, 'rx_mcast_packets': 59294, 'rx_bcast_packets': 4655211, 'rx_crc_errors': 0, 'rx_align_errors': 0, 'rx_undersize_packets': 0,
          'rx_oversize_packets': 0, 'rx_fragments': 0, 'rx_jabbers': 0, 'rx_discards': 0, 'rx_filtered_packets': 1221689, 'rx_mf_tag_discard': 0, 'pfc_frames_received': 0, 'pfc_frames_sent': 0, 'rx_brb_discard': 0,
          'rx_brb_truncate': 0, 'rx_pause_frames': 0, 'rx_mac_ctrl_frames': 0, 'rx_constant_pause_events': 0, 'rx_phy_ip_err_discards': 0, 'rx_csum_offload_errors': 0,
          'tx_bytes': 124256253, 'tx_error_bytes': 0, 'tx_ucast_packets': 922697, 'tx_mcast_packets': 9387, 'tx_bcast_packets': 217, 'tx_mac_errors': 0, 'tx_carrier_errors': 0,
          'tx_single_collisions': 0, 'tx_multi_collisions': 0, 'tx_deferred': 0, 'tx_excess_collisions': 0, 'tx_late_collisions': 0, 'tx_total_collisions': 0, 'tx_64_byte_packets': 11305,
          'tx_65_to_127_byte_packets': 801552, 'tx_128_to_255_byte_packets': 75756, 'tx_256_to_511_byte_packets': 12367, 'tx_512_to_1023_byte_packets': 4963, 'tx_1024_to_1522_byte_packets': 26357,
          'tx_1523_to_9022_byte_packets': 0, 'tx_pause_frames': 0, 'recoverable_errors': 0, 'unrecoverable_errors': 0, 'tx_lpi_entry_count': 0,
          '_q-0_': 'tx_bcast_packets', '': 0, '_q-1_': 'tx_bcast_packets', '_q-2_': 'tx_bcast_packets', '_q-3_': 'tx_bcast_packets'}}
        }


  def test_bos_info_lsdev_class(self):
    parser = bos_parser()
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
    assert coll_netstat.load_from_file('tests/test_data/netstat_s', parse_function=coll_netstat.parse_netstat_s) == expected_ret



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

    assert coll_mpstat.load_from_file('tests/test_data/mpstat_a_1_2', parse_function=coll_mpstat.parse_mpstat_stats) == expected_ret

