import streamlit as st
import numpy as np
import pandas as pd
import joblib
import base64
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
from streamlit_modal import Modal
from PIL import Image
import plotly.graph_objects as go
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans, MiniBatchKMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
import plotly.express as px  

st.set_page_config(page_title = 'CTD Simulator', layout="wide")

###### Imports ##########
@st.cache_data                  # Caching the data so that it doesn't gets loaded everytime 
def import_data(): 
    df_mat_mapping = pd.read_excel(r'data\Material_PalletQTY_Mapping.xlsx', engine='openpyxl')
    pincode_df = pd.read_excel(r'data\Pincode_data.xlsx')
    df_tspt_charges_dt4 = pd.read_excel(r'data\Tnspt_charges.xlsx', sheet_name='GXO_DT4')
    df_tspt_charges_ne2 = pd.read_excel(r'data\Tnspt_charges.xlsx', sheet_name='WHM_NE2')
    df_dt8 = pd.read_excel(r'data\Kammac_DT8.xlsx')
    df_dt8_skus = pd.read_csv(r'data\dt8_skus.csv')
    df_segments = pd.read_excel(r'data\Segments_FY23.xlsx')
    return df_mat_mapping, pincode_df, df_tspt_charges_dt4, df_tspt_charges_ne2, df_dt8, df_dt8_skus, df_segments

mat_mapping = import_data()[0]
pincode_df = import_data()[1]
tspt_charges_dt4 = import_data()[2]
tspt_charges_ne2 = import_data()[3]
dt8 = import_data()[4]
dt8_skus = import_data()[5]
df_segments = import_data()[6]

#pincode_df['SHIP_TO_NUMBER_NAME'] = pincode_df['SHIP_TO_NUMBER'] +'- '+ pincode_df['SHIP_TO_NAME'] 
pincode_df['SHIP_TO_NUMBER'] = pincode_df['SHIP_TO_NUMBER'].apply(lambda x : str(x))
pincode_df['SHIP_TO_NAME'] = pincode_df['SHIP_TO_NAME'].apply(lambda x : str(x))

tspt_charges_dt4[0] = 0
tspt_charges_ne2[0]= 0

##################### All Functions ####################
def line_break(comp, num_breaks):
    for i in range(num_breaks):
        comp.markdown('\n')
        
def warehouse_map(ship_to):
    ship_to_dict= dict()
    ship_to_name = pincode_df[pincode_df.SHIP_TO_NUMBER_NAME == ship_to].SHIP_TO_NAME.values[0]
    ship_to_number = pincode_df[pincode_df.SHIP_TO_NUMBER_NAME == ship_to].SHIP_TO_NUMBER.values[0]    
    ship_to_city = pincode_df[pincode_df.SHIP_TO_NUMBER == ship_to_number].SHIP_TO_CITY.values[0]   
    postal_code = pincode_df[pincode_df.SHIP_TO_NUMBER == ship_to_number].Postal_code_stripped.values[0]
    nearest_warehouse = pincode_df.loc[pincode_df.SHIP_TO_NUMBER == ship_to_number, 'Nearest_Warehouse'].values[0]
    mapped_warehouse=''
    if tspt_charges_dt4.loc[tspt_charges_dt4.Destination== postal_code, 'Type'].values[0] == 'KNDL':
        mapped_warehouse='DT4'
    elif tspt_charges_ne2.loc[tspt_charges_ne2.Postcode== postal_code, 'Contract Area'].values == 'Malcolm':
        mapped_warehouse='NE2'
    else: mapped_warehouse = 'none'
    
    ship_to_dict['ship_to_number'] = ship_to_number
    ship_to_dict['ship_to_name'] = ship_to_name
    ship_to_dict['ship_to_city'] = ship_to_city
    ship_to_dict['postal_code'] = postal_code
    ship_to_dict['mapped_warehouse'] = mapped_warehouse
    ship_to_dict['nearest_warehouse'] = nearest_warehouse
    
    return ship_to_dict

def transport_cost(mapped_warehouse, selected_warehouse, no_pallets, postal_code):
    full_trucks = int(no_pallets/26)
    if no_pallets==0:
        return 0
    elif selected_warehouse=='DT4' and mapped_warehouse=='DT4' and no_pallets<=26 and postal_code in tspt_charges_dt4.Destination.tolist():
        tspt_cost = tspt_charges_dt4.loc[tspt_charges_dt4.Destination== postal_code, no_pallets].values[0]
    elif selected_warehouse=='DT4' and mapped_warehouse=='DT4' and no_pallets>26 and postal_code in tspt_charges_dt4.Destination.tolist():
        tspt_cost = full_trucks * tspt_charges_dt4.loc[tspt_charges_dt4.Destination== postal_code, 26].values[0] + tspt_charges_dt4.loc[tspt_charges_dt4.Destination== postal_code, no_pallets%26].values[0]
    elif  selected_warehouse=='DT4' and mapped_warehouse!='DT4' and no_pallets<=26 and postal_code in tspt_charges_dt4.Destination.tolist():
        tspt_cost = tspt_charges_dt4.loc[(tspt_charges_dt4.Destination== postal_code) &(tspt_charges_dt4.Type=='NON-KNDL'), no_pallets].values[0]
    elif  selected_warehouse=='DT4' and mapped_warehouse!='DT4' and no_pallets>26 and postal_code in tspt_charges_dt4.Destination.tolist():
        tspt_cost = full_trucks * tspt_charges_dt4.loc[(tspt_charges_dt4.Destination== postal_code) &(tspt_charges_dt4.Type=='NON-KNDL'), 26].values[0] + tspt_charges_dt4.loc[(tspt_charges_dt4.Destination== postal_code) &(tspt_charges_dt4.Type=='NON-KNDL'), no_pallets%26].values[0]
    elif selected_warehouse=='NE2' and mapped_warehouse =='NE2' and no_pallets<=26 and postal_code in tspt_charges_ne2.Postcode.tolist():
        tspt_cost = tspt_charges_ne2.loc[tspt_charges_ne2.Postcode== postal_code, no_pallets].values[0]
    elif selected_warehouse=='NE2' and mapped_warehouse =='NE2' and no_pallets>26 and postal_code in tspt_charges_ne2.Postcode.tolist():
        tspt_cost = full_trucks * tspt_charges_ne2.loc[tspt_charges_ne2.Postcode== postal_code, 26].values[0] + tspt_charges_ne2.loc[tspt_charges_ne2.Postcode== postal_code, no_pallets%26].values[0]
    elif selected_warehouse=='NE2' and mapped_warehouse!='NE2' and no_pallets<=26 and postal_code in tspt_charges_ne2.Postcode.tolist():
        tspt_cost = tspt_charges_ne2.loc[(tspt_charges_ne2.Postcode== postal_code) & (tspt_charges_ne2['Contract Area']=='Non-Malcolms'), no_pallets].values[0]
    elif selected_warehouse=='NE2' and mapped_warehouse!='NE2' and no_pallets>26 and postal_code in tspt_charges_ne2.Postcode.tolist():
        tspt_cost = full_trucks* tspt_charges_ne2.loc[(tspt_charges_ne2.Postcode== postal_code) & (tspt_charges_ne2['Contract Area']=='Non-Malcolms'), 26].values[0] + tspt_charges_ne2.loc[(tspt_charges_ne2.Postcode== postal_code) & (tspt_charges_ne2['Contract Area']=='Non-Malcolms'), no_pallets%26].values[0]
    elif selected_warehouse=='DT8':
        line_break(st.sidebar, 1)
        custom_info("Transport cost not present from DT8, hence needed as user input")
        line_break(st.sidebar, 1)
        tspt_cost_input = st.sidebar.number_input("**Transport Cost/ pallet- DT8**", 0.00, 100.00, value = np.round(dt8['Per Pallet'].mean(), 2))
        tspt_cost = tspt_cost_input* no_pallets
    else: tspt_cost='NA'
    return tspt_cost

def map_plot(selected_ship_to, ship_to_city, ship_to_cor, comp):
    coordinates_df=pd.DataFrame({'Coordinates': ['DT4', 'NE2', 'DT8'], 'LAT': [52.885948, 55.833390, 53.314417],
                            'LON':[-1.701790, -3.924020, -2.655691]})
    map = folium.Map(location=[54.5000, -0.1250], zoom_start=6, control_scale=True)
    for i,row in coordinates_df.iterrows():
        iframe = folium.IFrame('Warehouse:' + str(row["Coordinates"]))

        popup = folium.Popup(iframe, min_width=120, max_width=200)

        folium.Marker(location=[row['LAT'],row['LON']],
                    popup = popup, c=row['Coordinates']).add_to(map)

    iframe2 = folium.IFrame(f'{selected_ship_to} - {ship_to_city}')
    popup2 = folium.Popup(iframe2, min_width=150, max_width=120)
    folium.Marker(ship_to_cor, popup = popup2, icon=folium.Icon(color='green')).add_to(map)
    with comp:
        st_map = st_folium(map, width=500, key='map')
    return st_map

def custom_info(message):
    st.sidebar.markdown(f'<div class="custom-st-info">{message}</div>', unsafe_allow_html=True)
    
def upload_to_azure_blob_storage(uploaded_file, container_name, connection_string):
    current_datetime = str(datetime.now())
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    for file in uploaded_file:
        blob_name =f"{file.name}_{current_datetime}"
        blob_client = container_client.get_blob_client(blob_name)
        with file as f:
            blob_client.upload_blob(f)
    
####### Header #################
st.markdown("""
<center>
<h1 style="font-size: 30px; text-align: center; font-family: 'Raleway'; color : #525252; ">Cost to Deliver - Great Britain</h1>
</center>
""", unsafe_allow_html=True)

######## Option menu ##########
om1, om2, om3 = st.columns([1,3,1])
with om2:    
    selected_option = option_menu(
        menu_title = None,
        options = ["Simulate", "Comparison Table", "Segmentation"],
        icons = ["gear-fill", "table", "person-bounding-box"],
        default_index = 0,
        orientation = "horizontal",
        styles={
        "nav-link-selected": {"background-color": "gray"},
    }
    )

###### Custom info bar for Nearest & Mapped warehouse info ######
st.markdown(
    """
    <style>
    /* Custom CSS class for the custom st.info widget */
    .custom-st-info {
        background-color: gray; /* Change the background color to gray */
        color: white; /* Change the font color to white */
        padding: 10px 10px; /* Add padding for better visual appearance */
    }
    </style>
    """,
    unsafe_allow_html=True
)

######### Main Background ##########

def main_bg(main_bg):
    main_bg_ext = 'png'
    st.markdown(
      f"""
      <style>
      [data-testid="stAppViewContainer"] > .main {{
        background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
        background-size: 180%;
        background-position: top left;
        background-repeat: no-repeat;
        background-attachment: local;
      }}
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}
    [data-testid="stToolbar"] {{
        right: 2rem;
    }}
      </style>
      """,
      unsafe_allow_html=True,
      )
main_bg_img = 'imgs\warehouse.jpeg'
main_bg(main_bg_img)

######### Sidebar Background ##############
def sidebar_bg(side_bg):
   side_bg_ext = 'png'
   st.markdown(
      f"""
      <style>
      [data-testid="stSidebar"] > div:first-child {{
          background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
      }}
      </style>
      """,
      unsafe_allow_html=True,
      )
   
side_bg = 'imgs\pexels-eberhard-grossgasteiger-1743392.jpg'
sidebar_bg(side_bg)

def convert_df(df):
    return df.to_csv().encode('utf-8')

####### Color change for labels ###########33
st.markdown(
    """
    <style>
    .stNumberInput label {
        color: white; 
    }
    .stSelectbox label {
        color: white; 
    }
    .stMultiSelect label {
        color: white;
    }
    .stFileInput label {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)
        
custom_styles = """
    <style>
    .custom-metric {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .custom-metric .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .custom-metric .metric-label {
        font-size: 12px;
        color: #777;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .custom-metric-ctd{
        background-color: #B3CDCB;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .custom-metric-ctd .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .custom-metric-ctd .metric-label {
        font-size: 12px;
        color: #777;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    .custom-metric-co2{
        background-color: #DBDEF9;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .custom-metric-co2 .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .custom-metric-co2 .metric-label {
        font-size: 12px;
        color: #777;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    </style>
    """


# Render custom CSS styles for metric tiles
st.markdown(custom_styles, unsafe_allow_html=True)   

if selected_option in ('Simulate', 'Comparison Table'):
    with st.sidebar:
        colx, coly, colz = st.columns([1,1.2,1])
        with coly:
            st.image("imgs\Diageo-Logo-Gold.png", width=100, use_column_width=True, output_format ="PNG") 
            st.image("imgs\heartbeat_logo-removebg.png", width=50, use_column_width=True, output_format ="PNG")
            unique_ship_to_list = pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist() + dt8['SHIP_TO_NAME'].unique().tolist()
        selected_ship_to = st.sidebar.selectbox('**Ship-to**', unique_ship_to_list,key='ship-to')
        
        if selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist():
            ship_to_details = warehouse_map(selected_ship_to)
            ship_to_number = ship_to_details['ship_to_number']
            ship_to_name = ship_to_details['ship_to_name']
            ship_to_city = ship_to_details['ship_to_city']
            postal_code = ship_to_details['postal_code']
            mapped_warehouse = ship_to_details['mapped_warehouse']
            nearest_warehouse = ship_to_details['nearest_warehouse']
            
        elif selected_ship_to in dt8['SHIP_TO_NAME'].unique().tolist():
            ship_to_name = selected_ship_to
            ship_to_city = dt8.loc[dt8.SHIP_TO_NAME==selected_ship_to, 'SHIP_TO_CITY'].values[0]
            postal_code = dt8.loc[dt8.SHIP_TO_NAME==selected_ship_to, 'Postcode'].values[0]
            mapped_warehouse = 'DT8'
            nearest_warehouse = dt8.loc[dt8.SHIP_TO_NAME==selected_ship_to, 'Nearest_warehouse'].values[0]

        custom_info(f'Ship-to city : {ship_to_city}')
        line_break(st.sidebar, 1)
        if mapped_warehouse == 'none':
            default_ix=0
            custom_info('No mapped warehouse found')
        else:
            warehouse_options = ['NE2', 'DT8', 'DT4']
            default_ix = warehouse_options.index(mapped_warehouse)
        selected_warehouse = st.sidebar.selectbox('**Shipping Warehouse**', ['NE2', 'DT8', 'DT4'], index=default_ix,
                                                    key='selected_warehouse')
        
        custom_info(f"Mapped warehouse is {mapped_warehouse}")
        custom_info(f"Nearest warehouse is {nearest_warehouse}")
        line_break(st.sidebar,1)
        if selected_warehouse == 'DT8':
            material_list = dt8_skus['MATERIAL_DESCRIPTION']            # Selecting only those SKUs present in DT8 if selected warehouse is DT8
        else:
            material_list = mat_mapping['Material Description']
        selected_material = st.sidebar.multiselect('**Material**', material_list, key='materials',
                                                default=material_list[0])
        pallet_picks, case_picks, units = 0,0,0
        pallet_picks_temp, case_picks_temp, units_temp, pallet_fill_rate = 0,0,0,0
        for mat in selected_material:
            units_temp = st.sidebar.number_input(f'**Units- {mat}**', 0, 5000, value = 200, step=1)
            conv_temp = mat_mapping.loc[mat_mapping['Material Description']==mat, 'Cs/Plt'].values[0]
            pallet_picks_temp = int(units_temp/conv_temp)
            case_picks_temp = units_temp - int(pallet_picks_temp * conv_temp)
            pallet_fillrate_temp = case_picks_temp/conv_temp
            pallet_picks+=pallet_picks_temp
            case_picks+= case_picks_temp
            units+= units_temp
            pallet_fill_rate+= pallet_fillrate_temp   
        pallet_transported = pallet_picks+ np.ceil(pallet_fill_rate)
        
        
        ############# Upload Button for raw data ############

        line_break(st.sidebar, 1)   
        modal = Modal("", key='raw_data_modal')
        open_modal = st.button("Upload data :cloud:")
        if open_modal:
            modal.open()
        
        connection_string = "DefaultEndpointsProtocol=https;AccountName=streamlittest0708;AccountKey=P6wjgDjeo/toCCDmzSYCAVaaUimezJPJBdgWizCTcPl9bsWv+mK/1ptsx+oAC5ueEN8Gan373xLf+AStInVlsw==;EndpointSuffix=core.windows.net"
        container_name = "streamlittest0708"

        if modal.is_open():
            with modal.container():
                uploaded_file = st.file_uploader("**Upload 3PL raw data**", accept_multiple_files= True)
                blob_upload = st.button("Upload to Azure Blob", on_click= upload_to_azure_blob_storage(uploaded_file, container_name, connection_string))
                if blob_upload:
                    st.success("File uploaded successfully!")

if selected_option == "Simulate":
    cl, c1, c2, c3, c4, c5,c6, cmap, cr = st.columns([0.3, 1.2, 0.5, 1.2, 0.5, 1.2, 0.5, 2.25, 0.3])
    selected_units = c1.markdown(f'<div class="custom-metric"><div class="metric-value">{units}</div><div class="metric-label">Total Units</div></div>', unsafe_allow_html=True)
    # pallet_picks = calculate_pallet_cases(selected_material, mat_mapping)[0]
    # case_picks = calculate_pallet_cases(selected_material, mat_mapping)[1]
    c3.markdown(f'<div class="custom-metric"><div class="metric-value">{pallet_picks}</div><div class="metric-label">Pallet picks</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="custom-metric"><div class="metric-value">{case_picks}</div><div class="metric-label">Case picks</div></div>', unsafe_allow_html=True)
    line_break(c1, 3)
    line_break(c3, 3)
    line_break(c5, 3)

    per_pickcost = dict()
    if selected_warehouse=='DT4':
        per_pickcost['per_case_pick'] = 0.42
        per_pickcost['per_pallet_pick']=3.53
        per_pickcost['per_keg_pick']=0.42
    elif selected_warehouse=='NE2':
        per_pickcost['per_case_pick'] = 0.4
        per_pickcost['per_pallet_pick']=2.23
        per_pickcost['per_keg_pick']=0.4
    elif selected_warehouse =='DT8':
        per_pickcost['per_case_pick'] = 0.42
        per_pickcost['per_pallet_pick']=2.38
        per_pickcost['per_keg_pick']=0.42
        
    selected_cost_per_casepick = c1.slider("**Cost per Case pick**",0.00,2.00, value=per_pickcost['per_case_pick'], step=0.01, key= 'cost_per_case_pick')
    selected_cost_per_palletpick = c3.slider("**Cost per Pallet pick**",0.00,5.00, value=per_pickcost['per_pallet_pick'], step=0.01, key= 'cost_per_pallet_pick')
    selected_cost_per_kegpick = c5.slider("**Cost per KEG pick**",0.00,2.00, value=per_pickcost['per_keg_pick'], step=0.01, key= 'cost_per_keg_pick')
    line_break(c1, 3)
    line_break(c3, 3)
    line_break(c5, 3)

    case_pick_cost = np.round(case_picks * selected_cost_per_casepick,2)
    c1.markdown(f'<div class="custom-metric"><div class="metric-value">{case_pick_cost}</div><div class="metric-label">Case pick costs (£)</div></div>', unsafe_allow_html=True)

    pallet_pick_cost =  np.round(pallet_picks * selected_cost_per_palletpick, 2)
    c3.markdown(f'<div class="custom-metric"><div class="metric-value">{pallet_pick_cost}</div><div class="metric-label">Pallet pick costs (£)</div></div>', unsafe_allow_html=True)
    tot_pick_cost = case_picks * selected_cost_per_casepick + pallet_picks * selected_cost_per_palletpick
    tot_pick_cost = np.round(tot_pick_cost,2)
    c5.markdown(f'<div class="custom-metric"><div class="metric-value">{tot_pick_cost}</div><div class="metric-label">Total Pick Cost (£)</div></div>', unsafe_allow_html=True)
    line_break(c1, 3)
    line_break(c3, 3)
    line_break(c5, 3)


    pickcost_per_unit = np.round(tot_pick_cost/units, 2)
    c1.markdown(f'<div class="custom-metric"><div class="metric-value">{pickcost_per_unit}</div><div class="metric-label">Pick Cost per case (£)</div></div>', unsafe_allow_html=True)
    
    #### Transport cost
    if selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist() and mapped_warehouse!='none':
        tspt_cost = np.round(transport_cost(mapped_warehouse, selected_warehouse, int(pallet_transported) , postal_code),2)
    elif selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist() and mapped_warehouse=='none':
        line_break(st.sidebar , 1)
        tspt_cost_input = st.sidebar.number_input(f'Transport cost/pallet - {selected_warehouse}', 0.00, 100.00,
                                                                            value = 70.00)
        tspt_cost = np.round(tspt_cost_input * pallet_transported, 2)
    elif selected_ship_to in dt8['SHIP_TO_NAME'].unique().tolist() and selected_warehouse=='DT8':
        st.sidebar.markdown("\n")
        dt8_per_pallet_tspt_cost = float(dt8.loc[dt8.SHIP_TO_NAME==selected_ship_to, 'Per Pallet'].values[0])
        tspt_cost = np.round(dt8_per_pallet_tspt_cost * pallet_transported, 2)
    elif selected_ship_to in dt8['SHIP_TO_NAME'].unique().tolist() and selected_warehouse!='DT8':
        line_break(st.sidebar, 1)
        custom_info(f'Transport cost not present from {selected_warehouse}, hence needed as user input')
        line_break(st.sidebar , 1)
        globals()[f"{selected_warehouse}_tspt_cost"]= st.sidebar.number_input(f'Transport cost/pallet - {selected_warehouse}', 0.00, 100.00,
                                                                            value = np.round(dt8['Per Pallet'].mean(), 2))
        tspt_cost = np.round(globals()[f"{selected_warehouse}_tspt_cost"] * pallet_transported, 2)
        
        
    if selected_material==[]:
        tspt_cost=0
    c3.markdown(f'<div class="custom-metric"><div class="metric-value">{tspt_cost}</div><div class="metric-label">Transport Cost (£)</div></div>', unsafe_allow_html=True)
    ctd = np.round(tot_pick_cost + tspt_cost, 2)
    c5.markdown(f'<div class="custom-metric-ctd"><div class="metric-value">{ctd}</div><div class="metric-label">Cost To Deliver (£)</div></div>', unsafe_allow_html=True)

    line_break(c1, 3)
    line_break(c3, 3)
    line_break(c5, 3)
    
    ######### Miles travelled & Ship to coordinates #########
    if selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist():
        #selected_dist = pincode_df.loc[(pincode_df[name_or_number] == selected_ship_to), f'distance_{mapped_warehouse}'].values[0]
        #nearest_dist = pincode_df.loc[(pincode_df[name_or_number] == selected_ship_to), f'distance_{nearest_warehouse}'].values[0]
        miles_travelled = pincode_df.loc[(pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to), f'distance_{selected_warehouse}'].values[0]
        ship_to_cor = [pincode_df[pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to].SHIP_TO_LATITUDE.values[0], pincode_df[pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to].SHIP_TO_LONGTITUDE.values[0]]    
    elif selected_ship_to in dt8.SHIP_TO_NAME.unique().tolist():
        #selected_dist = dt8.loc[(dt8.SHIP_TO_NAME == selected_ship_to), f'distance_{mapped_warehouse}'].values[0]
        #nearest_dist = dt8.loc[(dt8.SHIP_TO_NAME == selected_ship_to), f'distance_{nearest_warehouse}'].values[0]
        miles_travelled = dt8.loc[(dt8.SHIP_TO_NAME == selected_ship_to), f'distance_{selected_warehouse}'].values[0]
        ship_to_cor = [dt8[dt8.SHIP_TO_NAME == selected_ship_to].latitude.values[0], dt8[dt8.SHIP_TO_NAME == selected_ship_to].longitude.values[0]]    
        
        
    # if selected_warehouse== nearest_warehouse:
    #     miles_saved = np.round(selected_dist - nearest_dist,2)
    # elif selected_warehouse!= nearest_warehouse:
    #     miles_saved=0

    
    ctd_per_unit = np.round(ctd/units,2)
    c1.markdown(f'<div class="custom-metric-ctd"><div class="metric-value">{ctd_per_unit}</div><div class="metric-label">CTD per case (£)</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="custom-metric-co2"><div class="metric-value">{int(miles_travelled)}</div><div class="metric-label">Miles to Travel</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="custom-metric-co2"><div class="metric-value">{np.round(miles_travelled* 1.4865,1)}</div><div class="metric-label">CO2 Footprint (kg)</div></div>', unsafe_allow_html=True)
    def values_reset():
        st.session_state['ship-to'] = "101046- NISA TODAY'S LTD"
        st.session_state['materials'] = []
        st.session_state['cost_per_case_pick'] = per_pickcost['per_case_pick']
        st.session_state['cost_per_pallet_pick'] =per_pickcost['per_pallet_pick']
        st.session_state['cost_per_keg_pick'] = per_pickcost['per_keg_pick']
        st.session_state['map']= map
        
    if st.button('Reset :arrows_counterclockwise:', on_click=values_reset):
        st.info('Values refreshed')
        

    ###### Map ############
    map_plot(ship_to_name, ship_to_city, ship_to_cor, cmap)



################ Comparison Table ###########
        
if selected_option=='Comparison Table':
    warehouse_list = ['DT4', 'DT8', 'NE2']
    warehouse = st.radio("Warehouse", warehouse_list, index=0, disabled=False, horizontal=True, label_visibility="visible")
    ##### For Ship-to Coordinates
    if selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist():
        ship_to_cor = [pincode_df[pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to].SHIP_TO_LATITUDE.values[0], pincode_df[pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to].SHIP_TO_LONGTITUDE.values[0]]    
    elif selected_ship_to in dt8.SHIP_TO_NAME.unique().tolist():
        ship_to_cor = [dt8[dt8.SHIP_TO_NAME == selected_ship_to].latitude.values[0], dt8[dt8.SHIP_TO_NAME == selected_ship_to].longitude.values[0]]
    
    pick_cost = dict()
    pick_cost['DT4']= {'Pickcost_per_case': 0.42, 'Pickcost_per_pallet':3.53, 'Pickcost_per_keg':0.42}
    pick_cost['DT8']= {'Pickcost_per_case': 0.42, 'Pickcost_per_pallet':2.38, 'Pickcost_per_keg':0.42}
    pick_cost['NE2']= {'Pickcost_per_case': 0.4, 'Pickcost_per_pallet':2.23, 'Pickcost_per_keg':0.4}
    
    cl, c1,cb1, c2, cb2, c3, cr = st.columns([0.1, 1, 0.5, 1, 0.5, 1, 0.3])
    for w in warehouse_list:
        globals()[f"{w}_pick_cost_case"] = pick_cost[f'{w}']['Pickcost_per_case']
        globals()[f"{w}_pick_cost_pallet"] = pick_cost[f'{w}']['Pickcost_per_pallet']
        globals()[f"{w}_pick_cost_keg"] = pick_cost[f'{w}']['Pickcost_per_keg']
        
    if warehouse:
        line_break(c1, 2)
        line_break(c2, 2)
        line_break(c3, 2)
        globals()[f"{warehouse}_pick_cost_case"] = c1.slider(f'**{warehouse} - Cost per Case pick**',0.00, 5.0, value= pick_cost[f'{warehouse}']['Pickcost_per_case'])
        globals()[f"{warehouse}_pick_cost_pallet"] = c2.slider(f'**{warehouse} - Cost per Pallet pick**',0.00, 5.0, value= pick_cost[f'{warehouse}']['Pickcost_per_pallet'])
        globals()[f"{warehouse}_pick_cost_keg"] = c3.slider(f'**{warehouse} -Cost per KEG pick**',0.00, 5.0, value= pick_cost[f'{warehouse}']['Pickcost_per_keg'])
        pick_cost[f'{warehouse}']['Pickcost_per_case'] = globals()[f"{warehouse}_pick_cost_case"]
        pick_cost[f'{warehouse}']['Pickcost_per_pallet'] = globals()[f"{warehouse}_pick_cost_pallet"]
        pick_cost[f'{warehouse}']['Pickcost_per_keg'] =globals()[f"{warehouse}_pick_cost_keg"]
        
      
    for w in warehouse_list:
        globals()[f"{w}_pallet_pick_cost"] = np.round(pallet_picks * pick_cost[f'{w}']['Pickcost_per_pallet'],2)
        globals()[f"{w}_case_pick_cost"] = np.round(case_picks * pick_cost[f'{w}']['Pickcost_per_case'],2)
        globals()[f"{w}_total_pick_cost"] = np.round(globals()[f"{w}_pallet_pick_cost"] + globals()[f"{w}_case_pick_cost"],2)
        globals()[f"{w}_pick_cost_per_case"] = np.round(globals()[f"{w}_total_pick_cost"]/ units ,2)
        if selected_ship_to in pincode_df['SHIP_TO_NUMBER_NAME'].unique().tolist():
            globals()[f"{w}_transport_cost"] = transport_cost(mapped_warehouse, w, int(pallet_transported) , postal_code)
            globals()[f"{w}_miles_travelled"] = int(pincode_df.loc[(pincode_df['SHIP_TO_NUMBER_NAME'] == selected_ship_to), f'distance_{w}'].values[0])
        elif selected_ship_to in dt8['SHIP_TO_NAME'].unique().tolist() and w =='DT8':
            globals()[f"{w}_transport_cost"] = np.round(dt8.loc[dt8.SHIP_TO_NUMBER_NAME==selected_ship_to, 'Per Pallet'].values[0], 2) * pallet_transported
            globals()[f"{w}_miles_travelled"] = int(dt8.loc[(dt8.SHIP_TO_NUMBER_NAME == selected_ship_to), f'distance_{w}'].values[0])
        elif selected_ship_to in dt8['SHIP_TO_NAME'].unique().tolist() and w!='DT8':
            line_break(st.sidebar, 1)
            custom_info(f'Transport cost not present from {w}, hence needed as user input')
            globals()[f"{w}_per_pallet_tspt_cost"]= st.sidebar.number_input(f'Transport cost/pallet - {w}', 0.00, 100.00,
                                                                                value = np.round(dt8['Per Pallet'].mean(), 2))
            globals()[f"{w}_transport_cost"] = np.round(globals()[f"{w}_per_pallet_tspt_cost"] * pallet_transported, 2)
            globals()[f"{w}_miles_travelled"] = np.round(dt8.loc[(dt8.SHIP_TO_NAME == selected_ship_to), f'distance_{w}'].values[0],2)
            
        globals()[f"{w}_CTD"] = np.round((globals()[f"{w}_total_pick_cost"] + globals()[f"{w}_transport_cost"]),2)
        globals()[f"{w}_CTD_per_case"] = np.round(globals()[f"{w}_CTD"]/units, 2)
        globals()[f"{w}_co2_footprint"] = np.round(globals()[f"{w}_miles_travelled"] * 1.4865, 1)
    
    line_break(st, 3)       
    df=pd.DataFrame()
    df['Warehouse'] = warehouse_list
    df['Case Pick Costs'] = [DT4_case_pick_cost, DT8_case_pick_cost, NE2_case_pick_cost]
    df['Pallet Pick Costs'] = [DT4_pallet_pick_cost, DT8_pallet_pick_cost, NE2_pallet_pick_cost]
    df['Total Pick Costs'] = [DT4_total_pick_cost, DT8_total_pick_cost, NE2_total_pick_cost]
    df['Pick Cost/ Case'] = [DT4_pick_cost_per_case, DT8_pick_cost_per_case, NE2_pick_cost_per_case]
    df['Transport Cost'] = [DT4_transport_cost, DT8_transport_cost, NE2_transport_cost]
    df['Cost to Deliver'] = [DT4_CTD, DT8_CTD, NE2_CTD]
    df['CTD/ case'] = [DT4_CTD_per_case, DT8_CTD_per_case, NE2_CTD_per_case]
    df['Miles to Travel'] = [DT4_miles_travelled, DT8_miles_travelled, NE2_miles_travelled]
    df['CO2 Footprint (kg)'] = [DT4_co2_footprint, DT8_co2_footprint, NE2_co2_footprint]
    
    st.dataframe(df, use_container_width=True)
    line_break(st, 2)
    cl, c, cr = st.columns([0.5, 1, 0.5])
    
    ####### For Saving the scenario ############

    data = convert_df(df)
    scenario_save_button = cl.download_button( label = "Save Scenario", data=data , file_name = f"Scenario_{str(datetime.now())}.csv",
                       mime = "text/csv", key='download-csv')
    
    coordinates_df=pd.DataFrame({'Coordinates': ['DT4', 'NE2', 'DT8'], 'LAT': [52.885948, 55.833390, 53.314417],
                            'LON':[-1.701790, -3.924020, -2.655691]})
    map = folium.Map(location=[54.314417, 4.0], zoom_start=6, control_scale=True)
    for i,row in coordinates_df.iterrows():
        iframe = folium.IFrame('Warehouse:' + str(row["Coordinates"]))

        popup = folium.Popup(iframe, min_width=120, max_width=200)

        folium.Marker(location=[row['LAT'],row['LON']],
                    popup = popup, c=row['Coordinates']).add_to(map)

    iframe2 = folium.IFrame(f'{selected_ship_to} - {ship_to_city}')
    popup2 = folium.Popup(iframe2, min_width=150, max_width=120)
    folium.Marker(ship_to_cor, popup = popup2, icon=folium.Icon(color='green')).add_to(map)
    with c:
        st_map = st_folium(map, width=1500, height = 400, key='map')
    line_break(st, 3)


if selected_option=='Segmentation':
    
    with st.sidebar:
        colx, coly, colz = st.columns([1,1.2,1])
        with coly:
            st.image("imgs\Diageo-Logo-Gold.png", width=100, use_column_width=True, output_format ="PNG") 
            st.image("imgs\heartbeat_logo-removebg.png", width=50, use_column_width=True, output_format ="PNG")
            
    c1, c2, c3, c4, c5, c6, c7,c8,c9 = st.columns([1.3,0.2,1,0.2,1,0.2,1,0.2,1])
    with c1:
        analysis_option = option_menu(
            menu_title = None,
            options = ["Generate Segments", "Sold-to analysis", "Segment analysis"],
            icons = ["gear-fill", "person-vcard", "segmented-nav"],
            default_index = 0,
            orientation = "vertical",
            styles={
            "nav-link-selected": {"background-color": "none", "color": "#2B78BD"},
            "nav-link": {"font-size": "14px", "background-color": "transparent"}
        }
        )
        line_break(st.sidebar, 3)
        custom_write_style = """
        <style>
        .custom-markdown{
            display: inline-block;
            padding: 10px 20px;
            background-color: gray;
            color: #FFFFFF;
            width: 300px; 
            height: 50px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            text-decoration: none;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s;
        }
        </style>"""
        st.markdown(custom_write_style, unsafe_allow_html=True)
        
    
    if analysis_option in ("Sold-to analysis", "Segment analysis"):
        selected_sold_to = st.sidebar.selectbox('**Sold to**', df_segments.SOLD_TO_NAME.tolist(), key='sold-to')
        comp1, comp2, comp3, comp4 = st.columns([1,1,1,1])
        sold_to_number = df_segments.loc[df_segments.SOLD_TO_NAME == selected_sold_to, 'SOLD_TO_NUMBER'].values[0]
        mapped_segment = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'New Segment'].values[0]
        
        line_break(st.sidebar,2)
        st.sidebar.markdown('<p style="color: white; font-weight:bold">Segment</p>', unsafe_allow_html=True)
        st.sidebar.markdown(f'<div class="custom-markdown">{str.upper(mapped_segment)}</div>', unsafe_allow_html=True)
        
        
        recency = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Recency'].values[0]
        frequency = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Frequency'].values[0]
        netval = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'NET_VALUE'].values[0]
        units = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'UNITS'].values[0]
        pick_cost = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'TOTAL_PICK_COST'].values[0]
        tspt_cost = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'TRANSPORT_COST'].values[0]
        cost_per_deliv = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Cost_per_Delivery'].values[0]
        cases_per_deliv = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Cases_per_Delivery'].values[0]
        netval_per_deliv = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'NetValue_per_Delivery'].values[0]
        cost_per_case = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Cost_per_Case'].values[0]
        unique_skus = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Unique_MATERIAL'].values[0]
        total_shiptos = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Shipto_count'].values[0]
        
        segment_recency = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Recency'].mean()
        segment_frequency = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Frequency'].mean()
        segment_netval = df_segments.loc[df_segments['New Segment'] == mapped_segment,'NET_VALUE'].mean()
        segment_units = df_segments.loc[df_segments['New Segment'] == mapped_segment,'UNITS'].mean()
        segment_pick_cost = df_segments.loc[df_segments['New Segment'] == mapped_segment,'TOTAL_PICK_COST'].mean()
        segment_tspt_cost = df_segments.loc[df_segments['New Segment'] == mapped_segment,'TRANSPORT_COST'].mean()
        segment_cost_per_deliv = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Cost_per_Delivery'].mean()
        segment_cases_per_deliv = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Cases_per_Delivery'].mean()
        segment_netval_per_deliv = df_segments.loc[df_segments['New Segment'] == mapped_segment,'NetValue_per_Delivery'].mean()
        segment_cost_per_case = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Cost_per_Case'].mean()
        segment_unique_skus = df_segments.loc[df_segments['New Segment'] == mapped_segment,'Unique_MATERIAL'].mean()
        segment_total_shiptos = df_segments.loc[df_segments.SOLD_TO_NUMBER == int(sold_to_number),'Shipto_count'].values[0]
        
        df_segments_grouped= df_segments.groupby(by='New Segment').agg({
            'SOLD_TO_NUMBER': 'nunique',
            'Recency': 'mean',
            'Frequency':'mean',
            'UNITS': 'mean',
            'TOTAL_PICK_COST': 'mean',
            'TRANSPORT_COST': 'mean',
            'NET_VALUE': 'mean',
            'Unique_MATERIAL': 'mean',
            'Shipto_count': 'mean',
            'Cost_per_Delivery': 'mean',
            'NetValue_per_Delivery': 'mean',
            'Cases_per_Delivery': 'mean',
            'Cost_per_Case': 'mean'
        }).reset_index()
        
        column_placeholder =["New Segment", "Sold-to", "Recency", "Frequency", "Units", "Pick cost", "Transport cost", "Net value", "Material count",
                            "Shipto count", "Cost/delivery", "NetValue/delivery", "Cases/delivery", "Cost/case"]

        df_segments_grouped.columns = column_placeholder
        
        df_segments_grouped =pd.pivot_table(df_segments_grouped, columns='New Segment').reset_index().rename({'index': 'Metrics'}, axis=1)
        df_segments_grouped.columns.name=None
        df_segments_grouped = df_segments_grouped.set_index('Metrics').reindex(index =column_placeholder[1:]).reset_index()
        line_break(st,3)
        
######### Clustering Algorithm ###################
    def generate_segments(algorithm, primary_clusters, secondary_clusters, feature_list):
        algo_dict={'K-Means': KMeans, 'Mini-Batch K-Means': MiniBatchKMeans, 'Agglomerative Clustering': AgglomerativeClustering}
        scaler = MinMaxScaler()
        df_soldto = soldto_data
        df_soldto_scaled = scaler.fit_transform(df_soldto[feature_list])
        model = algo_dict[algorithm](n_clusters=primary_clusters).fit(df_soldto_scaled)
        model_labels = model.labels_
        df_model = df_soldto.copy()
        df_model['Clusters'] = model_labels
        primary_score = silhouette_score(df_soldto_scaled, model_labels).round(2)
        
        biggest_cluster = df_model['Clusters'].value_counts().idxmax()
        sec_df = df_model[df_model.Clusters == int(biggest_cluster)]
        scaler = MinMaxScaler()
        sec_df_scaled = scaler.fit_transform(sec_df[feature_list])
        sec_model = KMeans(n_clusters= secondary_clusters).fit(sec_df_scaled)
        secondary_labels = sec_model.labels_
        sec_df['Secondary_Clusters'] = secondary_labels
        sec_df.Secondary_Clusters = sec_df.Secondary_Clusters.replace({0:(biggest_cluster+0.1), 1:(biggest_cluster+0.2)
                                                                    , 2:(biggest_cluster+0.3)})
        df_results = df_model.merge(sec_df, on=df_model.columns.tolist(), how='left')
        df_results['Secondary_Clusters'].fillna(df_results['Clusters'], inplace=True)
        df_results.rename({'Secondary_Clusters': 'New Clusters'}, axis=1, inplace=True)
        final_score = np.round(silhouette_score(df_soldto_scaled, df_results['New Clusters']),2)
        cluster_analysis = df_results.groupby(by= 'New Clusters').agg({'SOLD_TO_NUMBER': 'nunique',
                                        'Recency': 'mean',
                                        'Frequency':'mean',
                                        'Units': 'mean',
                                        'Net Value': 'mean',
                                        'Pick Cost': 'mean',
                                        'Transport Cost': 'mean',
                                        'Distinct SKUs': 'mean',
                                        'Cost/Delivery': 'mean',
                                        'Net Value/Delivery': 'mean',
                                        'Cases/Delivery': 'mean',
                                        'Cost/Case': 'mean',
                                        'Shipto count': 'mean'
                                        }).reset_index().rename({'SOLD_TO_NUMBER': '#Sold-to'}, axis=1).round(2)
        st.info(f'Silhouette Score: {final_score}')
        cluster_analysis.loc[cluster_analysis['Net Value']==cluster_analysis['Net Value'].max(), 'New Segments']= 'Key Customers'
        cluster_analysis.loc[cluster_analysis['#Sold-to']==cluster_analysis['#Sold-to'].max(), 'New Segments']= 'Consistent Buyers'
        cluster_analysis.loc[cluster_analysis['Net Value']==cluster_analysis['Net Value'].nlargest(2).iloc[-1], 'New Segments']= 'Potential Big Players'
        cluster_analysis.loc[cluster_analysis['Recency']==cluster_analysis['Recency'].max(), 'New Segments']= 'Occassional/Inactive Customers'
        cluster_analysis.loc[cluster_analysis['Recency']==cluster_analysis['Recency'].nlargest(2).iloc[-1], 'New Segments']= 'Range Seekers'
        
        clusters_mapping = dict(zip(cluster_analysis['New Clusters'], cluster_analysis['New Segments']))
        df_results['New Segments'] = df_results['New Clusters'].map(clusters_mapping)
        
        cluster_analysis = cluster_analysis.reindex(columns= ['New Segments','#Sold-to','Recency', 'Frequency', 'Net Value','Units', 'Pick Cost','Transport Cost','Distinct SKUs',
                                           'Cost/Delivery','Net Value/Delivery', 'Cases/Delivery', 'Cost/Case', 'Shipto count'])
        
        st.dataframe(cluster_analysis, use_container_width= True)
        
        data = convert_df(df_results)
        save_segments_button = st.download_button(label = "Save Segments", data=data , file_name = f"Segments_{str(datetime.now())}.csv",
                       mime = "text/csv", key='download-segments')
        
        df_results['New Segments'] =df_results['New Segments'].apply(lambda x: str(x))
        fig =px.scatter_3d(df_results, x='Recency', y='Frequency', z='Net Value',color='New Segments', title= 'New Segments', 
                   height = 800, width = 800)
        st.plotly_chart(fig, use_container_width=True)
        


    features_list = ['Recency', 'Frequency', 'Net Value', 'Pick Cost','Transport Cost', 'Units', 'Cost/Delivery', 'Cases/Delivery', 'Net Value/Delivery',
                     'Cost/Case']
    if analysis_option =="Generate Segments":
        #@st.cache_data
        def generate_solto_data():
            df_transport = pd.read_csv(r'C:\Users\singhkis\Diageo\HB Data Science Working Group - General\Shared_Folder\CTS_Clustering_Python_Local\Clustering_python_local\data\F_TRANSPORT_FY23_Updated.csv',
                            low_memory= False)
            df_pick = pd.read_csv(r'C:\Users\singhkis\Diageo\HB Data Science Working Group - General\Shared_Folder\CTS_Clustering_Python_Local\Clustering_python_local\data\F_PICK_FY23_Updated.csv',
                            low_memory= False)
            df_shipto_cust = pd.read_csv(r'C:\Users\singhkis\Diageo\HB Data Science Working Group - General\Shared_Folder\CTS_Clustering_Python_Local\Clustering_python_local\data\ship_to_cust.csv')
            df_likp = pd.read_excel(r'C:\Users\singhkis\Diageo\HB Data Science Working Group - General\Shared_Folder\CTS_Clustering_Python_Local\Clustering_python_local\data\LIKP_FY_23.xlsx')
            df_del_netval = pd.read_excel(r'C:\Users\singhkis\Diageo\HB Data Science Working Group - General\Shared_Folder\CTS_Clustering_Python_Local\Clustering_python_local\data\FY22_FY23_Del_Value.xlsx')
            
            df_pick.rename({'DELIVERY_NUMBER_LINE_ITEM': 'LINE_ITEM', 'TOTAL_PRICE': 'TOTAL_PICK_COST'}, axis = 1, inplace=True)
            df_transport.rename({'TRUCK_UTILIZATION': 'TRUCK_UTILIZATION_%', 'EXTENDED_COST_WITHTAX': 'TRANSPORT_COST'}, axis=1, inplace=True)
            df_pick_transport = df_pick.merge(df_transport, on=['DELIVERY_NUMBER', 'LINE_ITEM'], how='left', suffixes=('', '_copy'))
            df_pick_transport.drop([col for col in df_pick_transport.columns if '_copy' in col], axis = 1, inplace=True)
            
            df_likp['Sold-To Pt'] = df_likp['Sold-To Pt'].astype(str).apply(lambda x: x.split('.')[0])
            df_likp['Ship-To'] = df_likp['Ship-To'].astype(str).apply(lambda x: x.split('.')[0])

            df_pick_transport_shipto = df_pick_transport.merge(df_likp[['Ship-To', 'Sold-To Pt']].drop_duplicates(), left_on='SHIP_TO_NUMBER',right_on ='Ship-To', how='left')
            df_pick_transport_shipto.rename({'Sold-To Pt': 'SOLD_TO_NUMBER'}, axis=1, inplace=True)
            df_pick_transport_shipto.drop(columns = ['Ship-To'], axis=1) 
            new_df = df_pick_transport_shipto.copy()
            cols_to_use = ['DELIVERY_NUMBER','LINE_ITEM', 'UNITS','DELIVERY_DATE', 'MATERIAL', 'TOTAL_PICK_COST', 'TRANSPORT_COST',
                'SHIP_TO_NUMBER', 'SHIP_TO_NAME', 'SOLD_TO_NUMBER','TRUCK_UTILIZATION_%' ]
            df = new_df[cols_to_use]
            df['DELIVERY_DATE'] = pd.to_datetime(df['DELIVERY_DATE'])
            current_date = df['DELIVERY_DATE'].max()
            df_deliv = df.groupby(by= ['DELIVERY_NUMBER','DELIVERY_DATE','SHIP_TO_NUMBER', 'SHIP_TO_NAME', 'SOLD_TO_NUMBER']).agg(
            {'UNITS':'sum', 'TOTAL_PICK_COST':'sum', 'TRANSPORT_COST':'first'}).reset_index()
            
            df_deliv_merged = df_deliv.merge(df_del_netval, left_on='DELIVERY_NUMBER', right_on = 'Delivery Number', how='left').drop(
                columns = 'Delivery Number', axis=1).rename({'Net Value': 'NET_VALUE'}, axis=1)
            df_deliv_merged.DELIVERY_DATE = pd.to_datetime(df_deliv_merged.DELIVERY_DATE)
            max_date = df_deliv_merged.DELIVERY_DATE.max()
            
            df_soldto = df_deliv_merged.groupby(by = ['SOLD_TO_NUMBER']).agg(
                {'DELIVERY_DATE':lambda x: (max_date - x.max()).days,
                'DELIVERY_NUMBER':'nunique',
                'NET_VALUE': 'sum',
                'SHIP_TO_NUMBER': 'nunique',
                'UNITS':'sum',
                'TOTAL_PICK_COST':'sum',
                'TRANSPORT_COST':'sum'}).rename(columns={'DELIVERY_DATE': 'Recency',
                                                    'DELIVERY_NUMBER':'Frequency', 'UNITS':'Units',
                                                    'NET_VALUE': 'Net Value', 'TOTAL_PICK_COST': 'Pick Cost', 'TRANSPORT_COST':'Transport Cost',
                                                    'SHIP_TO_NUMBER':'Shipto count'}).reset_index()
                
            df_soldto['Total Cost'] = df_soldto['Pick Cost'] + df_soldto['Transport Cost']
            df_soldto['Cost/Delivery'] = df_soldto['Total Cost']/ df_soldto['Frequency']
            df_soldto['Net Value/Delivery'] = df_soldto['Net Value']/ df_soldto['Frequency']
            df_soldto['Cost/Case'] = df_soldto['Total Cost']/ df_soldto['Units']
            df_soldto['Cases/Delivery'] = df_soldto['Units']/ df_soldto['Frequency']
            
            ##### For unique Material

            df_soldto_material = df.groupby('SOLD_TO_NUMBER').agg({'MATERIAL': 'nunique'}).reset_index().rename({'MATERIAL': 'Distinct SKUs'}, axis=1)
            df_soldto = df_soldto.merge(df_soldto_material, on='SOLD_TO_NUMBER', how='left')
            
            return df_soldto
        
        soldto_data= generate_solto_data()
        
        #selected_fy = st.sidebar.selectbox('**Financial year**',['FY23', 'FY22 + FY23'] , key='fy')
        selected_algorithm = st.sidebar.selectbox('**Clustering algorithm**',['K-Means', 'Mini-Batch K-Means', 'Agglomerative Clustering'] , key='algo')
        primary_clusters = st.sidebar.selectbox('**Primary Clusters**',[2,3,4,5] , key='prim_clusters', index=1)
        secondary_clusters = st.sidebar.selectbox('**Secondary Clusters**',[0,2,3,4] , key='sec_clusters', index=2)
        selected_features = st.sidebar.multiselect('**Features**', features_list ,default=['Recency', 'Frequency', 'Net Value'], key='features')
        if secondary_clusters!=0:
            custom_info(f"Total Segments going to be formed: {primary_clusters+ secondary_clusters -1}")
        else: custom_info(f"Total clusters: {primary_clusters}")
        
        line_break(st.sidebar,2)
        
        if st.sidebar.button('Generate Clusters'):
            generate_segments(selected_algorithm, primary_clusters, secondary_clusters, selected_features)
########################################################
    if analysis_option =="Sold-to analysis":
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{recency}</div><div class="metric-label">Recency</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{frequency}</div><div class="metric-label">Frequency</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(netval/10e5, 2)}M</div><div class="metric-label">Net Value</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(units/10e2, 2)}K</div><div class="metric-label">Units</div></div>', unsafe_allow_html=True)
        
        line_break(c3,2)
        line_break(c5,2)
        line_break(c7,2)
        line_break(c9,2)
        
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{total_shiptos}</div><div class="metric-label">Ship-to Count</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(pick_cost/10e2, 2)}K</div><div class="metric-label">Pick Cost</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(tspt_cost/10e2, 2)}K</div><div class="metric-label">Transport Cost</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{int(unique_skus)}</div><div class="metric-label">SKU count</div></div>', unsafe_allow_html=True)
        
        line_break(c3,2)
        line_break(c5,2)
        line_break(c7,2)
        line_break(c9,2)
        
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(cost_per_deliv/10e2,2)}K</div><div class="metric-label">Cost per delivery</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(netval_per_deliv/10e2, 2)}K</div><div class="metric-label">Net Value/ delivery</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(cases_per_deliv, 2)}</div><div class="metric-label">Cases per delivery</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(cost_per_case, 2)}</div><div class="metric-label">Cost per case</div></div>', unsafe_allow_html=True)
    
    
    if analysis_option =="Segment analysis":
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_recency,2)}</div><div class="metric-label">Recency</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_frequency,2)}</div><div class="metric-label">Frequency</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_netval/10e5, 2)}M</div><div class="metric-label">Net Value</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_units/10e2, 2)}K</div><div class="metric-label">Units</div></div>', unsafe_allow_html=True)
        
        line_break(c3,2)
        line_break(c5,2)
        line_break(c7,2)
        line_break(c9,2)
        
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_total_shiptos,2)}</div><div class="metric-label">Ship-to Count</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_pick_cost/10e2, 2)}K</div><div class="metric-label">Pick Cost</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_tspt_cost/10e2, 2)}K</div><div class="metric-label">Transport Cost</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{int(segment_unique_skus)}</div><div class="metric-label">SKU count</div></div>', unsafe_allow_html=True)
        
        line_break(c3,2)
        line_break(c5,2)
        line_break(c7,2)
        line_break(c9,2)
        
        c3.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_cost_per_deliv/10e2,2)}K</div><div class="metric-label">Cost/Delivery</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_netval_per_deliv/10e2, 2)}K</div><div class="metric-label">Net Value/Delivery</div></div>', unsafe_allow_html=True)
        c7.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_cases_per_deliv, 2)}</div><div class="metric-label">Cases/Delivery</div></div>', unsafe_allow_html=True)
        c9.markdown(f'<div class="custom-metric"><div class="metric-value">{np.round(segment_cost_per_case, 2)}</div><div class="metric-label">Cost/Case</div></div>', unsafe_allow_html=True)
        
        #############################
        df = df_segments_grouped

        # Normalize the data
        df_normalized = df_segments_grouped.set_index('Metrics').div(df_segments_grouped.set_index('Metrics').sum(axis=1), axis=0).reset_index().round(3)
        
        colors = ['#FF6361', '#58508D', '#FFA600', '#003F5C', '#FFB5A7']

        # Create stacked bar chart using Plotly graph objects
        fig = go.Figure()

        for i, series in enumerate(df_normalized.columns[1:]):
            fig.add_trace(go.Bar(
                x=df_normalized['Metrics'],
                y=df_normalized[series],
                name=str(series),
                text=np.round(df[series], 2),
                hovertemplate='%{text}',
                textposition='none',
                marker=dict(color=colors[i % len(colors)])  # Assign colors from the custom colorscale
            ))

        fig.update_layout(
            xaxis=dict(title='Features'),
            yaxis=dict(title='Segment values', showticklabels=False, range=[0, 1]),
            barmode='stack',
            plot_bgcolor='rgba(0,0,0,0)',  # Set background to transparent
            paper_bgcolor='rgba(0,0,0,0)'  # Set plot area background to transparent
        )
        cx,cy = st.columns([1,4])
        line_break(cx,2)
        line_break(cy,2)
        with cy: 
            st.plotly_chart(fig, use_container_width = True)
    
    style2 = """
    <style>
    .custom-metric {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }

    .custom-metric::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2%;
        background-color: #3498db;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
    }

    .custom-metric .metric-value {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #2B78BD;
    }

    .custom-metric .metric-label {
        font-size: 14px;
        color: #777;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.25rem;
    }

    </style>
    """

    # Apply the custom styles using st.markdown with unsafe_allow_html=True
    st.markdown(style2, unsafe_allow_html=True)
    
    
    ##################
line_break(st,2)       
st.markdown('<p style="text-align: center; color: gray;">Made with ❤️ by Hearbeat Advance Analytics team</p>', unsafe_allow_html=True)

hide_footer = """ <style> #MainMenu {visibility: hidden;} footer {visibility: hidden;} </style> """
st.markdown(hide_footer, unsafe_allow_html=True)