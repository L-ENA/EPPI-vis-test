"""page 3, containing customisable hierarchical plots"""

import plotly.express as px
import streamlit as st
from api_calls import (
    add_years_to_attribute_df,
    attributes_to_hierarchical,
    clean_dedupe_attributes,
)


def demo_p3():
    """
    A page containing various, customisable
    hierarchical visualisations.

    1: sunburst plot
    2: icile plot
    """

    st.write("#### Hierarchical Visualisations")
    st.write(
        "The purpose of this section is \
             to demonstrate various approaches to "
        "visualising hierarchical data. "
        "Beyond selecting a specific visualisation style, "
        "we can also subset our data by a year range. "
        "Please note: this annualised data is currenlty "
        "synthetic -- we will hopefully replace it with "
        "real-world data asap. "
    )

    df = attributes_to_hierarchical()
    attributes_years_df = add_years_to_attribute_df(df)

    if "year_range" not in st.session_state:
        years = sorted(attributes_years_df["year"].unique())
        st.session_state.year_range = (min(years), max(years))
        st.session_state.plot_df = df  # Store initial plot data

    if "plot_type" not in st.session_state:
        st.session_state.plot_type = "Sunburst"

    plot_type = st.selectbox(
        "Select Plot Type",
        options=["Sunburst", "Icicle", "Treemap"],
        index=0 if st.session_state.plot_type == "Sunburst" else 1,
        help="Choose between Sunburst, Icicle, and Treemap plot styles",
    )
    st.session_state.plot_type = plot_type

    years = sorted(attributes_years_df["year"].unique())
    min_year, max_year = min(years), max(years)

    selected_range = st.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
        help="Filter data by year range",
    )

    # plot updater button
    if st.button("Update Plot"):
        st.session_state.year_range = selected_range

        filtered_df = attributes_years_df[
            (attributes_years_df["year"] >= selected_range[0])
            & (attributes_years_df["year"] <= selected_range[1])
        ]
        # update plot data
        st.session_state.plot_df = clean_dedupe_attributes(
            filtered_df.groupby(["character", "parent"], as_index=False)["value"].sum()
        )

    if st.session_state.plot_type == "Sunburst":
        fig = px.sunburst(
            st.session_state.plot_df,
            names="character",
            parents="parent",
            values="value",
            branchvalues="total",
            title=f"Sunburst Plot: Data from {st.session_state.year_range[0]} to {st.session_state.year_range[1]}",
        )
    elif st.session_state.plot_type == "Icicle":
        fig = px.icicle(
            st.session_state.plot_df,
            names="character",
            parents="parent",
            values="value",
            branchvalues="total",
            title=f"Icicle Plot: Data from {st.session_state.year_range[0]} to {st.session_state.year_range[1]}",
        )
    elif st.session_state.plot_type == "Treemap":
        fig = px.treemap(
            st.session_state.plot_df,
            values="value",
            names="character",
            parents="parent",
            #color='lifeExp',
            hover_data=["value"],
            color_continuous_scale='RdBu',
            title=f"Treemap Plot: Data from {st.session_state.year_range[0]} to {st.session_state.year_range[1]}",

            #color_continuous_midpoint=np.average(df['lifeExp'], weights=df['pop'])
        ).update_layout(
        margin={'t':50,'l':0,'b':0,'r':0}
    )

    # fig.update_layout(title_x=0.5)
    st.session_state.plot_CodesVis = fig#to enable user to display this on the dashboard page - Using same object will reduce wait and load times, this might be significan with DESTINY dataset
    st.page_link(
        st.session_state.dashboardpage, label="View in dashboard", icon="📊"
    )
    st.plotly_chart(fig)

    with st.expander("Debug: show data"):
        st.write("### Current plot dataframe")
        st.write(st.session_state.plot_df)

    #############################
    ####### OLD #################
    ####### FOR DEBUGGING #######
    #############################
    # st.write("### items in session state")
    # for item in st.session_state:
    #     st.write(item)

    # st.write("### year_histogram_df")
    # st.write(st.session_state.year_histogram_df)

    # st.write("### frequency_counts ")
    # st.write(st.session_state.frequency_counts)

    # st.write("### attributes_list")
    # for attribute in st.session_state.attributes_list:
    #     st.write(dict(attribute.__dict__))

    # processed_df = clean_dedupe_attribtues(df)  # function from utils
    # print(processed_df)
    # st.write("### processed attributes df, no years")
    # st.write(processed_df)

    # processed_attributes_years_df = add_years_to_attribute_df(processed_df)
    # print(processed_attributes_years_df)
    # st.write("### processed attributes df with fake year data")
    # st.write(processed_attributes_years_df)

    # # Create sunburst plot
    # fig = px.sunburst(
    #     df, names="character", parents="parent", values="value", branchvalues="total"
    # )

    # st.plotly_chart(fig)
