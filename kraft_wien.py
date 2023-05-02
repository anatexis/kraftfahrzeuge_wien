import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
from io import StringIO
import pydeck as pdk
from shapely.geometry import shape, Polygon
import pprint

def print_geojson(geojson):
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(geojson)

CSV_URL = 'https://www.wien.gv.at/gogv/l9ogdviebezbiztecveh2002f'
VIENNA_DISTRICTS_GEOJSON_URL = "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BEZIRKSGRENZEOGD&srsName=EPSG:4326&outputFormat=json"

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

@st.cache_data
def load_data(url):
    """Load data from a CSV file."""
    data = pd.read_csv(url, sep=';', header=1, decimal=',', thousands='.')
    return data


@st.cache_data
def merge_data_with_geojson(district_data, geojson, value_key):
    """Merge district data with GeoJSON data."""
    for feature in geojson["features"]:
        district = feature["properties"].get("BEZNR")
        if district:
            # Find the row that matches the district value
            matching_row = district_data[district_data['DISTRICT'] == district]

            # If there's a matching row, set the value_key, otherwise set it to 0
            if not matching_row.empty:
                feature["properties"][value_key] = float(
                    matching_row[value_key].values[0])
            else:
                feature["properties"][value_key] = 0.0

            geom = shape(feature["geometry"])
            if geom.is_valid:
                centroid = geom.centroid
                feature["properties"]["centroid"] = (centroid.x, centroid.y)
            else:
                feature["properties"]["centroid"] = (0, 0)
    return geojson


@st.cache_data
def generate_text_data(geojson, value_key):
    """Generate text data for district values."""
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

@st.cache_data
def generate_districts_geojson(geojson_bare):
    """Generate a GeoJSON containing only district data."""
    district_geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for feature in geojson_bare["features"]:
        district_feature = {
            "type": "Feature",
            "properties": {
                "NAMEG": feature["properties"].get("NAMEG"),
                "BEZNR": feature["properties"].get("BEZNR")
            },
            "geometry": feature["geometry"]
        }
        district_geojson["features"].append(district_feature)
        
    return district_geojson


@st.cache_data
def create_2d_map_pydeck(geojson_bare, geojson_combined, value_key, year):
    """Create a 2D map using pydeck."""
    geojson_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson_bare,
        opacity=0.8,
        get_fill_color=[100, 100, 80, 60],
        get_line_color=[0, 0, 0],
        get_line_width=10,
        pickable=True,
        auto_highlight=True
    )

    # Generate the data for the Text layer
    text_data = generate_text_data(geojson_combined, value_key)

    # Create the Text layer
    text_layer = pdk.Layer(
        "TextLayer",
        text_data,
        pickable=False,
        get_position="position",
        get_text="text",
        get_size=13,
        get_color=[0, 40, 0],
        get_angle=0,
        get_text_anchor='"middle"',
        get_alignment_baseline='"center"',
        auto_highlight=True
    )


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

def main():
    st.title('Kraftfahrzeugbestand in Wien')
    
    csv_data = load_data(CSV_URL)
    csv_data = csv_data.assign(DISTRICT=csv_data['DISTRICT_CODE'].astype(str).str.slice(start=1, stop=3).astype(int))
    
    # Dropdown for selecting value
    value_options = list(csv_data.columns[5:-1])
    selected_value = st.selectbox('Bitte Variable auswählen: ', value_options)
    
    # Add this after the 'Select a value to plot' dropdown
    year_min = int(csv_data['REF_YEAR'].min())
    year_max = int(csv_data['REF_YEAR'].max())
    selected_year = st.slider('Select a year:', year_min, year_max, year_max)
    
    # Filter data for selected year
    csv_data_filtered = csv_data.loc[csv_data['REF_YEAR'] == selected_year]
    
    # Display the long title according to the selected_value
    st.header(title_mapping[selected_value][:26])
    st.subheader(title_mapping[selected_value][28:])
    
    # Load district boundaries GeoJSON for Vienna
    vienna_districts_geojson = requests.get(VIENNA_DISTRICTS_GEOJSON_URL).json()
    # create bare GeoJSON for districts
    geojson_bare = generate_districts_geojson(vienna_districts_geojson)


    # Merge data with GeoJSON
    merged_data = merge_data_with_geojson(csv_data_filtered, vienna_districts_geojson, selected_value)
    
    # Create the 2D map with numbers on districts using pydeck
    map_2d_pydeck = create_2d_map_pydeck(geojson_bare, merged_data, selected_value, selected_year)
    
    st.pydeck_chart(map_2d_pydeck)

    st.subheader(f'Daten für das Jahr {selected_year}')
    st.dataframe(csv_data_filtered[csv_data_filtered.columns[5:-1]])
    
    st.markdown('''

    Datenquelle und Datensätze:

    Stadt Wien - https://data.wien.gv.at

    [Zugelassene Kraftfahrzeuge seit 2002 - Bezirke Wien](https://www.data.gv.at/katalog/de/dataset/vie-bez-biz-tec-veh-2002f)
     & [Bezirksgrenzen Wien](https://www.data.gv.at/katalog/de/dataset/stadt-wien_bezirksgrenzenwien)
    
                ''')

    #print_geojson(geojson_bare)


if __name__ == "__main__":
    main()

