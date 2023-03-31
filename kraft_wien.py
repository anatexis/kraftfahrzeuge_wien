import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static
import pydeck as pdk


# Download the CSV file
url = 'https://www.wien.gv.at/gogv/l9ogdviebezbiztecveh2002f'
csv_text = requests.get(url).text
csv_data = pd.read_csv(StringIO(csv_text), sep=';', header=1, decimal=',')
csv_data["PKW_VALUE"] = pd.to_numeric(csv_data["PKW_VALUE"], errors='coerce')
# App title
st.title('District Data Plotter')

# Upload CSV file
uploaded_file = st.file_uploader('Choose a CSV file', type='csv')

if uploaded_file:
    csv_data = pd.read_csv(uploaded_file, sep=';', header=1, decimal=',')

# Change DISCTRICT_CODE to 4 numbers:

csv_data = csv_data.assign(DISTRICT = csv_data['DISTRICT_CODE'].astype(str).str.slice(start=1, stop=5).astype(int))

# Dropdown for selecting value
value_options = list(csv_data.columns[5:-1])
selected_value = st.selectbox('Select a value to plot:', value_options)

# Function to plot the data
def plot_data_for_year(year, data, value):
    year_data = data[data['REF_YEAR'] == year]
    pivot_data = year_data.pivot_table(index='REF_YEAR', columns='DISTRICT', values=value)
    pivot_data.plot(kind='bar', figsize=(10, 5))
    plt.title(f'Data of Districts for the Year {year}')
    plt.xlabel('Year')
    plt.ylabel(f'{value}')
    plt.legend(title='District', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)
    plt.grid(axis='y')
    return plt

years = csv_data['REF_YEAR'].unique()

# for year in years:
#    plot = plot_data_for_year(year, csv_data, selected_value)
#    st.pyplot(plot)

# Load district boundaries GeoJSON for Vienna
vienna_districts_geojson_url = "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BEZIRKSGRENZEOGD&srsName=EPSG:4326&outputFormat=json"

# Function to create a 3D map with columns
import pandas as pd
from keplergl import KeplerGl

def create_3d_map(data, value):
    map_config = {
        "version": "v1",
        "config": {
            "mapState": {
                "latitude": 48.2082,
                "longitude": 16.3738,
                "zoom": 11,
            },
            "mapStyle": {
                "styleType": "dark",
            },
            "visState": {
                "layers": [
                    {
                        "id": "3d_column_layer",
                        "type": "geojson",
                        "config": {
                            "dataId": "vienna_data",
                            "label": "Vienna Districts",
                            "columns": {
                                "geojson": "geometry"
                            },
                            "isVisible": True,
                            "visConfig": {
                                "color": [255, 0, 0],
                                "opacity": 0.8,
                                "extruded": True,
                                "sizeRange": [0, 500],
                                "getElevation": {
                                    "accessor": value,
                                    "scale": 1,
                                },
                            },
                        },
                    },
                ],
                "interactionConfig": {
                    "tooltip": {
                        "fieldsToShow": {
                            "vienna_data": ['NAMEK_NUM', 'UMFANG', 'FLAECHE', value],
                        },
                        "enabled": True,
                    },
                },
            },
        },
    }

    # Create a KeplerGl map object
    map_1 = KeplerGl(height=600, config=map_config)

    # Add data to the map
    map_1.add_data(data=data, name="vienna_data")

    return map_1


# Merge data with GeoJSON
vienna_districts_geojson = requests.get(vienna_districts_geojson_url).json()

def merge_data_with_geojson(district_data, geojson, value_key):
    for feature in geojson["features"]:
        district = feature["properties"].get("BEZNR")
        if district:
            feature["properties"][value_key] = float(district_data.loc[district, value_key] if district in district_data.index else 0)
            print(district)
    return geojson

merged_data = merge_data_with_geojson(csv_data, vienna_districts_geojson, selected_value)

# Create the 3D map with columns
value = selected_value 
map_3d = create_3d_map(merged_data, value)

# Display the map in Streamlit
keplergl_static(map_3d)

# Save the map to an HTML file
map_3d.save_to_html(file_name="3d_map.html")
