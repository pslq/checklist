from .. import try_conv_complex, debug_post_msg

def parse_net_v_stat_stats(logger, data:list, has_paragraphs:bool=True) -> dict:
  '''
  Parse aix's "netstat -s" like files

  Parameters:
    data           : list -> List of strings to be parsed ( loaded from either command output of file )
    has_paragraphs : bool -> If the file contents has paragraphs ( like netstat -s )

  Returns:
    dict
  '''

  ret = {}
  to_be_removed = ( '(', '<', ')', '>', '\'', ':', ',' )
  to_be_replaced = ( ( '  ', ' '), ('-', '_'), ('/', '_') )
  t1_session = ''
  cur_key=''
  for ln in data :
    ln = ln.rstrip().replace('\n','')
    t_count = ln.count('\t')
    try :
      if ln[0] != '\t' and ln[-1] == ":" :
        cur_key = ln.strip()[:-1]
        ret[cur_key] = {}
      else :
        ste = []
        nme = []

        # line cleanup
        for st in to_be_removed :
          ln = ln.replace(st,'')
        for rp in to_be_replaced :
          ln = ln.replace(rp[0],rp[1])
        ln = ln.strip().lower()

        for e in ln.split(' ') :
          if e.isnumeric() :
            nme.append(try_conv_complex(e))
          else :
            ste.append(e)

        if t_count == 1 :
          t1_session = '_'.join(ste)
          ret[cur_key][t1_session] = {}
          if len(nme) == 1 :
            if t1_session in ( 'packets_sent', 'packets_received', 'fast_retransmits' ) :
              ret[cur_key][t1_session] = { 'count' : try_conv_complex(nme[0]) }
            else :
              ret[cur_key][t1_session] = try_conv_complex(nme[0])

          elif len(nme) == 2 :
            if 'connections closed including' in ln :
              ret[cur_key]['connections_closed'] = { 'count' : nme[0] , 'drop' : nme[1] }
            elif 'segments updated rtt of' in ln :
              ret[cur_key]['segments_updated_rtt'] = { 'count' : nme[0], 'attempts' : nme[1] }
              ret[cur_key].pop(t1_session)
            elif 'fastpath loopback' in ln :
              ret[cur_key].pop(t1_session)
              try :
                ret[cur_key]['fastpath_loopback'][ste[2]] = nme[0]
              except :
                ret[cur_key]['fastpath_loopback'] = { ste[2] : nme[0] }
            else :
              debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 0 : %s,%s,%s'%(str(ste),str(nme),ln))
        elif len(nme) == 1 :
          sub_key = '_'.join(ste)
          sub_value = nme[0]
          if t_count > 1 :
            try :
              ret[cur_key][t1_session][sub_key] = sub_value
            except :
              t_value = ret[cur_key][t1_session]
              ret[cur_key][t1_session] = { 'count' : t_value, sub_key : sub_value }
          else :
            ret[cur_key][sub_key] = sub_value
        elif len(nme) == 2 :
          if t1_session == 'packets_sent' :
            if 'data packets' in ln :
              if 'bytes retransmitted' in ln :
                ret[cur_key][t1_session]['retransmitted'] = { 'count' : nme[0], 'bytes' : nme[1] }
              else :
                ret[cur_key][t1_session]['data'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'ack_only packets' in ln :
              ret[cur_key][t1_session]['ack_only'] = { 'count' : nme[0], 'delayed' : nme[1] }
            else :
              debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 1 : %s,%s,%s'%(str(ste),str(nme),ln))
          elif t1_session == 'packets_received' :
            if 'acks for' in ln :
              ret[cur_key][t1_session]['acks'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'bytes received in_sequence' in ln :
              ret[cur_key][t1_session]['received_in_sequence'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'completely duplicate packets' in ln :
              ret[cur_key][t1_session]['completely_duplicate'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'packets with some dup. data' in ln :
              ret[cur_key][t1_session]['with_some_duplicates'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'out_of_order packets' in ln :
              ret[cur_key][t1_session]['out_of_order'] = { 'count' : nme[0], 'bytes' : nme[1] }
            elif 'bytes of data after window' in ln :
              ret[cur_key][t1_session]['data_after_window'] = { 'count' : nme[0], 'bytes' : nme[1] }
            else :
              debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 2 : %s,%s,%s'%(str(ste),str(nme),ln))
          elif t1_session == 'fast_retransmits' :
            if 'when congestion window less than' in ln :
              ret[cur_key][t1_session]['congestion_window_less_than_4_segments'] = nme[0]
            else :
              debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 3 : %s,%s,%s'%(str(ste),str(nme),ln))
          else :
            debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 4 : %s,%s,%s'%(str(ste),str(nme),ln))
        else :
          debug_post_msg(logger, 'Unexpected values when parsing parse_net_v_stat_stats 5 : %s,%s,%s'%(str(ste),str(nme),ln))
    except Exception as e:
      if len(ln) > 0 :
        debug_post_msg(logger, 'Unknown error when parsing parse_net_v_stat_stats 6 : %s : %s'%(e,ln))
  return(ret)
