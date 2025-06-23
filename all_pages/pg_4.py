from math import ceil

import all_pages.pg_record_view
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from api_calls import req_first_page, req_next_page
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from titlecase import titlecase


# luminance calculation:
# https://nemecek.be/blog/172/how-to-calculate-contrast-color-in-python
def get_luminance(rgb_red, rgb_green, rgb_blue):
    return rgb_red * 0.2126 + rgb_green * 0.7152 + rgb_blue * 0.0722


def colourmap_format(threshold_low, threshold_high, cmap):

    # choose text colour by contrast score
    contrast_score = ((get_luminance(255, 255, 255) + 0.05) /
                      (get_luminance(cmap[0]*255, cmap[1]*255, cmap[2]*255) + 0.05))
    text_colour = "white"
    if contrast_score < 2:
        text_colour = "black"

    js_string = f"""
        if (params.value >= "{threshold_low}" && params.value < "{threshold_high}" ) {{
            return {{
                "color": "{text_colour}",
                "backgroundColor": "RGB({cmap[0]*255},{cmap[1]*255},{cmap[2]*255},{cmap[3]})",
            }}
        }}
    """

    return js_string


# js code adapted from:
# https://discuss.streamlit.io/t/conditional-formatting-of-column-based-on-the-max-min-values-within-the-column/33775/3
def generate_colourmap_js(data: pd.Series, c_count=3, colourmap_name="viridis"):

    cmap = mpl.colormaps[colourmap_name]
    # linear colour mapping
    q_range = pd.Series(range(min(data), max(data), c_count)).values
    # robust colour mapping (ignores extreme values)
    if st.session_state.selected_cmap_style == "robust":
        q_range = pd.Series(range(int(data.quantile(0.02)), int(data.quantile(0.98)), c_count)).values
    # adjust expected number of colours
    c_count = len(q_range)

    col_i = 0
    prev_min_thresh = min(data)
    js_string = str()
    for i in range(0, c_count+1):
        js_section = ""
        if i == 0:
            js_section = colourmap_format(min(data), q_range[1], cmap(0))
        elif i == c_count:
            js_section = colourmap_format(q_range[-1], max(data)+1, cmap(c_count/c_count))
        else:
            # prevent colours from sliding up the cmap divisions with duplicate thresholds
            if prev_min_thresh != q_range[i-1]:
                js_section = colourmap_format(q_range[i-1], q_range[i], cmap(i/c_count))
            else:
                js_section = colourmap_format(q_range[i-1], q_range[i], cmap(col_i/c_count))
            prev_min_thresh = q_range[i-1]
        js_string += js_section

    return js_string


def req_crosstab(_x_attribute, _y_attribute):
    """
    Get the results for an attribute crosstab query.
    """

    payload = {
        "attIdx": _x_attribute.AttributeId,
        "setIdx": _x_attribute.SetId,
        "attIdy": _y_attribute.AttributeId,
        "setIdy": _y_attribute.SetId,
        "included": True,
        "graphic": "table"
    }
    record_json = st.session_state.session.post("https://eppi.ioe.ac.uk/eppi-vis/Frequencies/GetCrosstabJSON",
                                                data=payload, cookies={"WebDbErLoginCookie": st.session_state.cookie})
    # read dataframe with a column of record count arrays
    df = pd.DataFrame(record_json.json()["rows"])

    data = {_x_attribute.AttributeName: record_json.json()["columnAttNames"]}
    # convert count arrays into columns
    for i in range(len(df)):
        col_name = df["attributeName"][i]
        # this is needed to prevent issues when showing results for type of ai x descriptive text codes
        # (we could also add the y attribute name to every relevant column)
        if col_name == _x_attribute.AttributeName:
            col_name += " ({})".format(_y_attribute.AttributeName)
        data[col_name] = df["counts"][i]
    # data to be displayed
    df = pd.DataFrame(data)

    return df


def aggrid_view(df, x_attribute, y_attribute):
    """
    Configure AgGrid options and display given DataFrame.
    """

    # store all counts
    all_data = pd.Series(df.loc[:, df.columns != x_attribute].values.ravel("F"))
    # determine the number of colours needed
    c_count = min(len(all_data.unique()) + 1, 10)
    # colourmap javascript
    cmap_js = generate_colourmap_js(all_data, c_count=c_count, colourmap_name=st.session_state.selected_color_theme)

    gb = GridOptionsBuilder()
    # set columns to fill entire table, wrap text, and auto-adjust row height
    gb.configure_default_column(flex=1, wrapText=True, autoHeight=True)
    for col in df.columns:
        # add heatmap colouration to numeric columns
        if df[col].dtype == "int64" or df[col].dtype == "float64":
            gb.configure_column(col, titlecase(col), flex=1, minWidth=100,
                                cellStyle=JsCode(f"""function(params){{{cmap_js}}}"""))
        else:
            gb.configure_column(col, titlecase(col), flex=2, minWidth=150)
    # click a cell to learn more about the crosstab
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    # prevent drag column hiding
    gb.configure_grid_options(suppressDragLeaveHidesColumns=True)
    # display with aggrid
    ag = AgGrid(df, gridOptions=gb.build(), theme="streamlit", allow_unsafe_jscode=True, enable_enterprise_modules=True)

    # focus a cell to show additional information
    if ag.grid_response.get("gridState"):
        # find row and column based on focused cell
        row_index = ag.grid_response["gridState"]["focusedCell"]["rowIndex"]
        col_name = ag.grid_response["gridState"]["focusedCell"]["colId"]
        if y_attribute in col_name:
            col_name = col_name.replace(" ({0})".format(y_attribute), "")

        # get attributes
        x_sub_attribute = [a for a in st.session_state.attributes_list
                           if ag.data.iloc[row_index][x_attribute] == a.AttributeName and not a.HasChildren][0]
        y_sub_attribute = [a for a in st.session_state.attributes_list
                           if col_name == a.AttributeName and not a.HasChildren][0]
        selected_searchable = [x_sub_attribute.AttributeId, y_sub_attribute.AttributeId]
        set_ids = [x_sub_attribute.SetId, y_sub_attribute.SetId]

        total_records = 0
        df = pd.DataFrame()
        # first page
        if len(selected_searchable) > 0:
            df, total_records = req_first_page(selected_searchable, set_ids)

        # determine search string
        search_string = " [AND] ".join(["`{0}`".format(a.AttributeName) for a in st.session_state.attributes_list
                                        if a.AttributeId in selected_searchable])
        st.write("Search:", search_string if search_string else None)
        st.write("Records Found:", total_records)
        # subsequent pages
        for i in range(1, ceil(total_records/100)):
            new_df = req_next_page(i, search_string, selected_searchable, set_ids)
            df = pd.concat([df, new_df], ignore_index=True)

        # display with aggrid
        all_pages.pg_record_view.aggrid_view(df)


def demo_p4():
    """
    A page where attribute crosstab record counts are displayed in table heatmap format.
    TODO: Click a cell to display a table of records at the given attribute cross-section.
    """

    st.write("##### Attribute Crosstabs")

    if "display_crosstab" not in st.session_state:
        st.session_state["display_crosstab"] = False
    with st.form(key="crosstab_form"):
        parent_attributes = [a for a in st.session_state.attributes_list if a.HasChildren]
        parent_attribute_names = [a.AttributeName for a in parent_attributes]
        col1, col2 = st.columns(2)
        with col1:
            parent_1 = st.selectbox("Select X Parent Attribute", options=parent_attribute_names,
                                    key="crosstab_parent_1")
        with col2:
            parent_2 = st.selectbox("Select Y Parent Attribute", options=parent_attribute_names,
                                    key="crosstab_parent_2")
        # identify attributes to request a crosstab of
        attribute_1 = parent_attributes[parent_attribute_names.index(parent_1)]
        attribute_2 = parent_attributes[parent_attribute_names.index(parent_2)]

        # colour theme options from matplotlib
        colour_theme_list = ["viridis", "cividis", "inferno", "magma", "plasma", "rainbow", "turbo",
                             "twilight", "twilight_shifted", "berlin", "managua", "vanimo",
                             "spring", "summer", "autumn", "winter", "rocket", "mako",
                             "icefire", "vlag", "flare", "crest"]
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.selected_color_theme = st.selectbox("Select a Colour Theme", colour_theme_list)
        with col2:
            st.session_state.selected_cmap_style = st.selectbox("Select a Colour Map Style", ["linear", "robust"])
        form_submit = st.form_submit_button("View")
        if form_submit:
            st.session_state.display_crosstab = True

    if st.session_state.display_crosstab:
        # crosstab dataframe
        df = req_crosstab(attribute_1, attribute_2)

        st.write("##### Overview")
        _, overview_col, _ = st.columns(3)
        # display a miniature full view of the heatmap
        with overview_col:
            fig, _ = plt.subplots()
            sns.heatmap(df.loc[:, df.columns != attribute_1.AttributeName], xticklabels=False, yticklabels=False,
                        annot=False, cbar=False, cmap=st.session_state.selected_color_theme,
                        robust=True if st.session_state.selected_cmap_style != "linear" else False)
            st.write(fig)

        st.write("#####", attribute_1.AttributeName, "x", attribute_2.AttributeName)
        aggrid_view(df, attribute_1.AttributeName, attribute_2.AttributeName)
