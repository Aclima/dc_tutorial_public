import pytz
import geopandas as gpd
import pandas as pd
import os
import datetime as dt
import h3
import shapely


def create_polygon_wkt_from_hindex(h_index: str) -> str:
    """Input an h3 hexagon h-index value, and return the resultant geometry as a wkt."""
    h_boundary = h3.cell_to_boundary(h_index)  # this returns (lat, lon)
    # shapely.geometry.Polygon needs everything to be in (lon, lat), so let's flip the lat lon
    h_boundary_lon_lat = tuple((x[1], x[0]) for x in h_boundary)
    geom = shapely.geometry.Polygon(h_boundary_lon_lat)
    return geom.wkt


def check_create_polygons(boundary) -> list:
    """check if the boundary is a multipolygon. if so, create polygons for each sub-polygon and save in a list"""
    if isinstance(boundary, shapely.geometry.multipolygon.MultiPolygon):
        # Do each sub-polygon individually to not include the space between
        region_polygons = [poly for poly in boundary.geoms]
    else:
        # just make the region polygon a list to handle conveniently.
        region_polygons = [boundary]
    return region_polygons


def create_hexagon_gdf(polygon_list, hexagon_res, crs) -> gpd.GeoDataFrame:
    total_regions = []
    # loop through the list of polygons
    for polygon in polygon_list:
        # convert polygon to geojson
        poly_geojson = polygon.__geo_interface__
        # Create the h3 hexagons and store them in a pandas dataframe
        hexagons = pd.DataFrame(
            h3.polygon_to_cells(h3.geo_to_h3shape(poly_geojson), res=hexagon_res),
            columns=["hexagons"],
        )
        # Check if this created actual polyongs, if not it's b/c the polygon is too small to fit a hexagon. In that case,
        # return 1 hexagon at the centroid.
        if hexagons.empty:
            hexagons = pd.DataFrame(
                [h3.latlng_to_cell(polygon.centroid.y, polygon.centroid.x, hexagon_res)],
                columns=["hexagons"],
            )
        # create a wkt for the hexagons and use them as the geometry
        hexagons["geometry"] = hexagons["hexagons"].apply(lambda h: create_polygon_wkt_from_hindex(h))
        # create the geometry object form the wkt
        hexagons['geometry'] = hexagons['geometry'].apply(
            lambda geo: shapely.wkt.loads(geo) if isinstance(geo, str) else geo
        )
        # append the hexagon to a list
        total_regions.append(hexagons)
    # concat everything together
    region_hexagons = pd.concat(total_regions)
    region_hexagons["h3_resolution"] = hexagon_res
    # convert to geopandas dataframe
    region_hexagons_gdf = gpd.GeoDataFrame(region_hexagons, crs=crs, geometry='geometry')
    return region_hexagons_gdf

##=============User input=============
# pollutant
pollutant = "CarbonDioxide"  # This needs to be the same as the pollutant name in the file name
# set up the time window for aggregation
target_begin_datetime = "2024/08/13 00:00:00"  # Use this format: "%YYYY/%mm/%dd %HH:%MM:%SS"
target_end_datetime = "2024/8/14 00:00:00"  # Use this format: "%YYYY/%mm/%dd %HH:%MM:%SS"
# hexagon resolution
hexagon_res = 9
##========End of user input===========
# DC geojson file
dc_boundary = gpd.read_file('Washington_DC_Boundary.geojson')
# convert the geometry to wkt
dc_boundary_wkt = dc_boundary.to_wkt()['geometry'].iloc[0]
# projection
crs_data = "EPSG:4326"  # EPSG number for WGS84
# convert to datetime object, use utc because data column says utc
target_begin_datetime_obj = pytz.utc.localize(dt.datetime.strptime(target_begin_datetime, '%Y/%m/%d %H:%M:%S'))
target_end_datetime_obj = pytz.utc.localize(dt.datetime.strptime(target_end_datetime, '%Y/%m/%d %H:%M:%S'))
# set up input directories
input_concentration_dir = r"./conc_dir"
# set up output directory
output_dir = r"./output_spatial_aggregate"
os.makedirs(output_dir, exist_ok=True)  # create the directory
# read the DC boundary wkt
boundary = shapely.wkt.loads(dc_boundary_wkt)
# if the boundary is a multipolygon, need to break them up to create a list of individual polygon
region_polygons = check_create_polygons(boundary=boundary)
# create hexagons within the region polygons and generate a geopandas dataframe
region_hexagons_gdf = create_hexagon_gdf(polygon_list=region_polygons, hexagon_res=hexagon_res, crs=crs_data)
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

# spatial join the concentration data to the hexagons,
joined_data_gpd = gpd.sjoin(left_df=region_hexagons_gdf, right_df=input_data_gpd, how='left')
# calculate hexagon average concentrations
polygon_conc = joined_data_gpd[['hexagons', 'geometry', 'avg_value']]
polygon_average = polygon_conc.dissolve(by='hexagons', aggfunc='mean')
# drop the polygons without data
polygon_average = polygon_average.dropna(subset=['avg_value'])
## Saving data
# save spatially aggregated file to a shapefile
polygon_average.to_file(os.path.join(output_dir, f"spatial_aggregate_example_hexagon_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.shp"))
# save spatially aggregated file to a geojson file
polygon_average.to_file(os.path.join(output_dir, f"spatial_aggregate_example_hexagon_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.geojson"), driver='GeoJSON')
# save spatially aggregated file to a csv
polygon_average.to_csv(os.path.join(output_dir, f"spatial_aggregate_example_hexagon_{pollutant}_{target_begin_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}_{target_end_datetime_obj.strftime('%Y_%m_%d_%H_%M_%S')}.csv"))
