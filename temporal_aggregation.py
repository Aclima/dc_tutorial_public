# Example script that temporally aggregates the concentrations for a given location with a customized buffer
import pandas as pd
import os
import geopandas as gpd
import matplotlib.pyplot as plt


#===============User Inputs===============
# pollutant
pollutant = "CarbonDioxide"  # this has to match the pollutant name in the filename
# set up a location for time aggregation
target_lat_lon = [[38.86494420455321], [-76.98468923536171]]  # Example of latitude and longitude of Anacostia Elementary Campus
# set up a radius from the target lat lon in meters
radius = 250  # in meters
#=============End of User Inputs===========
# set up output directory
output_dir = r"./output_temporal_aggregate"
os.makedirs(output_dir, exist_ok=True)
# set up input directories
input_concentration_dir = r"./conc_dir"
# projection
crs_utm = "EPSG:26918"  # EPSG number for UTM zone 18N, this is the UTM zone that DC is in. This measure of this projection is in meters because the radius is in meters.
crs_data = "EPSG:4326"  # EPSG number for WGS84
# convert the location to a geopandas dataframe
target_point = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x=target_lat_lon[1], y=target_lat_lon[0], crs=crs_data))
# convert to utm to construct a buffer in meters
target_point = target_point.to_crs(crs_utm)
# construct a buffer (size based on radius) around the point
target_point_buffer = gpd.GeoDataFrame(geometry=target_point.buffer(radius))

# read input concentration file
input_file = os.path.join(input_concentration_dir, f'dc_{pollutant}_example.csv')
input_data = pd.read_csv(input_file)
input_data['timestamp_utc'] = pd.to_datetime(input_data['timestamp_utc'])  #convert time stamp to date time object
# convert the input data to a geopandas dataframe
input_data_gpd = gpd.GeoDataFrame(input_data,
                                  crs=crs_data,
                                  geometry=gpd.points_from_xy(input_data['lon'], input_data['lat']))
input_data_gpd_utm = input_data_gpd.to_crs(crs=crs_utm)  # convert to utm
# spatial join the buffer and the concentration data, use right join to only keep the concentration data in the buffer
joined_data = input_data_gpd_utm.sjoin(target_point_buffer, how='right')
# determine the temporal resolution for the aggregation, this example shows daily aggregation
joined_data['date'] = joined_data['timestamp_utc'].dt.date  # generate a date column in the geo dataframe
temporal_aggregated = joined_data[['date', 'avg_value', 'geometry']]  # keep only needed parameters
# average the concentration to each date
temporal_aggregated = temporal_aggregated.dissolve(by='date', aggfunc='mean')
# save the temporally aggregated concentrations to files.
# save spatially aggregated file to a shapefile
temporal_aggregated.to_file(os.path.join(output_dir, f"temporal_aggregate_example_{pollutant}.shp"))
# save spatially aggregated file to a geojson file
temporal_aggregated.to_file(os.path.join(output_dir, f"temporal_aggregate_example_{pollutant}.geojson"), driver='GeoJSON')
# save spatially aggregated file to a csv
temporal_aggregated.to_csv(os.path.join(output_dir, f"temporal_aggregate_example_{pollutant}.csv"))
# create a pandas dataframe for plotting
plot_data = temporal_aggregated[['avg_value']]
# plot time series
fig, ax = plt.subplots(figsize=(12, 9))
plot_data.plot(ax=ax)
plt.savefig('timeseries_plot.png', bbox_inches='tight')