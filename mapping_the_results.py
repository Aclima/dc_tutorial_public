import geopandas as gpd
import os
import matplotlib.pyplot as plt
import contextily as cx


# set up the shapefile
#input_file = "./output_spatial_aggregate/spatial_aggregate_example_CarbonDioxide_2024_08_13_00_00_00_2024_08_14_00_00_00.shp"  # this is the block level shapefile
input_file = "./output_spatial_aggregate/spatial_aggregate_example_hexagon_CarbonDioxide_2024_08_13_00_00_00_2024_08_14_00_00_00.shp"  # this is the hexagonal grid shapefile
polygon_average = gpd.read_file(input_file)
crs_map = "EPSG:3857"  # EPSG number for Web Mercator (open street map). We're using the open street map as the background so we need to convert the projection to the same projection as the open street map
polygon_average = polygon_average.to_crs(crs=crs_map)  # convert to the projection of open street map
# plot
fig, ax = plt.subplots(figsize=(12, 9))  # set up figure size
polygon_average.plot(column='avg_value', legend=True, ax=ax, vmin=350, vmax=800, cmap='viridis_r', alpha=0.5,
                     missing_kwds={"color": 'lightgrey'})  # plot the geo dataframe
cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)  # add open street map in the background
plt.savefig(f'{os.path.basename(input_file).split('.')[0]}.png', bbox_inches='tight')  # save the figure
plt.close()



