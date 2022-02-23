def try_conv_complex(string:str, avoid_complex=True) :
  '''
  Type to convert a string to a number
  If the convertion fails, return the original string
  It will try on the following order:
    int -> float -> complex

  Parameters :
    string        = String to be converted
    avoid_complex = True or False, if as last attempt try to convert to a complex type number

  Returns :
    int or float or complex or string

  '''
  try :
    return(int(string))
  except ValueError:
    try :
      return(float(string))
    except ValueError:
      try :
        if avoid_complex == False :
          return(complex(string))
        else :
          return(string)
      except ValueError:
        return(string)

