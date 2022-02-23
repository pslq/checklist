

def custom_monitor(elements_monitored, element, value) :
  ret = None
  if element in elements_monitored :
    if isinstance(value, list) :
      if len(value) == 4 : # possibly pre-worked list with calculated averages
        if all([ isinstance(value[0], list), isinstance(value[3], list) ]) :
          if elements_monitored[element]['criteria'] in [ 'gt', '>', 'great', 'maior' ] :
            if len(value[3]) > 1 :
              if abs(stat_data[3][-1]-stat_data[3][-2]) > elements_monitored[element]['value'] :
                if 'message' in elements_monitored[element] :
                  ret = elements_monitored[element]['message']+' ( from %d to %d, avg : %f )'%(value[3][-2], value[3][-1], float(value[2]))
                else :
                  ret = '%s incremented from %d to %d'%(element, value[3][-2], value[3][-1])
            elif value[3][-1] > elements_monitored[element]['value'] :
              ret = elements_monitored[element]['message']+' ( to : %d )'%value[3][-1]
          elif elements_monitored[element]['criteria'] in [ 'lt', '<', 'less', 'menor' ] :
            if len(value[3]) < 1 :
              if abs(stat_data[3][-1]-stat_data[3][-2]) < elements_monitored[element]['value'] :
                if 'message' in elements_monitored[element] :
                  ret = elements_monitored[element]['message']+' ( from %d to %d, avg : %f )'%(value[3][-2], value[3][-1], float(value[2]))
                else :
                  ret = '%s decremented from %d to %d'%(element, value[3][-2], value[3][-1])
            elif value[3][-1] < elements_monitored[element]['value'] :
              ret = elements_monitored[element]['message']+' ( to : %d )'%value[3][-1]
    elif isinstance(value, str) :
      if ( elements_monitored[element]['criteria'] in [ '=', '==', 'equal', 'igual' ] and \
           value == elements_monitored[element]['value'] ) or \
         ( elements_monitored[element]['criteria'] in [ '!', '!=', 'diff', 'diferente' ] and \
           value != elements_monitored[element]['value'] ) :
        if 'message' in elements_monitored[element] :
          ret = elements_monitored[element]['message']
        else :
          ret = '%s reached value of %s'%( element, value )

  return(ret)
