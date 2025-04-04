import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
#from recommendations import *
import base64

#st.logo("pngegg.png", icon_image="pngegg.png")
st.set_page_config(layout='wide', page_title='IB-ILD AP', page_icon="⚡")

##########################################

# @st.cache_data
# def load_data():
#     NDC_final_scoring_df= pd.read_csv(r"data_eng\interm_ds\NDC_final_scoring_df.csv", dtype={'Cluster': str})
#     DC_final_scoring_df= pd.read_csv(r'data_eng\interm_ds\DC_final_scoring_df.csv', dtype={'Cluster': str})
#     weightage_df= pd.read_csv(r"data_eng\interm_ds\weightage_df.csv", dtype={'Cluster': str})
#     total_vio_df= pd.read_csv(r"data_eng\interm_ds\total_vio_df.csv", dtype={'Cluster': str})
#     NDC_final_scoring_df['Current_GS'].fillna('NA', inplace=True)
#     DC_final_scoring_df['Current_GS'].fillna('NA', inplace=True)
#     return NDC_final_scoring_df,DC_final_scoring_df, weightage_df, total_vio_df

# NDC_final_scoring_df ,DC_final_scoring_df, weightage_df, total_vio_df= load_data()

################# Functions #####################
def line_break(comp, num_breaks):
    for i in range(num_breaks):
        comp.markdown('\n')

# def recommendation_results(coverage_strategy, user_input_params):
#     if coverage_strategy=="No Double Coverage":
#         selected_weightage_df, final_scoring_df_2 = simulate_priority_based_recommendations_NDC(user_input_params,NDC_final_scoring_df,weightage_df,total_vio_df)
#         final_recommendation_df= extract_reco_skus(final_scoring_df_2, selected_weightage_df)
#         akd_summary, store_summary, cluster_summary= reco_summary(final_recommendation_df)

#     else:
#         selected_weightage_df, final_scoring_df_2= simulate_priority_based_recommendations_DC(user_input_params,DC_final_scoring_df,weightage_df,total_vio_df)
#         final_recommendation_df= extract_reco_skus(final_scoring_df_2, selected_weightage_df)
#         akd_summary, store_summary, cluster_summary= reco_summary(final_recommendation_df)
    
#     return final_recommendation_df, akd_summary, store_summary, cluster_summary

def process_priority_value(priority, value):
    if priority == 'Coverage Strategy':
        return value
    else:
        return value / 100

def modify_user_params(user_input_params):
    mapping = {
        "VIO Coverage": "VIO_Coverage_Perc", 
        "Historical Sales Coverage": "Sales_Coverage_Perc",
        "Projected Sales Growth": 'Projected_Sales_growth%',
        'Coverage Strategy': "Strategy_Coverage"
    }
    try:
        if user_input_params['parameters']['Coverage Strategy']=='Double Coverage':
            priority = {int(k): mapping[v] for k, v in user_input_params["priority"].items()}
            parameters = {mapping[k]: v for k, v in user_input_params["parameters"].items()}
            formatted_params = {'priority': priority,'parameters': parameters,
                                'strategy_coverage':user_input_params['strategy_coverage'],
                                'strategy_order': user_input_params['strategy_order']}
    except:
        priority = {int(k): mapping[v] for k, v in user_input_params["priority"].items()}
        parameters = {mapping[k]: v for k, v in user_input_params["parameters"].items()}
        formatted_params = {'priority': priority,'parameters': parameters}

    return formatted_params

###########################################
st.markdown("""
    <style>
        /* Hide the Streamlit watermark */
        .stApp .css-1vbd788.egzxvld1 {
            display: none;
        }

        /* Header styles */
        .header {
            background-color: #388E3C; /* Green background for the header */
            color: #FFFFFF; /* White text color for the header */
            padding: 10px;
            padding-left: 100px;
            font-family: 'Roboto';
            font-size: 28px;
            font-weight: bold;
            position: fixed; /* Fix the header at the top */
            top: 0;
            left: 0;
            width: 100%; /* Full width */
            z-index: 1000; /* Ensure it stays on top of other content */
            display: flex;
            align-items: center; /* Align items vertically */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Optional: Add shadow for better separation */
        }

        /* Ensure content is below the header */
        .main {
            padding-top: 60px; /* Adjust padding to ensure content is not hidden behind the header */
        }

        /* Tab styles */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #FFFFFF; /* White background for the tabs */
            margin-bottom: 20px;
            margin-top: -70px; /* Adjust this value to lift the tabs closer to the header */
            border-bottom: none;  /* No bottom border */
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF; /* White background for each tab */
            color: #000000; /* Black text color for the tabs */
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 0;
            border-bottom: none;  /* No bottom border */
        }
        .stTabs [aria-selected="true"] {
            border-bottom: none;  /* Remove the green underline from the selected tab */
            color: #388E3C; /* Green text color for the selected tab */
        }

        /* Green background for sections */
        .green-background {
            background-color: #E3F1E7; /* Light green background for sections */
            padding: 20px;
            border-radius: 5px;
            margin-top: 0px; /* Reduce or remove margin to move it upwards */
        }

        /* Final result box */
        .final-result {
            background-color: #FFFFFF; /* White background for the final result box */
            padding: 20px;
            border: 1px solid #DDDDDD; /* Light grey border */
            border-radius: 10px;
            margin-top: 20px;
        }

        /* Container styling */
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Slider customization */
        .stSlider .baseweb-slider__thumb {
            background-color: #388E3C; /* Green color for the slider thumb */
        }

        /* Dropdown and select box styling */
        .stSelectbox {
            border: none; /* Remove border */
        }
        .stSelectbox .css-1r7d5t1 {
            border: none; /* Remove border from select box */
            color: #000000; /* Black text color for the select box */
        }
        .stSelectbox .css-1r7d5t1 .css-1c2ji3i {
            color: #000000; /* Black text color for dropdown items */
        }
        .stSelectbox .css-1r7d5t1 .css-1c2ji3i:hover {
            background-color: #E8F5E9; /* Light green background on hover */
        }

        /* Add space between slicers */
        .slicer-container > div {
            margin-bottom: 20px; /* Adjust spacing between slicers */
        }
        div.stButton > button {
            background-color: #388E3C; /* Match green tone of header */
            color: #FFFFFF; /* White font */
            border: none; /* No border */
            padding: 10px 20px; /* Add padding for a rectangular button shape */
            font-size: 16px; /* Font size */
            font-weight: bold; /* Bold text */
            border-radius: 5px; /* Rectangular button shape */
            cursor: pointer; /* Pointer cursor on hover */
        }

        /* Change button color on hover to a lighter green */
        div.stButton > button:hover {
            background-color: #4CAF50;
            color: #FFFFFF; /* Lighter green for hover effect */
        }
    </style>
""", unsafe_allow_html=True)

# Main container for wider layout
st.markdown('<div class="container">', unsafe_allow_html=True)

st.markdown("""
    <div class="header">
        Assortment Tool
    </div>
""", unsafe_allow_html=True)

# Tabs
tabs = st.tabs(["Simulation", "Recommendation","Additional Recommendation" ,"Model Recommendation Action Log"])

default_values_no_double = {
    "VIO Coverage": 70,
    "Projected Sales Growth": 12,
    "Historical Sales Coverage": 60
}

default_values_double = {
    "VIO Coverage": 50,
    "Projected Sales Growth": 10,
    "Historical Sales Coverage": 30
}

def get_default_value(kpi, coverage_strategy, default_dict= default_values_double):
    if coverage_strategy == "Double Coverage":
        return default_values_double.get(kpi)
    else:
        return default_values_no_double.get(kpi)

# def adjust_sliders(slider_vals, active_idx):
#     total = sum(slider_vals)
#     if total != 100:
#         remaining = 100 - slider_vals[active_idx]
#         other_vals = [slider_vals[i] for i in range(4) if i != active_idx]
#         distributed = remaining / 3
        
#         # Update the non-active sliders
#         for i in range(4):
#             if i != active_idx:
#                 slider_vals[i] = distributed
#     return slider_vals


default_values={"VIO Coverage": 50, "Historical Sales Coverage": 50, "Projected Sales Growth": 30}

with tabs[0]:
    line_break(st,2)
    st.markdown("""
        <div class="green-background">
            <h5>Set Prioritization</h5> </div>""", unsafe_allow_html=True)
    line_break(st,2)

# Define KPI options
    kpi_options = ["VIO Coverage", 'Projected Sales Growth', 'Historical Sales Coverage', 'Coverage Strategy']

# Function to filter KPI options
    def filter_options(selected_options):
        return [kpi for kpi in kpi_options if kpi not in selected_options]

# Layout
    col1, col_br1, col2, col_br2, col3, col_br3, col4, col_br4, col5 = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1])

    selected_options = []

    # First priority
    with col1:
        first_priority = st.selectbox(":one: First Priority KPI", filter_options(selected_options), key="first_priority")
        selected_options.append(first_priority)
        if first_priority == "Coverage Strategy":
            coverage_strategy= first_priority
            first_priority_value = st.selectbox("Select Coverage Strategy", options=["No Double Coverage", "Double Coverage"])
            coverage_strategy= first_priority_value
            if first_priority_value == "Double Coverage":
                with st.popover("Strategy split"):
                    premium_strategy_perc= st.slider("Premium Strategy", 0, 100, 25)
                    best_strategy_perc= st.slider("Best Strategy", 0, 100, 25)
                    better_strategy_perc= st.slider("Better Strategy", 0, 100, 25)
                    good_strategy_perc= st.slider("Good Strategy", 0, 100, 25)
                st.write(f"""Premium: {premium_strategy_perc}%, Best: {best_strategy_perc}%, Better: {better_strategy_perc}%, Good: {good_strategy_perc}%,
                          Total:{premium_strategy_perc+best_strategy_perc+better_strategy_perc+good_strategy_perc}%""")
        else:
            first_priority_value= st.slider(f"{first_priority}", 0, 100, default_values[first_priority], key="first_priority_slider")

    # Second priority
    with col2:
        second_priority = st.selectbox(":two: Second Priority KPI", filter_options(selected_options), key="second_priority")
        selected_options.append(second_priority)
        if second_priority == "Coverage Strategy":
            second_priority_value = st.selectbox("Select Coverage Strategy", options=["No Double Coverage", "Double Coverage"])
            coverage_strategy= second_priority_value
            if second_priority_value == "Double Coverage":
                with st.popover("Strategy split"):
                    premium_strategy_perc= st.slider("Premium Strategy", 0, 100, 25)
                    best_strategy_perc= st.slider("Best Strategy", 0, 100, 25)
                    better_strategy_perc= st.slider("Better Strategy", 0, 100, 25)
                    good_strategy_perc= st.slider("Good Strategy", 0, 100, 25)
                st.write(f"""Premium: {premium_strategy_perc}%, Best: {best_strategy_perc}%, Better: {better_strategy_perc}%, Good: {good_strategy_perc}%,
                          Total:{premium_strategy_perc+best_strategy_perc+better_strategy_perc+good_strategy_perc}%""")
        else:
            second_priority_value= st.slider(f"{second_priority}", 0, 100, default_values[second_priority], key="second_priority_slider")

    # Third priority
    with col3:
        third_priority = st.selectbox(":three: Third Priority KPI", filter_options(selected_options), key="third_priority")
        selected_options.append(third_priority)
        if third_priority == "Coverage Strategy":
            third_priority_value = st.selectbox("Select Coverage Strategy", options=["No Double Coverage", "Double Coverage"])
            coverage_strategy= third_priority_value
            if third_priority_value == "Double Coverage":
                with st.popover("Strategy split"):
                    premium_strategy_perc= st.slider("Premium Strategy", 0, 100, 25)
                    best_strategy_perc= st.slider("Best Strategy", 0, 100, 25)
                    better_strategy_perc= st.slider("Better Strategy", 0, 100, 25)
                    good_strategy_perc= st.slider("Good Strategy", 0, 100, 25)
                st.write(f"""Premium: {premium_strategy_perc}%, Best: {best_strategy_perc}%, Better: {better_strategy_perc}%, Good: {good_strategy_perc}%,
                          Total:{premium_strategy_perc+best_strategy_perc+better_strategy_perc+good_strategy_perc}%""")
        else:
            third_priority_value= st.slider(f"{third_priority}", 0, 100, default_values[third_priority], key="third_priority_slider")

    # Fourth priority
    with col4:
        fourth_priority = st.selectbox(":four: Fourth Priority KPI", filter_options(selected_options), key="fourth_priority")
        selected_options.append(fourth_priority)
        if fourth_priority == "Coverage Strategy":
            fourth_priority_value = st.selectbox("Select Coverage Strategy", options=["No Double Coverage", "Double Coverage"])
            coverage_strategy= fourth_priority_value
            if fourth_priority_value == "Double Coverage":
                with st.popover("Strategy split"):
                    premium_strategy_perc= st.slider("Premium Strategy", 0, 100, 25)
                    best_strategy_perc= st.slider("Best Strategy", 0, 100, 25)
                    better_strategy_perc= st.slider("Better Strategy", 0, 100, 25)
                    good_strategy_perc= st.slider("Good Strategy", 0, 100, 25)
                st.write(f"""Premium: {premium_strategy_perc}%, Best: {best_strategy_perc}%, Better: {better_strategy_perc}%, Good: {good_strategy_perc}%,
                          Total:{premium_strategy_perc+best_strategy_perc+better_strategy_perc+good_strategy_perc}%""")
        else:
            fourth_priority_value= st.slider(f"{fourth_priority}", 0, 100, default_values[fourth_priority], key="fourth_priority_slider")
    # Fifth priority
    with col5:
        rack_size = st.selectbox("Rack Size", ['Qty in Consignment'] , key="rack_size")

    line_break(col5,7)


    if 'submit_clicked' not in st.session_state:
        st.session_state['submit_clicked'] = False
    if 'final_recommendation_df' not in st.session_state:
        st.session_state['final_recommendation_df'] = None

    if st.button("Submit"):
        with st.spinner("Generating Recommendations.."):
            if coverage_strategy == "No Double Coverage":
                user_input_params = {
                    'priority': {1: first_priority, 2: second_priority, 3: third_priority, 4: fourth_priority},
                    'parameters': {first_priority: process_priority_value(first_priority, first_priority_value),second_priority: process_priority_value(second_priority, second_priority_value),
                                   third_priority: process_priority_value(third_priority, third_priority_value), fourth_priority: process_priority_value(fourth_priority, fourth_priority_value)}
                }
                # Removing the Coverage strategy from params if it's No Double Coverage
                user_input_params['priority'] = {k: v for k, v in user_input_params['priority'].items() if v != 'Coverage Strategy'}
                user_input_params['parameters'] = {k: v for k, v in user_input_params['parameters'].items() if k != 'Coverage Strategy'}
                # Reset the index for 'priority'
                user_input_params['priority'] = {i + 1: v for i, (k, v) in enumerate(user_input_params['priority'].items())}
            else:
                user_input_params = {
                    'priority': {1: first_priority, 2: second_priority, 3: third_priority, 4: fourth_priority},
                    'parameters': {first_priority: process_priority_value(first_priority, first_priority_value),second_priority: process_priority_value(second_priority, second_priority_value),
                                   third_priority: process_priority_value(third_priority, third_priority_value),
                                    fourth_priority: process_priority_value(fourth_priority, fourth_priority_value)},
                    'strategy_coverage': {
                        'GOOD': good_strategy_perc / 100,'BETTER': better_strategy_perc / 100,'BEST': best_strategy_perc / 100,'PREMIUM': 0.0},
                    'strategy_order': {1: 'PREMIUM_BATTERIES%',2: 'BEST_BATTERIES%',3: 'BETTER_BATTERIES%',4: 'GOOD_BATTERIES%'}
                }

            user_input_params = modify_user_params(user_input_params)
            final_recommendation_df, akd_summary, store_summary, cluster_summary = recommendation_results(coverage_strategy, user_input_params)

            cluster_summary = cluster_summary[['CLUSTER', 'Pre_VIO_Coverage', 'Post_VIO_Coverage', 'SALES', 'PROJECTED_SALES', 'SALES_GROWTH']]
            col = ['Pre_VIO_Coverage', 'Post_VIO_Coverage', 'SALES_GROWTH']
            cluster_summary[col] = cluster_summary[col].apply(lambda x: x.apply(lambda y: f'{round(y * 100, 1)}%'))
            cluster_summary[cluster_summary.select_dtypes(include='number').columns] = cluster_summary[cluster_summary.select_dtypes(include='number').columns].round(0)
            
            st.dataframe(cluster_summary, use_container_width=True, hide_index=True)
            st.toast('🚀Recommendations generated successfully')

            # Save the final recommendation dataframe to session state
            st.session_state['final_recommendation_df'] = final_recommendation_df
            # Set the flag to show Save button
            st.session_state['submit_clicked'] = True

    # Show "Save Results" button only if "Submit" has been clicked
    if st.session_state['submit_clicked']:
        if st.button("Save Results"):
            if st.session_state['final_recommendation_df'] is not None:
                final_recommendation_df = st.session_state['final_recommendation_df']
                final_recommendation_df.to_csv(f'output_recos/recommendations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', index=False)
                st.success("Recommendations saved successfully!")
            else:
                st.warning("No recommendations to save.")

def get_dealer_level_summary(df, cluster, dealer):
    cols= ['STORE ID', 'RANK', 'GS', 'STRATEGY', 'CCA BREAKS', 'Running_VIO_%',
            'PROJECTED_SALES','MODEL_RECO']
    subset= df[(df['CLUSTER']==cluster) & (df['DEALMSTID']== dealer) & (df['RECOMMENDATION']=='YES')][cols]
    subset= subset.rename(columns={'STORE ID': 'Store ID', 'RANK': 'Rank', 'GS': 'Group Size',
                           'STRATEGY': 'Strategy', 'CCA BREAKS': 'CCA',
                             'Running_VIO_%': 'VIO Coverage', 'PROJECTED_SALES': 'Projected Sales',
                             'MODEL_RECO':'Model Recommendation Action'})
    
    subset['Store ID']= subset['Store ID'].astype(str)
    subset[['CCA', 'Projected Sales']]= subset[['CCA', 'Projected Sales']].fillna(0).astype(int)
    subset['VIO Coverage']= subset['VIO Coverage'].round(2)

    return subset

# def refresh():
#     if 'final_scoring_df' in st.session_state:
#         st.session_state['final_recommendation_df'] = st.session_state['final_recommendation_df']

with tabs[1]:
    if st.session_state['final_recommendation_df'] is not None:
        final_recommendation_df = st.session_state['final_recommendation_df']
        clusters_list= final_recommendation_df['CLUSTER'].unique().tolist()
        col1, col2, space= st.columns([1,1,5])
        selected_cluster= col1.selectbox("Cluster", clusters_list)
        dealers_list= final_recommendation_df[final_recommendation_df['CLUSTER']==selected_cluster]['DEALMSTID'].unique().tolist()
        selected_dealer= col2.selectbox('Dealer ID',dealers_list )
        subset= get_dealer_level_summary(final_recommendation_df, selected_cluster, selected_dealer)

        def color_cells(val):
            color = '#f4defa' if val == 'PREMIUM' else '#E3F1E7' if val== 'BEST' else '#fcdfb1s' if val=='BETTER' else '#cbe3f7' if val=='GOOD' else 'white'
            return f'background-color: {color}'

        styled_df = subset.style.applymap(color_cells, subset=['Strategy'])

        #st.data_editor(styled_df, key="my_key", num_rows="fixed",use_container_width= True,hide_index=True)
        edited_df= st.data_editor(
            styled_df, key='my_key',
            column_config={
                "Model Recommendation Action": st.column_config.SelectboxColumn(
                    "Model Recommendation Action",
                    width="medium",
                    options=["KEEP","ADD", "DELETE"],
                    required=True,
                )
            },
            hide_index=True, use_container_width= True,
        )
        if st.button('Push Changes'):
            final_recommendation_df.loc[(final_recommendation_df['DEALMSTID']==selected_dealer) & (final_recommendation_df['RECOMMENDATION']=='YES') ,'MODEL_RECO']= edited_df['Model Recommendation Action']
            st.session_state['final_recommendation_df']= final_recommendation_df
            st.toast(f'✅ Recommendations updated successfully')
    else:
        st.warning('No recommendations to display')


def dealer_non_recommended_skus(df, cluster, dealer):
    cols= ['STORE ID', 'RANK', 'GS', 'STRATEGY', 'CCA BREAKS', 'Running_VIO_%',
            'PROJECTED_SALES','MODEL_RECO']
    subset= df[(df['CLUSTER']==cluster) & (df['DEALMSTID']== dealer) & (df['RECOMMENDATION']=='NO')][cols]
    subset= subset.rename(columns={'STORE ID': 'Store ID', 'RANK': 'Rank', 'GS': 'Group Size',
                           'STRATEGY': 'Strategy', 'CCA BREAKS': 'CCA',
                             'Running_VIO_%': 'VIO Coverage', 'PROJECTED_SALES': 'Projected Sales',
                             'MODEL_RECO':'Model Recommendation Action'})
    subset['Store ID']= subset['Store ID'].astype(str)
    subset[['CCA', 'Projected Sales']]= subset[['CCA', 'Projected Sales']].fillna(0).astype(int)
    subset['VIO Coverage']= subset['VIO Coverage'].round(2)
    return subset

with tabs[2]:
    if st.session_state['final_recommendation_df'] is not None:
        final_recommendation_df = st.session_state['final_recommendation_df']
        clusters_list= final_recommendation_df['CLUSTER'].unique().tolist()
        col1, col2, col3= st.columns([1,1,5])
        selected_cluster= col1.selectbox("Cluster", clusters_list, key='cluster2')
        dealers_list= final_recommendation_df[final_recommendation_df['CLUSTER']==selected_cluster]['DEALMSTID'].unique().tolist()
        selected_dealer= col2.selectbox('Dealer ID',dealers_list, key='dealer2' )
        subset= dealer_non_recommended_skus(final_recommendation_df, selected_cluster, selected_dealer)
        subset['Model Recommendation Action']=  False
        edited_df= st.data_editor(subset, use_container_width=True, hide_index=True)

        if st.button('Push Recommendations'):
            added_recos= edited_df[edited_df['Model Recommendation Action']==True]
            added_gs= added_recos['Group Size'].unique().tolist()
            st.toast(f'🔗  Group Sizes {added_gs} added')
            edited_df['Model Recommendation Action']= edited_df['Model Recommendation Action'].apply(lambda x: 'YES' if x==True else 'NO')
            st.dataframe(edited_df, use_container_width=True)

            final_recommendation_df.loc[(final_recommendation_df['DEALMSTID']==selected_dealer) & (final_recommendation_df['GS'].isin(added_gs)),'RECOMMENDATION']='YES'
            st.session_state['final_recommendation_df']= final_recommendation_df
    else:
        st.warning('No recommendations to display')

def get_dealer_akd(df, cluster, dealer):
    cols= ['GS', 'CCA BREAKS']
    df['CCA BREAKS']= df['CCA BREAKS'].apply(lambda x: str(int(x)))
    keeps= df[(df['CLUSTER']==cluster) & (df['DEALMSTID']== dealer) &
               (df['MODEL_RECO']=='KEEP')][cols].rename(columns={'GS': 'Group Size',
                                                                'CCA BREAKS':'CCA'})
    adds= df[(df['CLUSTER']==cluster) & (df['DEALMSTID']== dealer) &
               (df['MODEL_RECO']=='ADD')][cols].rename(columns={'GS': 'Group Size',
                                                                'CCA BREAKS':'CCA'})
    deletes= df[(df['CLUSTER']==cluster) & (df['DEALMSTID']== dealer) &
               (df['MODEL_RECO']=='DELETE')][cols].rename(columns={'GS': 'Group Size',
                                                                'CCA BREAKS':'CCA'})
    return keeps, adds, deletes

with tabs[3]:
    if st.session_state['final_recommendation_df'] is not None:
        final_recommendation_df = st.session_state['final_recommendation_df']
        clusters_list= final_recommendation_df['CLUSTER'].unique().tolist()
        col1, col2, col3= st.columns([1,1,5])
        selected_cluster= col1.selectbox("Cluster", clusters_list, key='cluster3')
        dealers_list= final_recommendation_df[final_recommendation_df['CLUSTER']==selected_cluster]['DEALMSTID'].unique().tolist()
        selected_dealer= col2.selectbox('Dealer ID',dealers_list, key='dealer3' )
        keeps, adds, deletes= get_dealer_akd(final_recommendation_df, selected_cluster, selected_dealer)
        colx, _, coly,_, colz= st.columns([1,0.2,1,0.2,1])
        line_break(colx, 1)
        line_break(coly, 1)
        line_break(colz, 1)
        
        colx.markdown(
        """<div style="border: 1px solid #4CAF50; padding: 5px; border-radius: 5px; background-color: #f9f9f9;">
            <h5 style="color: #4CAF50; text-align: center;">Keeps</h5>
        </div>
        """, unsafe_allow_html=True)
        line_break(colx, 1)
        #colx.subheader('Keeps')
        colx.dataframe(keeps, use_container_width=True, hide_index=True)

        coly.markdown(
        """<div style="border: 1px solid #4CAF50; padding: 5px; border-radius: 5px; background-color: #f9f9f9;">
            <h5 style="color: #4CAF50; text-align: center;">Adds</h5>
        </div>
        """, unsafe_allow_html=True)
        line_break(coly, 1)
        #coly.subheader('Adds')
        coly.dataframe(adds, use_container_width=True, hide_index=True)
        colz.markdown(
        """<div style="border: 1px solid #4CAF50; padding: 5px; border-radius: 5px; background-color: #f9f9f9;">
            <h5 style="color: #4CAF50; text-align: center;">Deletes</h5>
        </div>
        """, unsafe_allow_html=True)
        #colz.subheader('Deletes')
        line_break(colz, 1)
        colz.dataframe(deletes, use_container_width= True, hide_index=True)
    else:
        st.warning('No recommendations to display')

hide_footer = """ <style> #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style> """
st.markdown(hide_footer, unsafe_allow_html=True)