from math import ceil

import pandas as pd
import streamlit as st
from api_calls import req_first_page, req_next_page
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from streamlit_tree_select import tree_select
from utils import downloader


def aggrid_view(df):
    """
    Configure AgGrid options and display given DataFrame.
    """

    # aggrid options
    gb = GridOptionsBuilder()
    # set columns to fill entire table, wrap text, and auto-adjust row height
    gb.configure_default_column(flex=1, wrapText=True, autoHeight=True)
    # disable cell data type to allow cell html to render properly
    gb.configure_column(
        "title",
        "Title",
        flex=4,
        minWidth=300,
        resizable=False,
        cellDataType=False,
        cellRenderer=JsCode("""
                        class UrlCellRenderer {
                            init (row) {
                                this.eGui = document.createElement('span');
                                if (!row.data.url) {this.eGui.innerHTML = row.data.title;}
                                else {this.eGui.innerHTML = `<a href="${row.data.url}"
                                      target="_blank">${row.data.title}</a>`;}
                            }
                            getGui() {return this.eGui;}
                        }
                        """),
    )
    gb.configure_column("authors", "Authors", flex=3, minWidth=200, resizable=False)
    gb.configure_column("year", "Year", flex=1, minWidth=70, resizable=False)
    gb.configure_column(
        "quickCitation",
        "Citation",
        flex=5,
        minWidth=400,
        resizable=False,
        cellDataType=False,
        cellRenderer=JsCode("""
                        class HTMLCellRenderer {
                            init (row) {
                                this.eGui = document.createElement('span');
                                this.eGui.innerHTML = row.data.quickCitation;
                            }
                            getGui() {return this.eGui;}
                        }
                        """),
        hide=True,
    )
    # click a row to learn more about the record
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    # deselect row with ctrl + click
    # FIXME: is there a more intuitive deselection method?
    gb.configure_grid_options(rowDeselection=True)
    # prevent drag column hiding
    gb.configure_grid_options(suppressDragLeaveHidesColumns=True)
    # present table data in pages
    gb.configure_pagination(True, paginationPageSize=20, paginationAutoPageSize=False)

    # display with aggrid
    ag = AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
    )

    # select a row to show additional information
    if ag.selected_data is not None:
        st.write("##### Selected Record")
        # FIXME: accessing selected_data produces many warnings - is there a way to suppress them?
        with st.container(border=True):
            # display more record details
            st.html("<h3>" + ag.selected_data["title"].values[0] + "</h3>")
            if ag.selected_data["abstract"].values[0] != "":
                st.markdown("###### Abstract")
                st.html(ag.selected_data["abstract"].values[0])
            st.html("<b>Author(s):</b> " + ag.selected_data["authors"].values[0])
            if ag.selected_data["quickCitation"].values[0] != "":
                st.html(
                    "<b>Quick Citation:</b> "
                    + ag.selected_data["quickCitation"].values[0]
                )
            if ag.selected_data["doi"].values[0] != "":
                st.html("<b>DOI:</b> " + ag.selected_data["doi"].values[0])
            if ag.selected_data["url"].values[0] != "":
                st.html(
                    '<b>URL:</b> <a href="'
                    + ag.selected_data["url"].values[0]
                    + '" target="_blank">'
                    + ag.selected_data["url"].values[0]
                    + "</a>"
                )


def view_records():
    """
    A page where records are displayed in table format. Click a row to select a record and
    display more information about it below the table. Ctrl + click a row to de-select it.
    """

    filter_status = None
    st.write("##### Attribute Filter")
    with st.container(border=True):
        # allow user to select desired attributes from a tree
        filter_status = tree_select(st.session_state.treestructures)

    # ignore top-level attributes (they are not searchable)
    selected_searchable = [
        int(x)
        for x in filter_status["checked"]
        if int(x)
        in [
            a.AttributeId for a in st.session_state.attributes_list if not a.HasChildren
        ]
    ]
    set_ids = [
        a.SetId
        for a in st.session_state.attributes_list
        if a.AttributeId in selected_searchable
    ]

    total_records = 0
    df = pd.DataFrame()
    # first page
    if len(selected_searchable) > 0:
        df, total_records = req_first_page(selected_searchable, set_ids)

    # determine search string
    search_string = " [AND] ".join(
        [
            "`{0}`".format(a.AttributeName)
            for a in st.session_state.attributes_list
            if a.AttributeId in selected_searchable
        ]
    )
    st.write("Search:", search_string if search_string else None)
    st.write("Records Found:", total_records)
    # subsequent pages
    for i in range(1, ceil(total_records / 100)):
        new_df = req_next_page(i, search_string, selected_searchable, set_ids)
        df = pd.concat([df, new_df], ignore_index=True)

    # display with aggrid
    downloader(df)
    aggrid_view(df)
