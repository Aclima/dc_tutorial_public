import pandas as pd
import os
from scipy.signal import find_peaks

# set up path
input_path_spatial = r"./output_spatial_aggregate"
input_path_temporal = r"./output_temporal_aggregate"
# set up file name
input_spatial_file = os.path.join(input_path_spatial,
                                  'spatial_aggregate_example_CarbonDioxide_2024_08_13_00_00_00_2024_08_14_00_00_00.csv')
input_temporal_file = os.path.join(input_path_temporal, 'temporal_aggregate_example_CarbonDioxide.csv')
# read files
input_spatial_data = pd.read_csv(input_spatial_file)
input_temporal_data = pd.read_csv(input_temporal_file)
# Method 1: sort the concentration by values
ranked_spatial_data = input_spatial_data.sort_values(by='avg_value', ascending=False)
ranked_temporal_data = input_temporal_data.sort_values(by='avg_value', ascending=False)
# Method 2, for the temporal data, use the find_peaks() function
peak_loc = find_peaks(input_temporal_data['avg_value'])
peak_data = input_temporal_data.iloc[peak_loc[0]]