from EST_tidy_data import makedf
#from EST_gui import get_variables
import numpy as np
import pandas as pd
import altair as alt
from io import BytesIO
import pandas as pd
import streamlit as st
import pgeocode


country = pgeocode.Nominatim("gb")
MonthDict={ 1 : "January", 2 : "February", 3 : "March", 4 : "April", 5 : "May", 6 : "June", 7: "July",
            8 : "August", 9 : "September", 10 : "October", 11 : "November",12 : "December"}
PropertyDict={
    "g0":"General Business", "g1":"Weekday Business","g2":"Evening Business","g3":"Continuous Business",
    "g4":"Shop or Barber","g5":"Bakery","g6":"Weekend Business",
    "l0":"General Farm","l1":"Dairy or Livestock Farm", "l2":"Other Farm", "h0":"Household"}
invPropertyDict = {v: k for k, v in PropertyDict.items()}

#lat, lon = 56.140,-3.919
start = 2013
end = 2016
st.set_page_config(layout="wide")

"""
# Welcome to the PVGIS-BDEW Tool!
Made by Maxim Oweyssi for the Energy Saving Trust :heart:
"""


col1, col2 = st.columns([1,3])
@st.cache
def to_the_shop_to_get_your_PVGIS_data(property_type,lat,lon,annual_consumption, PV_max_power, surface_tilt, surface_azimuth):
    return makedf(invPropertyDict[property_type],lat, lon, annual_consumption, PV_max_power, surface_tilt, surface_azimuth,start, end)

with col1:
    with st.form(key="Input parameters"):
        property_type = st.selectbox('What is the property type?',PropertyDict.values())
        lat = float(st.text_input('Latitude', value=56.140,))
        lon = float(st.text_input('Longitude',value =-3.919))
        annual_consumption = st.number_input('Annual property consumption [kWh]',value=12000,step=1)
        PV_max_power = st.number_input('PV system peak power [kWp]',value=5,step=1)
        surface_tilt = st.number_input('Surface tilt [degrees]',value=35,step=1)
        surface_azimuth = st.number_input('Surface tilt [degrees]',value=0,step=1)
        button = st.form_submit_button(label="Plot the plot!")
            
with col2:
    df, average,cloudy, sunny, bdew_demand, t, yearly_gen, yearly_use = to_the_shop_to_get_your_PVGIS_data(
                property_type,lat,lon,annual_consumption, PV_max_power, surface_tilt, surface_azimuth)
    month = st.slider("Month", 1, 12, 12)
    day = st.radio("What day?",('workday','saturday','sunday'),horizontal=True,label_visibility='hidden')

    PV = alt.Chart(df[month-1]).mark_line().encode(
    x='time',
    y=alt.Y('PV generation',scale=alt.Scale(domain=(0,PV_max_power*2/3))))

    error = alt.Chart(df[month-1]).mark_area(opacity=0.2).encode(x='time',y='PV min',y2='PV max')
    if day == 'workday':
        BDEW = alt.Chart(df[month-1]).mark_line(color='red').encode(x='time',y='BDEW workday')
    elif day == 'saturday':
        BDEW = alt.Chart(df[month-1]).mark_line(color='red').encode(x='time',y='BDEW saturday')
    elif day == 'sunday':
        BDEW = alt.Chart(df[month-1]).mark_line(color='red').encode(x='time',y='BDEW sunday')

    chart = PV+error +BDEW
    chart.height=450
    st.altair_chart(chart,use_container_width=True)

    def export_xlsx(df):
        output = BytesIO()
        year_df = pd.DataFrame(
            index = ['a','b','c'],
            columns = ['Annual \nDemand: ' + str(annual_consumption)+' kWh',
             'Annual PV \ngeneration: ' + (str(yearly_gen[0])+' ± '+str(yearly_gen[1])+' kWh'),
             ('Annual PV \n used: ' + str(yearly_use[0])+' ± '+str(yearly_use[1])+' kWh')])
        frames = [average,cloudy,sunny,bdew_demand,year_df]
        start_row = 1
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        sheet_name='Monthly Percentages'
        for df in frames:  # assuming they're already DataFrames
            df.to_excel(writer, sheet_name, startrow=start_row, startcol=0, index=False)
            start_row += len(df) + 2  # add a row for the column header?
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets[sheet_name].set_column(col_idx, col_idx, column_width)
        writer.save()
        processed_data = output.getvalue()
        return processed_data

    toexport = export_xlsx(df)
    st.download_button(label='📥 Download stats in Excel',
                                data=toexport ,
                                file_name= invPropertyDict[property_type]+"_"+str(annual_consumption)+"kWh_"+str(PV_max_power)+"kWp.xlsx")





