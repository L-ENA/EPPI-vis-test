import streamlit as st
from API_calls import get_frequency_counts, update_display_df
from plots import plot_freq_pie, plot_altair_freq_pie
from utils import settings_menu, downloader
from all_pages.pg_record_view import aggrid_view


def demo_p2():
    """
    A page where attribute frequencies are displayed as a pie chart.
    """

    st.write("##### Attribute Frequencies (Pie Chart)")
    settings_menu()

    parent_attributes = [a for a in st.session_state.attributes_list if a.HasChildren]
    parent_attribute_names = [a.AttributeName for a in parent_attributes]
    selected_parent = st.selectbox("Select Parent Attribute", options=parent_attribute_names)
    parent_index = parent_attribute_names.index(selected_parent)

    attribute = parent_attributes[parent_index]
    # avoid reloading frequency counts each run
    if "{}_{}".format(attribute.AttributeId, attribute.SetId) not in st.session_state.frequency_counts:
        st.session_state.frequency_counts["{}_{}".format(
            attribute.AttributeId, attribute.SetId)] = get_frequency_counts(attribute.AttributeId,
                                                                            attribute.SetId, included=True)
    freqs = st.session_state.frequency_counts["{}_{}".format(attribute.AttributeId, attribute.SetId)]

    # piename = "pie_{}".format(attribute.AttributeName)
    # fig = plot_freq_pie(freqs, title=attribute.AttributeName, col_scale=st.session_state.selected_color_theme)
    # st.plotly_chart(fig, on_select="rerun", key=piename)


    piename = "pie_{}".format(attribute.AttributeName)

    fig = plot_altair_freq_pie(freqs, title=attribute.AttributeName, col_scale=st.session_state.selected_color_theme)
    st.altair_chart(fig, on_select='rerun', key=piename)
    with st.expander("💡 Chart customisation and record display"):
        st.markdown(
            "*:gray[Click a pie slice to display records. Hold Shift key (⬆️) to select multiple slices.]*")
        st.markdown(
            "*:gray[Adjust number of codes, label length, and colour in the settings menu on the left.]*")
        st.markdown(
            "*:gray[View chart in full screen mode to expand legend (access via top right corner)]*")

    #st.write(st.session_state["pie_{}".format(attribute.AttributeName)])



    idlist = []
    setlist = []
    if len(st.session_state[piename]["selection"]["param_1"]) > 0:
        for point in st.session_state[piename]["selection"]["param_1"]:
            idlist.append(point["attId"])
            setlist.append(point["setId"])
        update_display_df(idlist, setlist)

    if st.session_state.display_df.shape[0] > 0:
        downloader(st.session_state.display_df)
        # FIXME: need to make changes to use full dataframe
        aggrid_view(st.session_state.display_df)
