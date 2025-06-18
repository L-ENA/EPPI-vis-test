import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def initialise_state():
    if "max_length_int" not in st.session_state:
        st.session_state.max_length_int = 50
    if "max_codes_slider_value" not in st.session_state:
        st.session_state.max_codes_slider_value = 10
    if "max_length_textbox" not in st.session_state:
        st.session_state.max_length_textbox = "50"
    if "selected_color_theme" not in st.session_state:
        st.session_state.selected_color_theme = "viridis"
    if 'display_df' not in st.session_state:
        st.session_state.display_df = pd.DataFrame()
    if 'frequency_counts' not in st.session_state:
        st.session_state.frequency_counts = {}
    if 'year_histogram_df' not in st.session_state:
        st.session_state.year_histogram_df = pd.DataFrame()
    if "search_info_retrieval" not in st.session_state:
        st.session_state.search_info_retrieval = []

def settings_menu():



        # Sidebar settings menu
    st.sidebar.header("⚙️ Settings Menu")
    color_theme_list = ['viridis','blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo'
                            ]
    st.session_state.selected_color_theme = st.sidebar.selectbox('Select a color theme', color_theme_list)

    # Integer slider input
    st.sidebar.slider(
        "Maximum Number of Codes in Plots",
        min_value=2,
        max_value=100,
        value=10,
        key="max_codes_slider_value"
    )

    # Integer-only text input with validation
    st.sidebar.text_input("Maximum Length of Labels in Plots", key="max_length_textbox")

    # Validate input
    if st.session_state.max_length_textbox:
        if st.session_state.max_length_textbox.isdigit() and int(st.session_state.max_length_textbox)>0:
            st.session_state.max_length_int = int(st.session_state.max_length_textbox)
            st.sidebar.success(f"Current label length: {st.session_state.max_length_int} characters")
        else:
            st.sidebar.error("❌ Please enter a valid integer.")

# def aggrid_view(df):
#     """
#     Configure AgGrid options and display given DataFrame.
#     """
#
#     # aggrid options
#
#
#
#     gb = GridOptionsBuilder()
#     # set columns to fill entire table, wrap text, and auto-adjust row height
#     gb.configure_default_column(flex=1, wrapText=True, autoHeight=True)
#     # disable cell data type to allow cell html to render properly
#     gb.configure_column("title", "Title", flex=4, minWidth=300, resizable=False, cellDataType=False,
#                         cellRenderer=JsCode("""
#                         class UrlCellRenderer {
#                             init (row) {
#                                 this.eGui = document.createElement('span');
#                                 if (!row.data.url) {this.eGui.innerHTML = row.data.title;}
#                                 else {this.eGui.innerHTML = `<a href="${row.data.url}"
#                                       target="_blank">${row.data.title}</a>`;}
#                             }
#                             getGui() {return this.eGui;}
#                         }
#                         """))
#     gb.configure_column("authors", "Authors", flex=3, minWidth=200, resizable=False)
#     gb.configure_column("year", "Year", flex=1, minWidth=70, resizable=False)
#     gb.configure_column("quickCitation", "Citation", flex=5, minWidth=400, resizable=False, cellDataType=False,
#                         cellRenderer=JsCode("""
#                         class HTMLCellRenderer {
#                             init (row) {
#                                 this.eGui = document.createElement('span');
#                                 this.eGui.innerHTML = row.data.quickCitation;
#                             }
#                             getGui() {return this.eGui;}
#                         }
#                         """), hide=True)
#     # click a row to learn more about the record
#     gb.configure_selection(selection_mode="single", use_checkbox=False)
#     # deselect row with ctrl + click
#     # FIXME: is there a more intuitive deselection method?
#     gb.configure_grid_options(rowDeselection=True)
#     # prevent drag column hiding
#     gb.configure_grid_options(suppressDragLeaveHidesColumns=True)
#     # present table data in pages
#     gb.configure_pagination(True, paginationPageSize=20, paginationAutoPageSize=False)
#
#     # display with aggrid
#     ag = AgGrid(df, gridOptions=gb.build(), theme="streamlit", allow_unsafe_jscode=True, enable_enterprise_modules=True)
#
#     # select a row to show additional information
#     if ag.selected_data is not None:
#         st.write("##### Selected Record")
#         # FIXME: accessing selected_data produces many warnings - is there a way to suppress them?
#         with st.container(border=True):
#             # display more record details
#             st.html("<h3>"+ag.selected_data["title"].values[0]+"</h3>")
#             if ag.selected_data["abstract"].values[0] != "":
#                 st.markdown("###### Abstract")
#                 st.html(ag.selected_data["abstract"].values[0])
#             st.html("<b>Author(s):</b> " + ag.selected_data["authors"].values[0])
#             if ag.selected_data["quickCitation"].values[0] != "":
#                 st.html("<b>Quick Citation:</b> " + ag.selected_data["quickCitation"].values[0])
#             if ag.selected_data["doi"].values[0] != "":
#                 st.html("<b>DOI:</b> " + ag.selected_data["doi"].values[0])
#             if ag.selected_data["url"].values[0] != "":
#                 st.html("<b>URL:</b> <a href=\"" + ag.selected_data["url"].values[0] +
#                         "\" target=\"_blank\">" + ag.selected_data["url"].values[0] + "</a>")

def adding(lines,key, value):
    if len(value)>0:
        lines.append("{}  - {}".format(key,value.strip()))
    return lines

def add_record(lines, i, row):
    pt=str(row["typeName"]).replace(",", "").strip()

    #
    lines.append('TY  - JOUR')
    lines = adding(lines, "T1", str(row["title"]))
    #lines = adding(lines, "OP", str(row["OriginalTitle"]))
    lines = adding(lines, "N2", str(row["abstract"]))
    for a in row["authors"].split(";"):
        lines = adding(lines, "A1", str(a).strip())
    lines = adding(lines, "IS", str(row["issue"]))
    lines = adding(lines, "VL", str(row["volume"]))

    lines = adding(lines, "JO", str(row["parentTitle"]))
    lines = adding(lines, "SP", str(row["pages"]))
    try:
        lines = adding(lines, "PY", str(int(row["year"])))  # or else we will get a float, ie. year 2022.0
    except:
        lines = adding(lines, "PY", str(row["year"]))
    #lines = adding(lines, "LA", str(row["Language"]))
    #lines = adding(lines, "AD", str(row["User defined 3"]))
    lines = adding(lines, "SN", str(row["standardNumber"]))
    lines = adding(lines, "DO", str(row["doi"]))
    lines = adding(lines, "CY", str(row["city"]))
    lines = adding(lines, "PB", str(row["publisher"]))
    lines = adding(lines, "UR", str(row["url"]))

    #lines = adding(lines, "KW", str(row["Language"]))
    #lines = adding(lines, "KW", pt)
    #lines = adding(lines, "KW", str(row["Language"]))
    # lines = adding(lines, "ET", str(row["Edition"]))



    #####################add a notes field

    notes = str(row["quickCitation"])
    lines.append("N1  - {}".format(notes))
    lines.append('ER  - ')
    lines.append("")
    return lines

def to_ris(df):
    lines = []
    for i,row in df.iterrows():
        lines = add_record(lines, i, row)

    lines='\n'.join(lines)
    return lines


def downloader(indf):

    d1, d2 = st.columns(2)
    with d1:
        if st.button("Download Options",icon=":material/download:"):
            with st.popover("Select"):
                @st.cache_data
                def convert_ris_download(df):
                    return to_ris(df)

                @st.cache_data
                def convert_for_download(df, encoding):
                    return df.to_csv().encode(encoding)

                # csv1 = convert_for_download(dfs[0], "utf-8")
                myris = convert_ris_download(indf)
                st.download_button(
                    label="RIS",
                    data=myris,
                    file_name="data_{}_records.ris".format(indf.shape[0]),
                    mime="text/csv",
                    icon=":material/download:",
                )

                csv1 = convert_for_download(indf, "utf-8-sig")

                st.download_button(
                    label="Download CSV (UTF-8-sig)",
                    data=csv1,
                    file_name="data_{}_records.csv".format(indf.shape[0]),
                    mime="text/csv",
                    icon=":material/download:",
                )
                # csv2 = convert_for_download(dfs[0], "windows-1252")
                #
                # st.download_button(
                #     label="Download Windows-1252 CSV",
                #     data=csv2,
                #     file_name="data_{}_records.csv".format(dfs[0].shape[0]),
                #     mime="text/csv",
                #     icon=":material/download:",
                # )
    with d2:
        st.session_state.dashboard_df = indf
        st.page_link(st.session_state.dashboardpage, label="Send to dashboard", icon="📊")
def process_df(df):
    # Load the CSV file

    # Step 1: Make 'character' entries unique by appending 'parent' if duplicates exist
    duplicates = df['character'].duplicated(keep=False)
    df['character'] = df.apply(
        lambda row: f"{row['character']} ({row['parent']})" if duplicates[row.name] and row['parent']!="" else row['character'],
        axis=1
    )


    # Step 2: Build mapping of each parent to the sum of its children's values
    value_sums = df.groupby('parent')['value'].sum()

    # Step 3: Add own value only if character is not referenced as a parent anywhere
    df['new_value'] = df['character'].map(value_sums).fillna(0)
    not_in_parent = ~df['character'].isin(df['parent'].dropna().unique())
    df.loc[not_in_parent, 'new_value'] += df.loc[not_in_parent, 'value']

    # Step 4: Replace 'value' with the updated values
    df['value'] = df['new_value'].astype(int)
    df.drop(columns=['new_value'], inplace=True)

    return df

# def test_sunburst():
#     import json
#     import pandas as pd
#     import plotly.express as px
#     from API_calls import extract_all_attributes
#     # Load the attributes data
#     # Build lookup dicts
#     import requests
#     import json
#
#     Url = 'https://eppi.ioe.ac.uk/EPPI-Vis/Login/Open?WebDBid=536'
#     # Url = 'https://eppi.ioe.ac.uk/EPPI-Vis/Login/DoLogin'
#
#     session = requests.session()
#     session.get(Url)
#
#     cookie = session.cookies['WebDbErLoginCookie']
#     r3 = session.get('https://eppi.ioe.ac.uk/eppi-vis/ReviewSetList/FetchJSON',
#                      cookies={'WebDbErLoginCookie': cookie})
#     atts = r3.json()
#
#     attributes = []
#
#     for i, _ in enumerate(atts):
#         attribute_data = extract_all_attributes(atts, i)
#         attributes.extend(attribute_data)
#
#
#     id_to_name = {att.AttributeId: att.AttributeName for att in attributes}
#     parent_map = {att.AttributeId: att.ParentAttributeId for att in attributes}
#
#     # Prepare rows for DataFrame
#     sunburst_data = []
#
#     for att in attributes:
#         current_id = att.AttributeId
#         current_name = att.AttributeName
#         parent_id = att.ParentAttributeId
#
#         parent_name = id_to_name.get(parent_id, "") if parent_id != 0 else ""
#
#         ######Need to get the value counts.
#         #Idea: 1 get the frequency counts using
#
#
#         sunburst_data.append({
#             "character": current_name,
#             "parent": parent_name,
#             "value": 1  # Default value, can be updated based on application
#         })
#
#     # Create DataFrame
#     df = pd.DataFrame(sunburst_data)
#
#     #################postprocess to: Get parent counts and make names unique
#     df=process_df(df)
#
#     print(df.head())
#
#     # Create sunburst plot
#     fig = px.sunburst(
#         df,
#         names="character",
#         parents="parent",
#         values="value"
#     )
#
#     fig.show()
#     df.to_csv(r"C:\Users\qtnzls7\PycharmProjects\EPPI-Vis\streamlit-demo\data\pg_3_final.csv".format(df.shape[0]))
#
# def plot_sunburst():
#     import pandas as pd
#     import plotly.express as px
#     df=pd.read_csv(r"C:\Users\qtnzls7\PycharmProjects\EPPI-Vis\streamlit-demo\data\pg_3_processed_updated.csv")
#     fig = px.sunburst(
#         df,
#         names="character",
#         parents="parent",
#         values="value"
#     )
#
#     fig.show()
#
# import pandas as pd
#
#
# # Example usage
# #process_csv("data/pg_3_processed.csv", "data/pg_3_processed_updated.csv")
# test_sunburst()

#plot_sunburst()