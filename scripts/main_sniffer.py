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
import geopandas as gpd
import json
from shapely.geometry import Point, LineString
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
        super().__init__(imc_id=9711)
        #self.target_driver = "manta-ntnu-1" #

        #self.target_brain = 0x3433
        #self.target_manta = 'manta-ntnu-1'
        self.target_list = ["ntnu-mr-usv","lauv-thor","ntnu-autonaut","ntnu-autonaut2","manta-ntnu-1", "lauv-simulator-1", "lauv-roald"]# vehicles to subscribe to 
        self.heartbeat.extend(self.target_list)

        # Directories
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Navigation state buffers
        self.state_array_lat_lon = np.empty((0, 3))  # [lat, lon, timestamp]
        self.coords_dict = {}
        self.state_array_x_y = np.empty((0, 3))      # [x, y, timestamp]
        self._operation_started = False
        self.WGS = WGS()

        # Current state
        self._lat = None
        self._lon = None
        self._depth = None
        self._timestamp = None
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
        self._id=node.sys_name
        self._timestamp = round(msg.timestamp)
        self._operation_started = True
        self._x, self._y = self.WGS.latlon2xy(self._lat, self._lon)
        
        self.state_array_x_y = np.vstack((
            self.state_array_x_y,
            [self._x, self._y, self._timestamp]
        ))

        if self.state_array_x_y.size == 0:
            return
        new_coord = [ self._lon,self._lat, self._depth]
        

        # Append coordinate to th vehicle's list
        if self._id not in self.coords_dict:
            self.coords_dict[self._id] = []
        self.coords_dict[self._id].append(new_coord)
        
    

    def log_data(self):
        # More convenient to use the usual names
        name_map = {
        'lauv-thor': 'Thor',
        'lauv-roald': 'Roald',
        'ntnu-mr-usv': 'Grethe',
        'manta-ntnu-1': 'Flyer',


        }
        # File to display on ArcGIS
        for name, coors in self.coords_dict.items():
            vehicle_name = name_map.get(name, name.title())
            vehicle_folder = os.path.join(self.output_dir, 'display')
            #print("folder",vehicle_folder)
            os.makedirs(vehicle_folder, exist_ok=True)
            current_time=datetime.now(timezone.utc)
            geojson_path = os.path.join(vehicle_folder,f"{name}.geojson")    
            
            geojson ={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coors
                        },
                        "properties": {
                            "name": vehicle_name,
                            "description": "vehicle navigation log, SFI Harvest 2025"
                        }
                    }
                            ]
                }
            with open(geojson_path, 'w') as f:
                json.dump(geojson,f,indent=4)

    # long term storage
    def log_data_storage(self):
        # Construct GeoJSON path per vehicle
        for name, coors in self.coords_dict.items():
            vehicle_folder = os.path.join(self.output_dir, name)
            #print("long term folder",vehicle_folder)
            os.makedirs(vehicle_folder, exist_ok=True)
            current_time=datetime.now(timezone.utc)
            geojson_path = os.path.join(vehicle_folder, f"{current_time.strftime('%Y%m%d%H%M%S')}_{name}.geojson")
            
            
            geojson ={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coors
                        },
                        "properties": {
                            "name": name,
                            "description": "vehicle navigation log, SFI Harvest 2025"
                        }
                    }
                            ]
                }
            with open(geojson_path, 'w') as f:
                json.dump(geojson,f,indent=4)

                     
    @Periodic(60*3)
    def run_periodic(self):
        print("executed")
        self.log_data()
'''
    @Periodic(5*60*60)
    def run_periodic_data(self):
        print("executed")
        self.log_data_storage()
'''
    
if __name__ == '__main__':
    #output_dir should be passed as command-line arguments
    import argparse 
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='Directory to watch for logs')
    args = parser.parse_args()
    handler = vehicle_nav(
        output_dir=args.output_dir
    )
    handler()
