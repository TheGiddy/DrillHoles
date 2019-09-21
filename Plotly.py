import plotly
import plotly.graph_objs as go
from pyproj import Proj
import pandas as pd
import os
import numpy as np


by_zone = True
data_path = os.getcwd()
csv_path = os.path.join(data_path, 'GGI_Assays.csv')
figure_path = os.path.join(data_path, 'GGI_Assays.html')
width = 0.5
zones = []
empty_colour = '#FF0022'


# Colour data, first value is low end of nickel percent range, second value is high, third value is hex colour code
blue_swatch = [[0.5, 1.5, '#D0E6F3'],
               [1.51, 3.0, '#8BC2E2'],
               [3.01, 4.5, '#459DD1'],
               [4.51, 6.0, '#0079C1'],
               [6.01, 7.5, '#00598D'],
               [7.51, 9.0, '#003758'],
               [9.01, 100, '#001624']]

red_swatch = [[0.5, 1.5, '#99525A'],
               [1.51, 3.0, '#802731'],
               [3.01, 4.5, '#6A111B'],
               [4.51, 6.0, '#550E16'],
               [6.01, 7.5, '#400A10'],
               [7.51, 9.0, '#2B070B'],
               [9.01, 100, '#160406']]

colour_data = red_swatch

df_colour = pd.DataFrame(colour_data, columns=['low_r', 'high_r', 'colour'])

# Loads data from csv to pandas df
df = pd.read_csv(csv_path)

# Converts northing and easting to lat/lon
myProj = Proj("+proj=utm +zone=9V, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
lon, lat = myProj(df['Easting'].values, df['Northing'].values, inverse=True)

df['Lat'] = lat
df['Lon'] = lon

# Convert angles to radians
df['LatRad'] = np.deg2rad(df['Lat'])
df['LonRad'] = np.deg2rad(df['Lon'])
df['AzRad'] = np.deg2rad(df['Azimuth'])
df['DipRad'] = np.deg2rad(df['Dip'])

# Convert to cartesian coordinates for easier graphing
# gets hole start
df['holeStartX'] = df['Elevation'] * np.cos(df['LatRad']) * np.cos(df['LonRad'])
df['holeStartY'] = df['Elevation'] * np.cos(df['LatRad']) * np.sin(df['LonRad'])
df['holeStartZ'] = df['Elevation'] * np.sin(df['LatRad'])

# gets hole deltas
df['holeDX'] = df['Length'] * np.sin(df['AzRad']) * np.cos(df['DipRad'])
df['holeDY'] = df['Length'] * np.cos(df['AzRad']) * np.cos(df['DipRad'])
df['holeDZ'] = df['Length'] * np.sin(df['DipRad'])

# gets hole end adding deltas to start
df['holeEndX'] = df['holeStartX'] + df['holeDX']
df['holeEndY'] = df['holeStartY'] + df['holeDY']
df['holeEndZ'] = df['holeStartZ'] + df['holeDZ']

# gets interval start deltas, this is distance of the starting point of each interval in x, y, z
df['intervalStartDX'] = df['IntervalStart'] * np.sin(df['AzRad']) * np.cos(df['DipRad'])
df['intervalStartDY'] = df['IntervalStart'] * np.cos(df['AzRad']) * np.cos(df['DipRad'])
df['intervalStartDZ'] = df['IntervalStart'] * np.sin(df['DipRad'])

# gets interval start by adding interval delta to hole start
df['intervalStartX'] = df['holeStartX'] + df['intervalStartDX']
df['intervalStartY'] = df['holeStartY'] + df['intervalStartDY']
df['intervalStartZ'] = df['holeStartZ'] + df['intervalStartDZ']

# gets interval end deltas
df['intervalEndDX'] = df['IntervalEnd'] * np.sin(df['AzRad']) * np.cos(df['DipRad'])
df['intervalEndDY'] = df['IntervalEnd'] * np.cos(df['AzRad']) * np.cos(df['DipRad'])
df['intervalEndDZ'] = df['IntervalEnd'] * np.sin(df['DipRad'])

# gets interval end coordinates, adding end deltas to start
df['intervalEndX'] = df['holeStartX'] + df['intervalEndDX']
df['intervalEndY'] = df['holeStartY'] + df['intervalEndDY']
df['intervalEndZ'] = df['holeStartZ'] + df['intervalEndDZ']


# create plotly figure
fig = go.Figure()

count = 0
prev_hole = ''
for index, row in df.iterrows():

    try:
        colour = df_colour.loc[(df_colour['low_r'] < row.NiEq) & (df_colour['high_r'] > row.NiEq)].colour.item()
    except ValueError:
        pass

    # for first iteration add total hole length
    if row.Hole != prev_hole:
        prev_hole = row.Hole

        # add the start of the hole
        fig.add_trace(go.Scatter3d(x=[row.holeStartX],
                                   y=[row.holeStartY],
                                   z=[row.holeStartZ],
                                   name=row.Hole,
                                   legendgroup=row.Hole,
                                   hoverinfo='text',
                                   hovertemplate='{0}<extra>{1}m - ({2})</extra>'.format(row.Hole, row.Length, row.Zone)))

        # add line representing total hole length
        fig.add_trace(go.Scatter3d(x=[row.holeStartX, row.holeEndX],
                                   y=[row.holeStartY, row.holeEndY],
                                   z=[row.holeStartZ, row.holeEndZ],
                                   legendgroup=row.Hole,
                                   mode='lines',
                                   showlegend=False,
                                   name=row.Hole,
                                   line={'color': 'black',
                                         'width': 2},
                                   hoverinfo='text',
                                   hovertemplate='{0}<extra>{1}m - ({2})</extra>'.format(row.Hole, row.Length, row.Zone)))

    # if current interval NiEq over 0.5 we plot it (there is nothing lower than .5, this is just cut off as exploration holes have no intervals to plot)
    if row.NiEq > 0.5:
        # Add interval plot. Is just a thick line as plotly doesn't have 3d cylinders.
        fig.add_trace(go.Scatter3d(x=[row.intervalStartX, row.intervalEndX],
                                   y=[row.intervalStartY, row.intervalEndY],
                                   z=[row.intervalStartZ, row.intervalEndZ],
                                   legendgroup=row.Hole,
                                   mode='lines',
                                   showlegend=False,
                                   name=row.Hole,
                                   line={'color': colour,
                                         'width': 15},
                                   hoverinfo='text',
                                   hovertemplate='{0}<extra>{1}m - ({2}%)</extra>'.format(row.Hole, row.Over, row.NiEq)))
    # print(row)
    # print('{0}: Lat:{1} Lon:{2}'.format(row.Hole, row.Lat, row.Lon))

# saves offline version of plot as html file
plotly.offline.plot(fig, filename=figure_path, auto_open=False)

# uncomment below if you want figure to render right away (can be slow if graphics card sucks)
# fig.show()