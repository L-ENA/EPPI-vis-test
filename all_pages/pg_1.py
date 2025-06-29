import streamlit as st
from streamlit_tree_select import tree_select
import streamlit_antd_components as sac

from all_pages.pg_record_view import aggrid_view
from api_calls import get_frequency_counts, update_display_df
from plots import plot_freq_bar

from utils import (
    settings_menu,
    downloader,
    convert_to_sac_tree_items
)


def demo_p1():
    """
    A page where attribute frequencies are displayed as an interactive bar chart.
    Click a bar to select an attribute (or select multiple with the box select tool)
    and display information about the records associated with that attribute below as a table.
    """

    st.write("##### Attribute Frequencies (Bar Chart)")
    settings_menu()

    col_Left, col_Right = st.columns([1, 3], vertical_alignment="top", border=True)

    with col_Left:
        st.subheader("Codeset")
        treetype = st.radio("Chose Type", ("ANTD", "ST_tree"), index=0)
        if treetype == "ANTD":
            if "sactree" not in st.session_state:
                st.session_state.sactree = convert_to_sac_tree_items(st.session_state.treestructures)

            sac.tree(items=st.session_state.sactree, label='Terminology', align='left', color='grape', icon='table',
                     height=500, open_all=True, checkbox=False)
        else:
            return_select = tree_select(st.session_state.treestructures)
    with col_Right:

        parent_attributes = [a for a in st.session_state.attributes_list if a.HasChildren]
        parent_attribute_names = [a.AttributeName for a in parent_attributes]
        selected_parent = st.selectbox(
            "Select Parent Attribute", options=parent_attribute_names
        )
        parent_index = parent_attribute_names.index(selected_parent)

        attribute = parent_attributes[parent_index]
        # avoid reloading frequency counts each run
        if (
            "{}_{}".format(attribute.AttributeId, attribute.SetId)
            not in st.session_state.frequency_counts
        ):
            st.session_state.frequency_counts[
                "{}_{}".format(attribute.AttributeId, attribute.SetId)
            ] = get_frequency_counts(attribute.AttributeId, attribute.SetId, included=True)
        freqs = st.session_state.frequency_counts[
            "{}_{}".format(attribute.AttributeId, attribute.SetId)
        ]

        barname = "bar_{}".format(attribute.AttributeName)
        fig = plot_freq_bar(
            freqs,
            title=attribute.AttributeName,
            col_scale=st.session_state.selected_color_theme,
        )
        st.plotly_chart(fig, on_select="rerun", key=barname)

        with st.expander("💡 Chart customisation and record display"):
            st.markdown(
                "*:gray[Click on a bar to display records. Hold Shift key (⬆️) to select multiple slices or see the Plotly menu on the top right for advanced selection methods.]*"
            )
            st.markdown(
                "*:gray[Adjust number of codes, label length, and colour in the settings menu on the left.]*"
            )
            st.markdown(
                "*:gray[Use scrollbar or view chart in full screen mode to read the whole legend (access via top right corner)]*"
            )

    idlist = []
    setlist = []
    if len(st.session_state[barname]["selection"]["points"]) > 0:
        for point in st.session_state[barname]["selection"]["points"]:
            idlist.append(point["customdata"]["0"])
            setlist.append(point["customdata"]["1"])
        update_display_df(idlist, setlist)

    if st.session_state.display_df.shape[0] > 0:
        # FIXME: need to make changes to use full dataframe
        downloader(st.session_state.display_df)
        aggrid_view(st.session_state.display_df)
