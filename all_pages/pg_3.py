import streamlit as st
from API_calls import get_frequency_counts
from utils import process_df
import pandas as pd
import plotly.express as px

def get_sunburst():
    id_to_name = {att.AttributeId: att.AttributeName for att in st.session_state.attributes_list}
    parent_map = {att.AttributeId: att.ParentAttributeId for att in st.session_state.attributes_list}

    # Prepare rows for DataFrame
    sunburst_data = []

    #########get frequency counts and save them to session state
    for attribute in st.session_state.attributes_list:
        if attribute.HasChildren:
            if "{}_{}".format(attribute.AttributeId, attribute.SetId) not in st.session_state.frequency_counts:
                st.session_state.frequency_counts["{}_{}".format(
                    attribute.AttributeId, attribute.SetId)] = get_frequency_counts(attribute.AttributeId,
                                                                                    attribute.SetId, included=True)

    for att in st.session_state.attributes_list:
        current_id = att.AttributeId
        current_name = att.AttributeName
        parent_id = att.ParentAttributeId

        parent_name = id_to_name.get(parent_id, "") if parent_id != 0 else ""

        ######Need to get the value counts.
        try:
            freqs = st.session_state.frequency_counts["{}_{}".format(parent_id, attribute.SetId)]

            sunburst_data.append({
                "character": current_name,
                "parent": parent_name,
                "value": freqs.loc[freqs['attId'] == current_id, 'Counts'].iloc[0]
            })
        except:
            sunburst_data.append({
                "character": current_name,
                "parent": parent_name,
                "value": 0
            })

    # Create DataFrame
    df = pd.DataFrame(sunburst_data)

    #################postprocess to: Get parent counts and make names unique
    df = process_df(df)  # function from utils

    # Create sunburst plot
    fig = px.sunburst(
        df,
        names="character",
        parents="parent",
        values="value",
        branchvalues="total"
    )
    return fig

def demo_p3():
    """
    TODO: ...
    """

    st.write("Demo Page 3")
    if 'sunburst' not in st.session_state:
        st.session_state.sunburst=get_sunburst()

    st.plotly_chart(st.session_state.sunburst)
    #st.dataframe(df)
    #df.to_csv(r"C:\Users\qtnzls7\PycharmProjects\EPPI-Vis\streamlit-demo\data\pg_3_final.csv".format(df.shape[0]))





