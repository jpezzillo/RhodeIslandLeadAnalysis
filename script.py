# -*- coding: utf-8 -*-
"""
@author: Jesse Pezzillo
@description: This script leverages the google maps 'places' api to generate
lat + long of schools with high lead levels. Using this data, the script
plots the schools in the state given. 
This program seeks to visualize schools that were opened before 1982 as 
lead pipes were banned form new plubming systems starting in 1986. 
"""

# import packages
# google maps package from  https://github.com/googlemaps/google-maps-services-python/tree/master/googlemaps
# geopandas install setup here: http://geopandas.org/install.html 
# I recommend using anaconda distribution for ease of install
# plot tutorial here = https://towardsdatascience.com/geopandas-101-plot-any-data-with-a-latitude-and-longitude-on-a-map-98e01944b972
import googlemaps
import pandas as pd
import geopandas as gpd
import descartes
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

# set client key - place google key obtained in google map api console
# key manager recommended for production implementation
gmaps = googlemaps.Client(key='',retry_timeout=2)

''' create function to lookup latitude and longitude 
    uses 0 index to return first result in list. 
    First result is most reliable return from google.
'''
def lookupCoord(location):
    try:
        location = str(location)
        result = googlemaps.places.places(client=gmaps, query=location,type='school', region='northeast')
        resultlat = result['results'][0]['geometry']['location']['lat']
        resultlng = result['results'][0]['geometry']['location']['lng']
        resultReturn = str(resultlat) + ',' + str(resultlng)
    except:
        resultReturn = 'NotFound'
    return resultReturn

''' take in list of schools in RI to 
    create a reference table of all RI schools
    with supplemental information 
    source: http://www.ride.ri.gov/FundingFinance/
    SchoolBuildingAuthority/FacilityDataInformation
    /FacilitiesMap.aspx
'''
# remove and format columns, set index 
reference_table = pd.read_excel('RIDESchools.xlsx')
reference_table.index = reference_table['School Name']
reference_table = reference_table.drop(columns=['Info','InfoWorks!'])


''' for each school on the reference table
    lookup latitude, longitude, and formatted address 
'''
# create row used for lookup with School Name + Town to avoid lookup errors
reference_table['Lookup'] = (reference_table['School Name'] + ', ' +  reference_table['City'] + ' Rhode Island')                                             

# loop and add result to a list
coordinates = []
for row in reference_table['Lookup']:
    lookup = lookupCoord(row)
    coordinates.append(lookup)
reference_table['coordinates'] = coordinates

''' Data cleaning section
    This part formats the dataframe for use
'''
# convert lat and longitude to separate column and drop coordinates column
ref = reference_table['coordinates'].str.split(',', n=1, expand = True)
reference_table['lat'] = ref[0]
reference_table['long'] = ref[1]
reference_table.drop(columns=["coordinates"], inplace = True)
#convert lat and long to numbers
reference_table['lat'] = reference_table['lat'].astype(float)
reference_table['long'] = reference_table['long'].astype(float)

#rename year opened column with underscore
reference_table.rename(columns={'Year Opened':'Year_Opened'}, inplace=True)
#drop rows where year is > 1986
reference_table = reference_table.drop(reference_table[reference_table.Year_Opened >= 1986].index)
'''This section actually plots the
    schools that are at risk for lead issues
'''
# create plot using shapefile downloaded from 
# http://www.rigis.org/datasets/state-boundary-1989
# tutorial found here: https://towardsdatascience.com/
# geopandas-101-plot-any-data-with-a-latitude-and-longitude-on-a-map-98e01944b972
myMap = gpd.read_file('State_Boundary_1989.shp')
fig,ax = plt.subplots(figsize = (15,15))
myMap.plot(ax=ax)
crs = {'init':'epsg:4236'}

# create points and set in a value called geometry, then create DF joning ref table and geometry
geometry = [Point(xy) for xy in zip( reference_table['long'], reference_table['lat'])]
geometry[:3]
geo_df = gpd.GeoDataFrame(reference_table, crs=crs, geometry = geometry)

# plot points on map
fig,ax = plt.subplots(figsize = (15,15))
myMap.plot(ax=ax, alpha = 0.4, color='grey')
geo_df.plot(ax=ax, markersize=20, color ='red', marker ='o')
