from .pq_round_number import pq_round_number
from .avg_list  import avg_list

def get_list_avg_and_diff(lst:list, calculate_diff:bool=True) :
  if calculate_diff :
    just_changes = [ v if p == 0 else v-lst[p-1] for p,v in enumerate(lst) ]
  else :
    just_changes = lst
  change_rate = pq_round_number([ True if p == 0 else True if v-just_changes[p-1] == 0 else False for p,v in enumerate(just_changes) ].count(False)/len(just_changes))
  return(just_changes,avg_list(just_changes), change_rate)


