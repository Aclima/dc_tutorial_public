# This repository contains scripts provided to used for the DC DOEE project for their potential analysis needs

## Environment set up
Use the requirements.txt file to generate a virtual environment to run these codes. 

With pyenv:
```
pyenv virtualenv 3.12.2 <name_of_virtual_environment>
pyenv activate <name_of_virtual_environment>
pip install -r requirements.txt
```

With conda:
```
conda create --name <name_of_virtual_environment> --file requirements.txt
```

## Description

An example concentration file is needed to execute these codes. The size of the example file is too big to be pushed to github so will be shared through other means such as google drive

***spatial_aggregation.py***:\
Aggregates the hyperlocal concentration to census blocks

***spatial_aggregation_hexagonal_grids.py***:\
Aggregates the hyperlocal concentration to hexagonal grids

***temporal_aggregation.py***:\
Aggregates the hyperlocal concentration to daily level

***mapping_the_results.py***:\
Map the spatially aggregated concentrations

***identify_hotspots.py***:\
Identify the hotspots spatially and temporally 
