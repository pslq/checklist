# import external functions

from .utils.debug_post_msg import debug_post_msg
from .utils.merge_dict import merge_dict
from .utils.try_conv_complex import try_conv_complex
from .utils.avg_list import avg_list
from .utils.get_list_avg_and_diff import get_list_avg_and_diff
from .utils.pq_round_number import pq_round_number
from .utils.line_cleanup import line_cleanup
from .utils.get_command_output import get_command_output



#####################################################################################################################################################
## logging related functions ########################################################################################################################
#####################################################################################################################################################
def pq_logger(log_level:int=10, stdout:bool=False, name:str=__name__, to_dev_log:bool=True, dst_file = None) :
  '''
  Create and return a logger object used for logging across the program
  '''
  import importlib.util, logging, logging.handlers, os.path
  logger = logging.getLogger(name)
  if dst_file :
    if os.path.exists(os.path.dirname(dst_file)) :
      logger.addHandler(logging.handlers.RotatingFileHandler(dst_file, maxBytes=10485760, backupCount=90))
    else :
      debug_post_msg(None, 'Error when trying to use %s as logfile'%dst_file, screen_only=True, flush=True)
  if stdout == True :
    logger.addHandler(logging.StreamHandler())

  if to_dev_log :
    if os.path.exists('/dev/log') :
      logger.addHandler(logging.handlers.SysLogHandler(address = '/dev/log'))

    if importlib.util.find_spec('systemd') is not None :
      from systemd import journal
      logger.addHandler(journal.JournalHandler())

  ch = logging.StreamHandler()
  ch.setLevel(log_level)
  formatter = logging.Formatter('%(name)s - %(message)s')
  ch.setFormatter(formatter)
  logger.addHandler(ch)

  return(logger)

#######################################################################################################################
def load_file(logger, file:str, specific_replacements:list=[]) -> str:
  '''
  Load and parse files
  '''
  # Replace strings if any replacement defined
  ret_str = ''

  if file:
    try :
      with open(file, 'r') as fptr :
        ret_str = fptr.read()
    except Exception as e :
      debug_post_msg(logger,'Error loading sqlfile : %s'%str(e), raise_type=Exception)

  for r in specific_replacements :
    try :
      ret_str = ret_str.replace(r[0],r[1])
    except :
      pass

  return(ret_str)

#######################################################################################################################
def conv_bash_var_to_dict(string, try_conv_number=False, delimiter=" ") -> dict :
  '''
  Convert bash/shell style variables into a dictionary
    Convert:
      X=1 B=ASSA C=WWW
    Into:
      { 'X' : 1, 'B' : 'ASSA', 'C' : 'WWW }

  Parameters:
    string          -> str : String to be converted
    try_conv_number -> bool : if will try to convert the string values into numbers ( using the function try_conv_complex )
    delimiter       -> str  : Delimiter that will be used when spliting the strings to be analyzed

  Returns:
    dict of processed values
  '''
  ret = dict(x.split("=") for x in string.split(delimiter))
  if try_conv_number :
    for k,v in ret.items() :
      ret[k] = try_conv_complex(v)
  return(ret)

#######################################################################################################################
def get_config(log_start=False, default_config_file='pq_checklist.conf', config_path:str='') :
  '''
  Function to get current logging and configuration parameters
  Parameters :
    log_start           -> [True,False] : write a message at log file, informing which config file is being used
    default_config_file -> str : Default filename used for checklist files
    config_path         -> str : Specific config file to be loaded ( usefull for debug )

  Returns:
    Two variables:
    config, logger
      config -> configparser object
      logger -> pq_logger object
  '''
  import configparser, os.path, shutil, logging, importlib.util

  if len(config_path) == 0 :
    if importlib.util.find_spec('xdg.BaseDirectory') :
      import xdg.BaseDirectory
      search_path = [ xdg.BaseDirectory.xdg_config_home ]
    elif importlib.util.find_spec('xdg') :
      import xdg
      try :
        search_path = [ str(xdg.XDG_CONFIG_HOME) ]
      except :
        search_path = [ os.getenv('HOME') ]
    else :
      search_path = [ os.getenv('HOME') ]

    search_path = search_path + [ '/etc' , '/opt/freeware/etc' ]
    config_path = None

    for ph in search_path :
      full_path = os.path.join(ph,default_config_file)
      if os.path.exists(full_path) :
        config_path = full_path
        break

  if not config_path :
    new_config_path = os.path.join(search_path[0],default_config_file)
    template_file = os.path.join(os.path.dirname(importlib.util.find_spec('pq_checklist').origin),'pq_checklist.conf.template')
    try :
      shutil.copy(template_file,new_config_path)
      config_path = new_config_path
      debug_post_msg(None, 'Configuration not found at %s, writting new one at %s'%(' '.join(search_path), new_config_path), screen_only=True, flush=True)
    except Exception as e :
      raise SystemError(e)

  config = configparser.ConfigParser()
  if not config_path :
      raise SystemError('No config file could be either located or created, need at least be able to write a new one at %s'%search_path[0])
  else :
    config.read(config_path)

    # Logging configuration
    log_level = logging.INFO
    if config['LOG']['log_level'] == "DEBUG" :
      log_level = logging.DEBUG
    log_file = None
    to_dev_log = True
    if len(config['LOG']['log_file']) > 0 :
      log_file = config['LOG']['log_file']
      to_dev_log = False
    logger = pq_logger(log_level = log_level, stdout = False, name = 'pq_checklist', to_dev_log = to_dev_log, dst_file = log_file)

    if log_start :
      debug_post_msg(logger, 'Using config file: %s'%config_path, screen_only=True, flush=True)

  return(config,logger)

#######################################################################################################################
def main_help() :
  help_text = \
  """Parameters that can be sent through command line:
    -h            # Help Message
    -l <filename> # InfluxDB dumpfile to me loaded ( cannot be used along with -d )
    -d            # Run collector
    -c <filename> # Specific config file """
  print(help_text)
  return(0)


#######################################################################################################################
def main() -> int:
  '''
  Entry point for the checklist program
  '''
  from .general_collector import loop
  import sys, getopt

  ret = -1
  file_to_load = ''
  config_file = ''
  run_loop = False

  if len(sys.argv) < 2 :
    sys.exit(main_help())
  else :
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hl:dc:")
    except getopt.GetoptError:
      sys.exit(main_help())
    for opt, arg in opts:
      if opt == '-h':
        sys.exit(main_help())
      elif opt == "-l" :
        file_to_load = arg
      elif opt == "-c" :
        config_file = arg
      elif opt == "-d" :
        run_loop = True

  if run_loop and len(file_to_load) == 0 :
    ret = loop(config_file)
  elif len(file_to_load) > 0 :
    from db_client import load_file as db_client_load_file
    ret = db_client_load_file(file_to_load,config_file)
  return(ret)

if __name__ == '__main__' :
  main()
