def avg_list(lst:list, ndigits:int=2) :
  '''
  Calculate average value of a list
  Parameters :
    lst -> List of numbers
    ndigits -> Number of digits to be considered when rounding the number, -1 means no rouding

  Returns:
    number -> float
  '''
  ret = sum(lst)/len(lst)
  if ndigits > 0 :
    ret=round(ret, ndigits)
  return(ret)

