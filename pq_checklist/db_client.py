from . import debug_post_msg, get_config
import json, importlib, os.path
from . import load_file as load_query_file
import datetime
#######################################################################################################################

def load_file(file_to_load,config_file) :
  '''
  main loop that will refresh
  '''
  ret = 2
  if len(config_file) > 0 :
    config,logger = get_config(log_start=False, config_path=config_file)
  else :
    config,logger = get_config(log_start=False)

  with db_client(config,logger) as db :
    if db.write_from_file(file_to_load) :
      ret = 0

  return(ret)


#######################################################################################################################
#######################################################################################################################
class db_client() :
  def __init__(self, config = None, logger = None, auto_connect:bool=True) :
    '''
    Class to handle write off data into databases or dump-files

    Parameters :
        config       -> obj  : config object
        logger       -> obj  : pq_logger object
        auto_connect -> bool : Auto connect to the database
    '''
    self.config = config
    self.logger = logger
    self.auto_connect = auto_connect
    self.db, self.db_write_api, self.query_api, self.output_file = None, None, None, None
    self.query_dir      = os.path.join(os.path.dirname(os.path.abspath(__file__)),"flux")


    if auto_connect :
      self.connect()
    return(None)

#######################################################################################################################
  def __enter__(self) :
    if self.auto_connect :
      self.connect()
    return(self)
#######################################################################################################################

  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.disconnect()
    return(None)

#######################################################################################################################
  def disconnect(self) :
    if self.output_file :
      self.output_file.close()

    if self.db_write_api :
      self.db_write_api.close()

    return(None)

#######################################################################################################################
  def connect(self) :
    '''
    Connect to the database using directives defined into the config file

    Returns:
       Bool -> True,False  If some kind of connection or write off mech have been defined
    '''
    if importlib.util.find_spec('influxdb_client') is not None and self.config['INFLUXDB']['url'] != "<influxdb_url>" and len(self.config['INFLUXDB']['url']) > 0 :
      from influxdb_client import InfluxDBClient, Point, WritePrecision
      try :
        self.db = InfluxDBClient(**dict(self.config.items('INFLUXDB')))

      except Exception as e :
        debug_post_msg(self.logger,'Error connecting to influxDB: %s'%e)
    if self.logger.getEffectiveLevel() <= 10  and len(self.config['INFLUXDB']['dump_file']) :
      try :
        self.output_file = open(self.config['INFLUXDB']['dump_file'], 'a+')
      except Exception as e :
        debug_post_msg(self.logger,'Error opening dump file: %s'%e, raise_type=Exception)
      debug_post_msg(self.logger,'InfluxDB not configured or influxdb_client not installed, or loglevel set to debug. Queries will be saved at dumpfile')
    return(None)

#######################################################################################################################
  def delete_measurement(self, measurement,start_date:str='1970-01-01T00:00:00Z', date_end:str='') :
    ret = None
    if self.db :
      delete_api = self.db.delete_api()
      if len(date_end) == 0 :
        date_end = datetime.datetime.utcnow().isoformat()
      ret = delete_api.delete(start_date, '2020-04-27T00:00:00Z', '_measurement="%s"'%measurement, bucket=self.config['INFLUXDB']['bucket'], org=self.config['INFLUXDB']['org'])
    return(ret)


#######################################################################################################################
  def write_from_file(self, filename:str) -> bool :
    '''
    Load data from file and write into the influxdb

    Parameters :
      filename : str -> filename to be loaded, in order to write into the InfluxDB

    Returns :
      bool -> [True,False]
    '''
    ret = False
    try :
      with open(filename, 'r') as fptr :
        lst_of_messages = json.load(fptr)
        ret = self.write(lst_of_messages)
    except Exception as e :
      debug_post_msg(self.logger, 'Error writing data from file : %s'%e, raise_type=Exception)
    return(ret)

#######################################################################################################################
  def query(self,measurement,start_date:str='1970-01-01T00:00:00Z', date_end:str='', yield_function:str="nonnegative derivative") :
    ret = []
    if self.db :
      self.db_query_api = self.db.query_api()

      tgt = os.path.join(self.query_dir,'base_query.flux')
      rep = [ [ '<BUCKET>', self.config['INFLUXDB']['bucket'] ],
              [ '<MEASUREMENT>', measurement ],
              [ '<START_RANGE>', start_date ],
              [ '<STOP_RANGE>', date_end ],
              [ '<YIELD_FUNCTION>', yield_function ]]
      query = load_query_file(self.logger, tgt, rep)

      for table in self.db_query_api.query(org=self.config['INFLUXDB']['org'], query=load_query_file(self.logger, tgt, rep)) :
        for record in table.records:
          ret.append((record.get_field(), record.get_value()))
    return(ret)

#######################################################################################################################
  def write(self,msg:list, dumpfile_only = False, db_only = False) -> bool :
    '''
    Write data into influxdb or dumpfile in order to perform further analysis

    Parameters:
      msg : list -> list of messages that will be written
      dumpfile_only : bool -> write only to the dump file
      db_only : bool -> write only to the database

    Returns:
      bool -> True,False in case it works or not
    '''
    ret = False
    try :
      self.db_write_api = self.db.write_api()
      if self.db_write_api and not dumpfile_only :
        try :
          ret_data = self.db_write_api.write(self.config['INFLUXDB']['bucket'],  self.config['INFLUXDB']['org'], msg)
          if ret_data :
            debug_post_msg(self.logger, 'Unexpected from InfluxDB, something weird might be happening: %s'%str(ret_data))
          self.db_write_api.close()
          ret = True
        except Exception as e :
          debug_post_msg(self.logger, 'Error writing data to influxdb: %s'%e, raise_type=Exception)
      if self.output_file and not db_only :
        try :
          self.output_file.write(json.dumps(msg))
          if not ret and not self.db_write_api :
            ret = True
        except Exception as e :
          debug_post_msg(self.logger, 'Error writing data to dumpfile : %s'%e, raise_type=Exception)
    except Exception as e :
      debug_post_msg(self.logger, 'Error writing data : %s'%e, raise_type=Exception)
    return(ret)
