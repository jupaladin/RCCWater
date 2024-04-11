import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import pydeck as pdk

# Setting up page configurations
st.set_page_config(
    page_title="RCC",
    page_icon="💧",
    layout="wide")



# Loading the dataset only once
@st.cache_resource
def read_objects():
    df = pd.read_csv('RCC_CN_with_coordinates.csv')   
    # Convert 'ID' column to string data type
    df['ID'] = df['ID'].astype(str) 
    # Convert '公布时间' column to datetime format
    df['公布时间'] = pd.to_datetime(df['公布时间'])
    return df

# Load the dataset
df = read_objects()



# Setting up the expander for filtering the dataset
with st.expander("筛选"):
    col1, col2 = st.columns(2)

    with col1:
        # Add a text input for free text search
        text_search = st.text_input("搜索项目描述")

        # Get unique areas
        unique_regions = df['区域'].unique()
        # Allow users to select multiple regions
        selected_regions = st.multiselect('选择区域', unique_regions)

        # Determine provinces based on selected regions
        if selected_regions:
            unique_provinces = df[df['区域'].isin(selected_regions)]['省份'].unique()
        else:
            unique_provinces = df['省份'].unique()
        # Allow users to select multiple provinces
        selected_provinces = st.multiselect('选择省份', unique_provinces)

        # Determine cities based on selected provinces
        if selected_provinces:
            unique_cities = df[df['省份'].isin(selected_provinces)]['城市'].unique()
        else:
            unique_cities = df['城市'].unique()
        # Allow users to select multiple cities
        selected_cities = st.multiselect('选择城市', unique_cities)

    with col2:
        # Get unique years
        unique_years = sorted(df['公布时间'].dt.year.unique())
        # Allow users to select multiple years
        selected_years = st.multiselect('选择年份', unique_years, default=[max(unique_years)])

        # Get unique search terms
        unique_search_terms = df['搜索词'].unique()
        # Allow users to select multiple search terms
        selected_search_terms = st.multiselect('选择项目领域', unique_search_terms)

        # Get unique project stages
        unique_project_stages = df['项目阶段'].unique()
        # Allow users to select multiple project stages
        selected_project_stages = st.multiselect('选择项目阶段', unique_project_stages)

        # Get unique categories
        unique_categories = set('/'.join(df['行业分类']).split('/'))
        # Allow users to select multiple categories
        selected_categories = st.multiselect('选择项目类别', list(unique_categories))



    # Filtering the dataframe
    filtered_df = df.copy()

    if text_search:
        filtered_df = filtered_df[filtered_df['项目名称'].str.contains(text_search)]
    if selected_years:
        filtered_df = df[df['公布时间'].dt.year.isin(selected_years)]
    if selected_search_terms:
        filtered_df = filtered_df[filtered_df['搜索词'].isin(selected_search_terms)]
    if selected_regions:
        filtered_df = filtered_df[filtered_df['区域'].isin(selected_regions)]
    if selected_provinces:
        filtered_df = filtered_df[filtered_df['省份'].isin(selected_provinces)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['城市'].isin(selected_cities)]
    if selected_project_stages:
        filtered_df = filtered_df[filtered_df['项目阶段'].isin(selected_project_stages)]
    if selected_categories:
        # Filter based on categories requires checking if any category in selected_categories is in the Category column
        filtered_df = filtered_df[filtered_df['行业分类'].apply(lambda x: any(category in x for category in selected_categories))]



# Check if the filtered DataFrame is empty
if filtered_df.empty:
    st.write("没有结果符合您的搜索条件。")
else:
    # Expander
    with st.expander("查看单一项目"):
        filtered_df['公布时间'] = filtered_df['公布时间'].dt.date
        st.dataframe(filtered_df, hide_index=True)

    # Setting up the dashboard and viz
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        # Calculate the sum of the 'ID' column in the filtered dataframe
        total_ids = filtered_df['ID'].count()
        # Display the sum with thousand delimiter
        st.metric(label="项目数量", value=f"{total_ids:,.0f}")
                
    with col2:
        # Convert 'Cost (millions)' column to numeric data type
        filtered_df['造价(百万)'] = pd.to_numeric(filtered_df['造价(百万)'], errors='coerce')
        # Calculate the sum of the 'Cost (millions)' column in the filtered dataframe
        total_cost = filtered_df['造价(百万)'].sum()
        # Display the sum with thousand delimiter
        st.metric(label="造价(百万)", value=f"{total_cost:,.0f}", delta="暂无数据", delta_color="off")

    with col3:
        # Convert 'Building area (㎡)' column to numeric data type
        filtered_df['建面(㎡)'] = pd.to_numeric(filtered_df['建面(㎡)'], errors='coerce')
        # Calculate the sum of the 'Building area (㎡)' column in the filtered dataframe
        total_cost = filtered_df['建面(㎡)'].sum()
        # Display the sum with thousand delimiter
        st.metric(label="建面(㎡)", value=f"{total_cost:,.0f}", delta="暂无数据", delta_color="off")

    with col4:
        province_max_count = filtered_df['省份'].value_counts().idxmax()
        # Display the sum with thousand delimiter
        st.metric(label="项目最多的省份", value=province_max_count)

    with col5:
        city_max_count = filtered_df['城市'].value_counts().idxmax()
        # Display the sum with thousand delimiter
        st.metric(label="项目最多的城市", value=city_max_count)



    col6, col7 = st.columns(2)

    with col6:
        # Create a pie chart showing the distribution of project stages
        fig = px.pie(filtered_df.groupby('项目阶段').size().reset_index(name='Count'), values='Count', names='项目阶段', title='项目阶段分布占比')
        # Show the pie chart
        st.plotly_chart(fig, use_container_width=True)

    with col7:
        # Create a new DataFrame for exploded categories without altering the original one
        exploded_df = filtered_df.assign(Category=filtered_df['行业分类'].str.split('/')).explode('行业分类')
        # Create a pie chart showing the distribution of categories
        fig = px.pie(exploded_df.groupby('行业分类').size().reset_index(name='Count'), values='Count', names='行业分类', title='项目类别分布占比')
        # Show the pie chart
        st.plotly_chart(fig, use_container_width=True)

    col8, col9 = st.columns(2)

    with col8:
        # Filter the dataframe to include only the top 10 provinces
        top_10_provinces = filtered_df['省份'].value_counts().nlargest(10).reset_index()
        # Create a bar chart showing the distribution of provinces
        fig = px.bar(top_10_provinces, x='count', y='省份', title='项目最多省份排列', labels={'count': '计数'})
        # Show the bar chart
        st.plotly_chart(fig, use_container_width=True)

    with col9:
        # Filter the dataframe to include only the top 10 cities
        top_10_cities = filtered_df['城市'].value_counts().nlargest(10).reset_index()
        # Create a bar chart showing the distribution of cities
        fig = px.bar(top_10_cities, x='count', y='城市', title='项目最多城市排列', labels={'count': '计数'})
        # Show the bar chart
        st.plotly_chart(fig, use_container_width=True)




    # Convert 'Announcement time' column to datetime
    filtered_df['公布时间'] = pd.to_datetime(filtered_df['公布时间'])

    # Extract year and month (yy-mm) from the datetime column and convert to string
    filtered_df['公布时间'] = filtered_df['公布时间'].dt.strftime('%y-%m')

    # Group the data by 'Announcement time by year and month' and count the number of announcements for each period
    timeline_data = filtered_df.groupby('公布时间').size().reset_index(name='项目数量')

    # Create a line chart showing the distribution of announcements over time
    fig = px.line(timeline_data, x='公布时间', y='项目数量', 
                title='项目数量变化趋势')

    # Show the line chart
    st.plotly_chart(fig, use_container_width=True)



    # Convert '公布时间' to string
    filtered_df['公布时间'] = filtered_df['公布时间'].astype(str)

    # Create the Pydeck map
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=filtered_df['纬度'].mean(),
            longitude=filtered_df['经度'].mean(),
            zoom=3,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=filtered_df,
                get_position='[经度, 纬度]',
                get_radius=20000,
                get_fill_color=[255, 0, 0],
                pickable=True,
            ),
        ],
        tooltip={
            'html': '<b>ID:</b> {ID}<br/>' +
                    '<b>项目名称:</b> {项目名称}<br/>' +
                    '<b>造价(百万):</b> {造价(百万)}<br/>' +
                    '<b>项目阶段:</b> {项目阶段}<br/>' +
                    '<b>省份:</b> {省份}<br/>' +
                    '<b>城市:</b> {城市}<br/>' +
                    '<b>公布时间:</b> {公布时间}<br/>' + 
                    '<b>区域:</b> {区域}<br/>' +
                    '<b>建面(㎡):</b> {建面(㎡)}'
        }
    ))
