import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
from io import StringIO
import pydeck as pdk
from shapely.geometry import shape, Polygon


# Download the CSV file
url = 'https://www.wien.gv.at/gogv/l9ogdviebezbiztecveh2002f'
@st.cache_data
def load_data(url):
    data = pd.read_csv(url, sep=';', header=1, decimal=',', thousands='.')
    return data

csv_data = load_data(url)

# App title
st.title('District Data Plotter')

# # Upload CSV file
# uploaded_file = st.file_uploader('Choose a CSV file', type='csv')
#
# if uploaded_file:
#     csv_data = pd.read_csv(uploaded_file, sep=';', header=1, decimal=',')

# Change DISCTRICT_CODE to 4 numbers:

csv_data = csv_data.assign(DISTRICT = csv_data['DISTRICT_CODE'].astype(str).str.slice(start=1, stop=5).astype(int))

# Dropdown for selecting value
value_options = list(csv_data.columns[5:-1])
selected_value = st.selectbox('Select a value to plot:', value_options)

# Map short codes to long titles
title_mapping = {
    'PKW_VALUE': 'Zugelassene Kraftfahrzeuge - Personenkraftwagen (inkl. Autotaxi)',
    'BUS_VALUE': 'Zugelassene Kraftfahrzeuge - Omnibusse',
    'LKW_VALUE': 'Zugelassene Kraftfahrzeuge - Lastkraftwagen',
    'TRA_VALUE': 'Zugelassene Kraftfahrzeuge - Zugmaschinen und Traktoren',
    'OTH_VALUE': 'Zugelassene Kraftfahrzeuge - Sonstige Kraftfahrzeuge',
    'BIK_VALUE': 'Zugelassene Kraftfahrzeuge - Krafträder',
    'PKW_DENSITY': 'Zugelassene Kraftfahrzeuge - Personenkraftwagen (inkl. Autotaxi) pro 1.000 EinwohnerInnen',
    'BUS_DENSITY': 'Zugelassene Kraftfahrzeuge - Omnibusse pro 1.000 EinwohnerInnen',
    'LKW_DENSITY': 'Zugelassene Kraftfahrzeuge - Lastkraftwagen pro 1.000 EinwohnerInnen',
    'TRA_DENSITY': 'Zugelassene Kraftfahrzeuge - Zugmaschinen und Traktoren pro 1.000 EinwohnerInnen',
    'OTH_DENSITY': 'Zugelassene Kraftfahrzeuge - Sonstige Kraftfahrzeuge pro 1.000 EinwohnerInnen',
    'BIK_DENSITY': 'Zugelassene Kraftfahrzeuge - Krafträder pro 1.000 EinwohnerInnen'
}

# Display the long title according to the selected_value
st.header(title_mapping[selected_value][:26])
st.subheader(title_mapping[selected_value][28:])
# get the data for whole Vienna (DISTRICT_CODE: 9000)
st.text('Ganz Wien: ' + str(csv_data.loc[csv_data['DISTRICT_CODE'] == 90000, selected_value].values[0]) + title_mapping[selected_value][28:])

# Load district boundaries GeoJSON for Vienna
vienna_districts_geojson_url = "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BEZIRKSGRENZEOGD&srsName=EPSG:4326&outputFormat=json"

# Merge data with GeoJSON
vienna_districts_geojson = requests.get(vienna_districts_geojson_url).json()

@st.cache_data
def merge_data_with_geojson(district_data, geojson, value_key):
    for feature in geojson["features"]:
        district = feature["properties"].get("BEZNR")
        if district:
            feature["properties"][value_key] = float(district_data.loc[district, value_key] if district in district_data.index else 0)
            geom = shape(feature["geometry"])
            if geom.is_valid:
                centroid = geom.centroid
                feature["properties"]["centroid"] = (centroid.x, centroid.y)
            else:
                feature["properties"]["centroid"] = (0, 0)
    return geojson

@st.cache_data
def generate_text_data(geojson, value_key):
    text_data = []

    for feature in geojson["features"]:
        district_value = feature["properties"].get(value_key)
        centroid = feature["properties"].get("centroid")
        distr_name = feature["properties"].get("NAMEG")

        if district_value is not None and centroid is not None:
            text_data.append({
                "position": centroid,
                "text": str(f"{distr_name}:\n{district_value}")
            })

    return text_data


merged_data = merge_data_with_geojson(csv_data, vienna_districts_geojson, selected_value)

@st.cache_data
def create_2d_map_pydeck(geojson, value_key):
    # Create the GeoJSON layer
    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson,
        opacity=0.8,
        get_fill_color=[100, 100, 80, 60],
        get_line_color=[0, 0, 0],
        get_line_width=10,
        pickable=True,
        auto_highlight=True
    )

    # Generate the data for the Text layer
    text_data = generate_text_data(geojson, value_key)

    # Create the Text layer
    text_layer = pdk.Layer(
        "TextLayer",
        text_data,
        pickable=False,
        get_position="position",
        get_text="text",
        get_size=13,
        get_color=[0,40,0],
        get_angle=0,
        get_text_anchor='"middle"',
        get_alignment_baseline='"center"',
        auto_highlight=True
    )

    # Set the initial view state
    #view_state = pdk.ViewState(latitude=48.1351, longitude=11.5820, zoom=10)

    # Render the map
    return pdk.Deck(
        layers=[geojson_layer, text_layer],
        initial_view_state={
            "latitude": 48.2082,
            "longitude": 16.3738,
            "zoom": 12,
            "pitch": 0,
            "bearing": 0,
        },
        map_provider="mapbox", map_style=None)




 # Create the 2D map with numbers on districts using pydeck
map_2d_pydeck = create_2d_map_pydeck(merged_data, selected_value)

# Display the map in Streamlit
st.pydeck_chart(map_2d_pydeck)
