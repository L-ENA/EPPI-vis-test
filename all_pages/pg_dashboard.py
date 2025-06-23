from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from streamlit_tree_select import tree_select
import streamlit_antd_components as sac

import streamlit as st
from api_calls import (  # @L-ENA most of these functions are unused
    get_frequency_counts,
    get_total_n,
    get_year_histogram,
)
from plots import plot_freq_bar
from utils import (
    settings_menu,
    convert_to_sac_tree_items
)

# from all_pages.pg_3 import get_sunburst # @L-ENA this function no longr exists


def session_state_dashboard():
    if "dashboard_df" not in st.session_state:
        st.session_state.dashboard_df = pd.DataFrame()


def world_quick():
    df = px.data.gapminder()

    # Create a scatter geo plot
    # 'locations' maps to the 'iso_alpha' column for country codes
    # 'size' maps to 'pop' for bubble size based on population
    # 'color' maps to 'continent' for coloring by continent
    # 'hover_name' displays country name on hover
    # 'animation_frame' creates an animation over the 'year' column
    fig1 = px.scatter_geo(
        df,
        locations="iso_alpha",
        size="pop",
        color="continent",
        hover_name="country",
        animation_frame="year",
    )

    # Display the figure

    # Import data from GitHub
    data = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/gapminder_with_codes.csv"
    )

    # Create basic choropleth map
    fig2 = px.choropleth(
        data,
        locations="iso_alpha",
        color="gdpPercap",
        hover_name="country",
        title="GDP per Capita by Country",
        color_continuous_scale="Viridis",
    )

    return fig1, fig2


def dashbd():
    session_state_dashboard()  # init session state variables for this page
    settings_menu()  # get the menu to adjust the plots


    ################### ---------- Generate Fake Data ----------
    np.random.seed(42)
    n = 1000
    start_date = datetime(2020, 1, 1)

    df = pd.DataFrame(
        {
            "date": [
                start_date + timedelta(days=int(x))
                for x in np.random.randint(0, 1600, size=n)
            ],
            "category": np.random.choice(["A", "B", "C", "D"], size=n),
            "region": np.random.choice(["North", "South", "East", "West"], size=n),
            "value": np.random.normal(loc=100, scale=20, size=n).round(2),
            "score": np.random.randint(1, 6, size=n),
        }
    )

    df["year"] = df["date"].dt.year
    ############################################

    st.title("DESTINY Dashboard")
    st.subheader("Whole database overview")

    # ---------- Top Metrics ----------
    col1, col2, col3 = st.columns(3)
    new_recs = 713  # fake
    col1.metric("Total Records", f"{get_total_n():,}", str(new_recs))  # real

    # Get the current date and time
    now = datetime.now()
    formatted_date_time = now.strftime("%Y-%m-%d")
    col2.metric("Last Update Date (TOY DATA)", formatted_date_time, " 3 Days Ago")  # fake

    col3.metric("TOY placeholder?", 358, "4%")  # fake

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
    col_Left, col_Right = st.columns([1, 3], vertical_alignment="top", border=True)

    with col_Left:
        st.subheader("Codeset")
        treetype= st.radio("Chose Type", ("ANTD", "ST_tree"), index=0)
        if treetype == "ANTD":
            if "sactree" not in st.session_state:
                st.session_state.sactree = convert_to_sac_tree_items(st.session_state.treestructures)

            sac.tree(items=st.session_state.sactree, label='Terminology', align='left', color='grape', icon='table', height=500, open_all=True, checkbox=False)
        else:
            return_select = tree_select(st.session_state.treestructures)


    with col_Right:
        # ---------- Main Plot: Yearly Histogram ----------#real

        st.subheader("Yearly Record Distribution")
        hist_fig = plot_freq_bar(
            st.session_state.year_histogram_df,
            title="Records per Year (showing latest {} years)".format(
                st.session_state.max_codes_slider_value
            ),
            col_scale=st.session_state.selected_color_theme,
            x_axis="Year",
            y_axis="Counts",
            plot_attributes=False,
            sort_counts=False,
        )
        st.plotly_chart(hist_fig, use_container_width=True)
        with st.expander("💡 Chart customisation and record display"):
            st.markdown(
                "*:gray[Adjust number of bars displayed, label length, and colour in the settings menu on the left.]*"
            )
            st.markdown(
                "*:gray[Use scrollbar or view chart in full screen mode to read the whole legend (access via top right corner)]*"
            )
        st.divider()

    cola, colb = st.columns(2)
    with cola:
        st.subheader("Codes within database")
        # if "sunburst" not in st.session_state: #@L-ENA - commented out as functio no longer exists
        #     st.session_state.sunburst = get_sunburst()
        if "plot_CodesVis" not in st.session_state:
            st.write("Go to the hierarchical visualisations page ⬇️ to create content")
            st.page_link(st.session_state.p3, label="Click to add plot", icon="🛠️")
        else:
            st.page_link(st.session_state.p3, label="Click to change plot type", icon="🛠️")
            st.plotly_chart(st.session_state.plot_CodesVis, use_container_width=True)

    with colb:
        st.subheader("Toy data world maps")
        f1, f2 = world_quick()
        worldtype = st.radio("Chose Type", ("Scattermap", "Filled Map"), index=1)
        if worldtype == "Scattermap":
            st.plotly_chart(f1, use_container_width=True)
        else:
            st.plotly_chart(f2, use_container_width=True)

    st.divider()
    st.subheader("Records selected from search page")
    if st.session_state.dashboard_df.shape[0] > 0:
        st.dataframe(st.session_state.dashboard_df)
    else:
        st.write("Click 'Search'⬇️ to go to the search page to select records")
        st.page_link(st.session_state.p5, label="Search", icon="🔍")

    # ---------- Multi-column Category Plots ----------#fake
    st.divider()
    st.header("TOY DATA DASHBOARD: Category Distributions")
    col4, col5 = st.columns(2)

    with col4:
        cat_count_fig = px.bar(
            df["category"].value_counts().reset_index(),
            x="count",
            y="category",
            labels={"count": "Category", "category": "Count"},
            title="Records by Category",
        )
        st.plotly_chart(cat_count_fig, use_container_width=True)

    with col5:
        region_fig = px.pie(df, names="region", title="Records by Region")
        st.plotly_chart(region_fig, use_container_width=True)

    # ---------- Score Distribution ----------
    st.subheader("Score Distribution")
    score_fig, ax = plt.subplots()
    df["score"].value_counts().sort_index().plot(kind="bar", ax=ax, color="skyblue")
    ax.set_title("Score Distribution (1–5)")
    ax.set_xlabel("Score")
    ax.set_ylabel("Count")
    st.pyplot(score_fig)

    # ---------- Scatter Plot ----------
    st.subheader("Value vs Score Scatter Plot")
    scatter_fig = px.scatter(
        df, x="score", y="value", color="category", title="Value vs Score by Category"
    )
    st.plotly_chart(scatter_fig, use_container_width=True)

    # ---------- Optional Sidebar Filters ----------
    with st.sidebar:
        st.header("🔎 Filters (TOY DATA)")
        selected_years = st.multiselect(
            "Select Year(s)",
            sorted(df["year"].unique()),
            default=sorted(df["year"].unique()),
        )
        selected_categories = st.multiselect(
            "Select Categories",
            df["category"].unique(),
            default=df["category"].unique(),
        )

        # Filter Data
        filtered_df = df[
            df["year"].isin(selected_years) & df["category"].isin(selected_categories)
            ]
        st.markdown(f"**Filtered Records:** {len(filtered_df)}")
