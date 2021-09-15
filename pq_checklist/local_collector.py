from . import pq_logger, debug_post_msg, conv_bash_var_to_dict, net_collector, cpu_collector
import importlib,json
from datetime import datetime

def __pq_main_loop__() :
  from . import get_config
  import time
  config,logger = get_config(log_start=False)
  coll_class = collector(config = config, logger = logger)
  while True :
    coll_class.collect_all()
    time.sleep(int(config['LOOP']['interval']))

  return(None)


def loop() :
  from multiprocessing import Process
  p = Process(target=__pq_main_loop__)
  p.start()
  return(p)


class collector :
  def __init__(self, config = None, logger = None ) :
    self.rundir = '/tmp'
    self.config = config
    self.logger = logger

    # Load influxdb connection directives
    if importlib.util.find_spec('influxdb_client') is not None and self.config['INFLUXDB']['url'] != "<influxdb_url>" and len(self.config['INFLUXDB']['url']) > 0 :
      from influxdb_client import InfluxDBClient, Point, WritePrecision
      try :
        self.db = InfluxDBClient(**dict(config.items('INFLUXDB')))
        self.db_write_api = self.db.write_api()
      except Exception as e :
        self.db, self.db_write_api = None, None
        debug_post_msg(self.logger,'Error connecting to influxDB: %s'%e, err= True)
    else :
      self.db, self.db_write_api = None, None
      debug_post_msg(self.logger,'InfluxDB not configured or influxdb_client not installed, queries will be saved at dumpfile', err=True)

    # Load collectors
    self.net_collector = net_collector.collector(config = config, logger = logger)
    self.cpu_collector = cpu_collector.collector(config = config, logger = logger)
    self.collectors    = ( self.net_collector, self.cpu_collector )
    debug_post_msg(self.logger,'Starting local collector', err= False)
    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)


  def collect_all(self, debug=False) :
    from time import time
    st = time()
    data = []
    for measurement_povider in self.collectors :
      data += measurement_povider.get_latest_measurements(debug = debug)

    if self.db_write_api :
      try :
        self.db_write_api.write(self.config['INFLUXDB']['bucket'],  self.config['INFLUXDB']['org'], data)
      except Exception as e :
        debug_post_msg(self.logger, 'Error writing data to influxdb: %s'%e, err=True)
    if len(self.config['INFLUXDB']['dump_file']) > 0 and ( not self.db_write_api or debug ) :
      with open(self.config['INFLUXDB']['dump_file'], 'a+') as fptr :
        fptr.write(json.dumps(data))
    duration = time() - st
    debug_post_msg(self.logger,'Collect Task Duration: %d seconds'%int(duration), err= False)

    return(None)
