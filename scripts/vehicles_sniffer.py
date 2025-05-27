import logging
import sys
from typing import Optional, Tuple, List, Union
from threading import Thread, Event
import time
from datetime import datetime, timezone
import os
import glob
import math
import numpy as np
import pandas as pd
import imcpy
import imcpy.coordinates
from imcpy.actors import DynamicActor
from imcpy.decorators import Periodic, Subscribe
from SSL_Comm_msgs_toolbox import (
    pack_single_message as tpl_pack_single,
    unpack_single_message,
    pack_batch_message as tpl_pack_batch,
)
from WGS import WGS

class vehicle_nav(DynamicActor):
    def __init__(
        self,
        output_dir: Optional[str] = None,
    ):
        super().__init__(imc_id=9876)
        #self.target_driver = "manta-ntnu-1" #

        #self.target_brain = 0x3433
        #self.target_manta = 'manta-ntnu-1'
        self.target_list = ["ntnu-mr-usv","lauv-thor","manta-ntnu-1", "lauv-roald","lauv-simulator-1", "ntnu-autonaut", "ntnu-autonaut2"]#, self.target_driver, self.target_brain, self.target_manta]
        self.heartbeat.extend(self.target_list)

        # Directories
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.update_nav_log_path()

        # Navigation state buffers
        self.state_array_lat_lon = np.empty((0, 4))  # [ID, lat, lon, timestamp]
        self.state_array_x_y = np.empty((0, 3))      # [x, y, timestamp]
        self._operation_started = False
        self.WGS = WGS()

        # Current state
        self._lat = None
        self._lon = None
        self._depth = None
        self._timestamp = None
        self.datetime= None
        self.id= None
        self._x = None
        self._y = None


    def __call__(self):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        self.run()

    def __is_from_target(self, msg):
        try:
            node = self.resolve_node_id(msg)
            if (
                node.sys_name in self.target_list                
            ):
                print(node.sys_name)
                return node
        except KeyError:
            pass
        return False

    @Subscribe(imcpy.EstimatedState)


    def recv_Estate(self, msg: imcpy.EstimatedState):
        '''
        subscribe to state 

        we subscribe from :
        - Grethe
        - manta-ntnu-1    (or the one on flyer)   this is flyer information 
        - AUV (thor / roald) only wehn we are close to wifi
        '''
        node = self.__is_from_target(msg)
        if not node:
            return
        lat, lon, _ = imcpy.coordinates.toWGS84(msg)
        self._lat = lat * 180.0 / math.pi
        self._lon = lon * 180.0 / math.pi
        self._depth = msg.depth
        self.id=node.sys_name
        self._timestamp = round(msg.timestamp)
        self.datetime=datetime.fromtimestamp(msg.timestamp, tz=timezone.utc).strftime('%Y%m%d%H%M%S%Z')
        self._operation_started = True
        self._x, self._y = self.WGS.latlon2xy(self._lat, self._lon)
        self.state_array_lat_lon = np.vstack((
            self.state_array_lat_lon,
            [self.id, self._lat, self._lon, self.datetime]
        ))
        self.state_array_x_y = np.vstack((
            self.state_array_x_y,
            [self._x, self._y, self._timestamp]
        ))

        if self.state_array_x_y.size == 0:
            return
        df = pd.DataFrame(
            self.state_array_lat_lon,
            columns=['vehicle_id','lat', 'long', 'datetime']
        )

        df.to_csv(
            self.nav_log_path,
            mode='a',
            header=not os.path.exists(self.nav_log_path),
            index=False
        )
        self.state_array_x_y = np.empty((0, 3)) 
        self.state_array_lat_lon = np.empty((0, 4)) #clear buffer
    
    ''' 
    def log_state(self):
        """
        Append current navigation buffer to nav_log and clear buffer.
        """
        print("loging ")
        if self.state_array_x_y.size == 0:
            return
        df = pd.DataFrame(
            self.state_array_x_y,
            columns=['x', 'y', 'timestamp']
        )
        print("writing to csv file")
        df.to_csv(
            self.nav_log_path,
            mode='a',
            header=not os.path.exists(self.nav_log_path),
            index=False
        )
        self.state_array_x_y = np.empty((0, 3))
    '''
    def update_nav_log_path(self):
        start_time=datetime.now(timezone.utc)
        nav_log_filename=start_time.strftime('%Y%m%dT%H%M%S%z')+'_vehicles.csv'
        self.nav_log_path = os.path.join(self.output_dir, nav_log_filename)

    @Periodic(60*60)
    def run_periodic(self):
        print("done")
        self.update_nav_log_path()

    
if __name__ == '__main__':
    # csv_dir and output_dir can be passed as command-line arguments
    import argparse 
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='Directory to watch for logs')
    # parser.add_argument(
    #     '--output_dir',
    #     help='Directory to store logs (defaults to csv_dir)',
    #     default=None
    # )
    args = parser.parse_args()
    #basee = "D:/Campaigns/Harvest2025/"
    #data_dir = 
    #nav_dir  = data_dir + "/navigation_log"
    #nav_log_filename=nav_dir  
    handler = vehicle_nav(
        output_dir=args.output_dir
    )
    handler()
