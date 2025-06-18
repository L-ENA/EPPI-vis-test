
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from API_calls import get_total_n, get_year_histogram
from utils import settings_menu
from plots import plot_freq_bar

from all_pages.pg_3 import get_sunburst
from API_calls import get_frequency_counts
from utils import process_df


def session_state_dashboard():
    if "dashboard_df" not in st.session_state:
        st.session_state.dashboard_df=pd.DataFrame()

def world_quick():
    df = px.data.gapminder()

    # Create a scatter geo plot
    # 'locations' maps to the 'iso_alpha' column for country codes
    # 'size' maps to 'pop' for bubble size based on population
    # 'color' maps to 'continent' for coloring by continent
    # 'hover_name' displays country name on hover
    # 'animation_frame' creates an animation over the 'year' column
    fig1 = px.scatter_geo(df,
                         locations="iso_alpha",
                         size="pop",
                         color="continent",
                         hover_name="country",
                         animation_frame="year",
                         )

    # Display the figure

    # Import data from GitHub
    data = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_with_codes.csv')

    # Create basic choropleth map
    fig2 = px.choropleth(data, locations='iso_alpha', color='gdpPercap', hover_name='country', title='GDP per Capita by Country', color_continuous_scale='Viridis')

    return fig1, fig2


def dashbd():
    session_state_dashboard()#init session state variables for this page
    settings_menu()#get the menu to adjust the plots


    ################### ---------- Generate Fake Data ----------
    np.random.seed(42)
    n = 1000
    start_date = datetime(2020, 1, 1)

    df = pd.DataFrame({
        'date': [start_date + timedelta(days=int(x)) for x in np.random.randint(0, 1600, size=n)],
        'category': np.random.choice(['A', 'B', 'C', 'D'], size=n),
        'region': np.random.choice(['North', 'South', 'East', 'West'], size=n),
        'value': np.random.normal(loc=100, scale=20, size=n).round(2),
        'score': np.random.randint(1, 6, size=n),
    })

    df['year'] = df['date'].dt.year
    ############################################

    st.title("DESTINY Dashboard")
    st.subheader("Whole database overview")

    # ---------- Top Metrics ----------
    col1, col2, col3 = st.columns(3)
    new_recs=713#fake
    col1.metric("Total Records", f"{get_total_n():,}", str(new_recs))#real

    # Get the current date and time
    now = datetime.now()
    formatted_date_time = now.strftime("%Y-%m-%d")
    col2.metric("Last Update Date fake", formatted_date_time, " 3 Days Ago")#fake

    col3.metric("Something else fake?", 358, "4%")#fake

    # Add custom CSS (optional)
    st.markdown(
        """
        <style>
        .stMetric {
            border: 1px solid #ddd; /* Add a border */
            border-radius: 5px; /* Round the corners */
            padding: 10px; /* Add some padding */
            margin-bottom: 10px; /* Add some spacing below */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ---------- Main Plot: Yearly Histogram ----------#real

    st.subheader("Yearly Record Distribution of records")
    hist_fig = plot_freq_bar(st.session_state.year_histogram_df, title="Records per Year (showing last {} years)".format(st.session_state.max_codes_slider_value), col_scale=st.session_state.selected_color_theme,
                  x_axis="Year", y_axis="Counts", plot_attributes=False)
    st.plotly_chart(hist_fig, use_container_width=True)
    with st.expander("💡 Chart customisation and record display"):
        st.markdown(
            "*:gray[Adjust number of bars displayed, label length, and colour in the settings menu on the left.]*")
        st.markdown(
            "*:gray[Use scrollbar or view chart in full screen mode to read the whole legend (access via top right corner)]*")
    st.divider()
    cola, colb = st.columns(2)
    with cola:
        st.subheader("Codes within database")
        if 'sunburst' not in st.session_state:
            st.session_state.sunburst = get_sunburst()
        st.plotly_chart(st.session_state.sunburst, use_container_width=True)
        st.subheader("Placeholder for treeview viz")
    with colb:
        st.subheader("Fake world map")
        f1,f2=world_quick()
        st.plotly_chart(f1, use_container_width=True)
        st.plotly_chart(f2, use_container_width=True)

    st.divider()
    st.subheader("Records selected from search page")
    if st.session_state.dashboard_df.shape[0] > 0:
        st.dataframe(st.session_state.dashboard_df)
    else:
        st.write("Go to the search page to select records")
        st.page_link(st.session_state.p4, label="Search", icon="🔍")

    # ---------- Multi-column Category Plots ----------#fake
    st.divider()
    st.header("FAKE DASHBOARD: Category Distributions")
    col4, col5 = st.columns(2)

    with col4:
        cat_count_fig = px.bar(df['category'].value_counts().reset_index(),
                               x= 'count', y='category',
                               labels={ 'count': 'Category', 'category': 'Count'},
                               title='Records by Category')
        st.plotly_chart(cat_count_fig, use_container_width=True)

    with col5:
        region_fig = px.pie(df, names='region', title='Records by Region')
        st.plotly_chart(region_fig, use_container_width=True)

    # ---------- Score Distribution ----------
    st.subheader("Score Distribution")
    score_fig, ax = plt.subplots()
    df['score'].value_counts().sort_index().plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title("Score Distribution (1–5)")
    ax.set_xlabel("Score")
    ax.set_ylabel("Count")
    st.pyplot(score_fig)

    # ---------- Scatter Plot ----------
    st.subheader("Value vs Score Scatter Plot")
    scatter_fig = px.scatter(df, x='score', y='value', color='category',
                             title="Value vs Score by Category")
    st.plotly_chart(scatter_fig, use_container_width=True)

    # ---------- Optional Sidebar Filters ----------
    with st.sidebar:
        st.header("🔎 Filters (fake)")
        selected_years = st.multiselect("Select Year(s)", sorted(df['year'].unique()),
                                        default=sorted(df['year'].unique()))
        selected_categories = st.multiselect("Select Categories", df['category'].unique(),
                                             default=df['category'].unique())

        # Filter Data
        filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]
        st.markdown(f"**Filtered Records:** {len(filtered_df)}")

