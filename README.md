# Vehicle Inventory in Vienna

This is a Streamlit web app that visualizes the inventory of vehicles in Vienna by district, using data from the city of Vienna. The app provides an interactive map displaying the number of registered vehicles per district, broken down by vehicle type, and normalized by population. Users can choose which vehicle type to display, and the data can be filtered by year.

## Features

- Interactive map of Vienna displaying the number of registered vehicles per district.
- Dropdown menu to select a vehicle type (e.g., cars, buses, motorcycles, etc.).
- Slider to filter data by year.
- Table displaying the data for the selected year and vehicle type.

## Usage

### Access the Streamlit App Online

You can access the application online without installing any dependencies or running it locally. Visit the following URL to use the interactive Kraftfahrzeugbestand in Wien: [Streamlit-App](https://anatexis-kraftfahrzeuge-wien-kraft-wien-31e195.streamlit.app/)

### Access it locally

1. Clone this repository.
2. Install the required dependencies using pip: `pip install -r requirements.txt`
3. In your terminal, navigate to the directory containing the app.py file.
4. Run the Streamlit app: `streamlit run app.py`
5. If the website is not opend automatically, open the app in your browser using the link provided in the terminal.



## Data Sources

- City of Vienna: https://data.wien.gv.at
- [Zugelassene Kraftfahrzeuge seit 2002 - Bezirke Wien](https://www.data.gv.at/katalog/de/dataset/vie-bez-biz-tec-veh-2002f)
- [Bezirksgrenzen Wien](https://www.data.gv.at/katalog/de/dataset/stadt-wien_bezirks
