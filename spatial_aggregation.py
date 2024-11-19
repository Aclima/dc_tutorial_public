# Example, pick a time window then aggregate the data to polygons provided as an input
import pytz
import geopandas as gpd
import pandas as pd
import os
import datetime as dt


##=============User input=============
# pollutant
pollutant = "CarbonDioxide"  # This needs to be the same as the pollutant name in the file name
# set up the time window for aggregation
target_begin_datetime = "2024/08/13 00:00:00"  # Use this format: "%YYYY/%mm/%dd %HH:%MM:%SS"
target_end_datetime = "2024/8/14 00:00:00"  # Use this format: "%YYYY/%mm/%dd %HH:%MM:%SS"
##========End of user input===========
# projection
crs_data = "EPSG:4326"  # EPSG number for WGS84
# convert to datetime object, use utc because data column says utc
target_begin_datetime_obj = pytz.utc.localize(dt.datetime.strptime(target_begin_datetime, '%Y/%m/%d %H:%M:%S'))
target_end_datetime_obj = pytz.utc.localize(dt.datetime.strptime(target_end_datetime, '%Y/%m/%d %H:%M:%S'))
# set up input directories
input_concentration_dir = r"./conc_dir"
input_shapefile_dir = r"./Census_Blocks_in_2020"
# set up output directory
output_dir = r"./output_spatial_aggregate"
os.makedirs(output_dir, exist_ok=True)  # create the directory
# read the shapefile with polygons where the concentrations will be aggregated to
input_polygon_file = os.path.join(input_shapefile_dir, 'Census_Blocks_in_2020.shp')
input_polygon_gpd = gpd.read_file(input_polygon_file)
input_polygon_gpd = input_polygon_gpd[['OBJECTID', 'BLKGRP', 'BLOCK', 'GEOID', 'geometry']]  # keep only needed columns
input_polygon_gpd = input_polygon_gpd.to_crs(crs=crs_data)  # convert the polygon projection to the same projection as the concentration
# read input concentration file
input_file = os.path.join(input_concentration_dir, f'dc_{pollutant}_example.csv')  # this could change if the filename of the concentration data is different
input_data = pd.read_csv(input_file)
input_data['timestamp_utc'] = pd.to_datetime(input_data['timestamp_utc'])  #convert time stamp to date time
# keep data for the target time window
input_data = input_data[(input_data['timestamp_utc'] >= target_begin_datetime_obj) &
                        (input_data['timestamp_utc'] <= target_end_datetime_obj)]
# sort the data, not necessary but would be easier to view
input_data = input_data.sort_values(by=['timestamp_utc', 'device_id'])
# convert the input data to a geopandas dataframe
input_data_gpd = gpd.GeoDataFrame(input_data,
                                  crs=crs_data,
                                  geometry=gpd.points_from_xy(input_data['lon'], input_data['lat']))
# spatial join the concentration data to the polygon
joined_data_gpd = gpd.sjoin(left_df=input_polygon_gpd, right_df=input_data_gpd, how='left')
# calculate polygon average concentrations
polygon_conc = joined_data_gpd[['GEOID', 'geometry', 'avg_value']]
polygon_average = polygon_conc.dissolve(by='GEOID', aggfunc='mean')
## Saving data
# save spatially aggregated file to a shapefile
polygon_average.to_file(os.path.join(output_dir, f"spatial_aggregate_example_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.shp"))
# save spatially aggregated file to a geojson file
polygon_average.to_file(os.path.join(output_dir, f"spatial_aggregate_example_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.geojson"), driver='GeoJSON')
# save spatially aggregated file to a csv
polygon_average.to_csv(os.path.join(output_dir, f"spatial_aggregate_example_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.csv"))
