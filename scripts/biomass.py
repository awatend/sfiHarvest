import json
import time
from pathlib import Path
import csv

# Script for converting biomass CSV files in geoJSON

def save_geojson(csv_file, geojson_file):
    # Read CSV and construct GeoJSON
    features = []
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')  # or ',' depending on your file
        for row in reader:
            if row["lat"].strip().lower() == "lat":
                continue
            lat = float(row["lat"])
            lon = float(row["lon"])
            biomass = float(row["biomass"])

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "biomass": biomass
                }
            }
            features.append(feature)

    geojson_data = {
    "type": "FeatureCollection",
    "features": features
    }

    # Write to GeoJSON file
    with open(geojson_file, "w") as f:
        json.dump(geojson_data, f, indent=2)

    print(f"GeoJSON saved to {geojson_file}")


def save_files_periodically(save_directory,output_file):    
    seen_files = set()
    all_files = sorted(Path(save_directory).glob("*.csv"))
    new_files = [f for f in all_files if f not in seen_files]
    if new_files:
            print(f"[CONCAT] Concatenating {len(new_files)} new files...")
            with open(output_file, "a") as outfile:
                for file_path in new_files:
                    with open(file_path, "r") as infile:
                        outfile.write(infile.read())
                    seen_files.add(file_path)
                    file_path.unlink()
            print(f"[CONCAT] Output saved to {output_file}")
    else:
        print("[CONCAT] No new files to concatenate.")

                
        



if __name__ == "__main__":
    grethe_directory="/home/awa/sfiHarvest/data_sniffing/biomass_files/grethe"
    grethe_file= "/home/awa/sfiHarvest/data_sniffing/biomass_files/grethe/concat/biomass_concat.csv"
    autonaut_directory="/home/awa/sfiHarvest/data_sniffing/biomass_files/autonaut"
    autonaut_file="/home/awa/sfiHarvest/data_sniffing/biomass_files/autonaut/concat/biomass_concat.csv"
    grethe_biomass="/home/awa/sfiHarvest/data_sniffing/gis_data/display/sinmod_models/grethe_biomass.geojson"
    autonaut_biomass= geojson_file = "/home/awa/sfiHarvest/data_sniffing/gis_data/display/sinmod_models/autonaut_biomass.geojson" 
    while True:
        save_files_periodically(grethe_directory,grethe_file)    
        save_files_periodically(autonaut_directory,autonaut_file)
        save_geojson(grethe_file,grethe_biomass )
        save_geojson( autonaut_file,autonaut_biomass)
        time.sleep(3*60)
