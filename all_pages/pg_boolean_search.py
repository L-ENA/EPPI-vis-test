import datetime
import re
from time import time as timefunc

import pandas as pd
import plotly.express as px
import streamlit as st
from all_pages.pg_record_view import aggrid_view
from annotated_text import annotated_text, annotation
from api_calls import *
from streamlit.components.v1 import html
from utils import *


def rgb_to_rgba(rgb_string, alpha):
    """Converts an RGB string to an RGBA string.
    Args:
        rgb_string: The RGB color string (e.g., "rgb(255, 0, 100)").
        alpha: The desired alpha value (float between 0 and 1).
    Returns:
        An RGBA color string (e.g., "rgba(255, 0, 100, 0.5)") or None if invalid input
    """
    match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb_string)
    if not match:
        return None
    r, g, b = map(int, match.groups())
    return f"rgba({r}, {g}, {b}, {alpha})"


def search_sessionstate_init():
    if "name_to_ids" not in st.session_state:
        st.session_state.name_to_ids = {}

    if "picooptions" not in st.session_state:
        st.session_state.picooptions = {}
        get_all_attributes()
        for attribute in st.session_state.attributes_list:
            if attribute.HasChildren:
                if (
                    "{}_{}".format(attribute.AttributeId, attribute.SetId)
                    not in st.session_state.frequency_counts
                ):
                    st.session_state.frequency_counts[
                        "{}_{}".format(attribute.AttributeId, attribute.SetId)
                    ] = get_frequency_counts(
                        attribute.AttributeId, attribute.SetId, included=True
                    )

                freqs = st.session_state.frequency_counts[
                    "{}_{}".format(attribute.AttributeId, attribute.SetId)
                ]

                st.session_state.picooptions[attribute.AttributeName] = [
                    list(freqs["Codes"]),
                    attribute,
                ]

    if "searchdoc" not in st.session_state:
        st.session_state.searchdoc = []
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "picogroups" not in st.session_state:
        st.session_state.picogroups = []
    if "operators" not in st.session_state:
        st.session_state.operators = []
    if "this_operator" not in st.session_state:
        st.session_state.this_operator = ""
    if "freetext_query" not in st.session_state:
        st.session_state.freetext_query = ""

        # st.session_state.picooptions['CodeB']=sorted(["BA", "BB", "BX", "BC", ])
        # st.session_state.picooptions['CodeC']=sorted(["hello", "testBB", "BX", "BC", ])
    # st.write(st.session_state.attributes_list)


def year_filtering():
    yearfilter = st.toggle(
        "Add Publication Year Filter (Toy function)",
    )
    if yearfilter:
        if st.session_state.year_histogram_df.shape[0] == 0:
            get_year_histogram()
        yrlist = sorted(
            st.session_state.year_histogram_df["Year"].unique(), reverse=True
        )
        selected_years = st.multiselect("Select Year(s)", yrlist, key="filtered_years")

        # Create the Line Chart
        def move_first_row_to_last(df):
            first_row = df.iloc[[0]]
            rest_of_df = df.iloc[1:]
            new_df = pd.concat([rest_of_df, first_row], ignore_index=True)
            return new_df

        mydata = move_first_row_to_last(st.session_state.year_histogram_df)
        fig = px.line(mydata, x="Year", y="Counts", template="simple_white")
        st.plotly_chart(fig, use_container_width=True)
        # st.session_state.picooptions['CodeB']=sorted(["BA", "BB", "BX", "BC", ])
        # st.session_state.picooptions['CodeC']=sorted(["hello", "testBB", "BX", "BC", ])
    # st.write(st.session_state.attributes_list)


def boolsearcher():
    st.markdown("# Database Search")
    search_sessionstate_init()
    with st.sidebar:
        year_filtering()

    textsearch = st.toggle(
        "Advanced text search",
    )
    if textsearch:
        st.text_input(
            "Freetext Query",
            placeholder="Enter Freetext Query, eg. title:'AI equity'~5 AND abstract:(machine OR learn*)",
            key="freetext_query",
        )
        st.session_state.multiselect = []
    else:
        if len(st.session_state.freetext_query) == 0:
            picooption = st.selectbox(
                "Select Concept",
                set(st.session_state.picooptions.keys()),
                index=0,
                placeholder="Click here to select",
                key="picooption",
            )

            multi = st.multiselect(
                "Optional: Select '{}' concepts (or leave blank and add search arm to select all)".format(
                    picooption
                ),
                st.session_state.picooptions[picooption][0],
                key="multiselect",
            )

    def clear_multi():
        st.session_state.multiselect = []
        st.session_state.freetext_query = ""
        return

    def clear_all():
        st.session_state.multiselect = []
        st.session_state.picogroups = []
        st.session_state.searchdoc = []
        st.session_state.operators = []
        st.session_state.this_operator = ""
        st.session_state.submitted = False
        st.session_state.freetext_query = ""

    def add_and():
        st.session_state.operators.append("AND")
        add_pico()

    def add_or():
        st.session_state.operators.append("OR")
        add_pico()

    def add_empty():
        st.session_state.operators.append("")
        add_pico()

    def add_pico():
        # =["#faa", "#afa", "#8ef"]
        n_cols = len(st.session_state.picooptions.keys()) + 1

        colors_rgb = px.colors.sample_colorscale(
            "Rainbow", [n / (n_cols - 1) for n in range(n_cols)]
        )
        colors = []
        for c in colors_rgb:
            colors.append(rgb_to_rgba(c, 0.3))

        coldict = {
            val: colors[i] for i, val in enumerate(st.session_state.picooptions.keys())
        }
        coldict["Free Text Query"] = colors[-1]

        if st.session_state.multiselect == [] and st.session_state.freetext_query == "":
            print("QUERY EMPTY ADDING ALL")
            st.session_state.multiselect = st.session_state.picooptions[picooption][
                0
            ]  # add all options
            print(st.session_state.multiselect)
            print(type(st.session_state.multiselect))

        if len(st.session_state.freetext_query) > 0:
            print("ADDING QUERY")
            col = coldict["Free Text Query"]
            thislist = [(st.session_state.freetext_query, "Free Text Query", col)]
            st.session_state.searchdoc.append(thislist)
            clear_multi()

        elif len(st.session_state.multiselect) > 0:
            print("ADDING MULTISELECT")
            col = coldict[picooption]
            tblname = picooption

            # if picooption=="Intervention":#make colored output
            #     col="#faa"
            #     tblname="tblintervention"
            # elif picooption=="Outcome":
            #     col = "#afa"
            #     tblname = "tbloutcome"
            # elif picooption=="Health Condition":
            #     col="#8ef"
            #     tblname = "tblhealthcarecondition"
            st.session_state.picogroups.append(
                {tblname: st.session_state.multiselect}
            )  # for search

            thislist = []
            for sel in st.session_state.multiselect:
                thislist.append((sel, picooption, col))
                thislist.append(" OR ")
            del thislist[-1]  # delete last OR
            st.session_state.searchdoc.append(thislist)
            # st.session_state.searchdoc.append("{}: {}".format(picooption, " OR ".join(st.session_state.multiselect)))
            clear_multi()
        return

    col1, col1b, col2, col3 = st.columns(4)

    def submission():
        st.session_state.submitted = True

    if len(st.session_state.operators) > 0:
        with col1:
            st.button("Add as AND", on_click=add_and)

        with col1b:
            st.button("Add as OR", on_click=add_or)

        with col2:
            st.button("Submit search", on_click=submission, type="primary")

    else:
        with col1:
            st.button("Add selection", on_click=add_empty)

    with col3:
        st.button("⚠️Delete this search", on_click=clear_all)

        ##################################################################

    for i, sd in enumerate(st.session_state.searchdoc):
        if i != 0:
            if st.session_state.operators[i] == "AND":
                annotated_text(annotation("AND", "", "#faf", border="2px dashed red"))
            elif st.session_state.operators[i] == "OR":
                annotated_text(annotation("OR", "", "#24dde0", border="2px dashed red"))
        annotated_text(sd)
    with st.expander("View structured query", expanded=False):
        st.write(st.session_state.operators)
        st.divider()
        st.write(st.session_state.searchdoc)


    @st.cache_data
    def search_all(this_searchdoc):
        dfs = []
        now = datetime.datetime.now()
        progress_bar = st.progress(0)
        status_text = st.empty()

        st.markdown("## Search Documentation")
        formatted_date_time = now.strftime("%Y-%m-%d at %H:%M:%S")
        searchinfo = [
            "The following searches were carried out on {}".format(formatted_date_time)
        ]
        # st.code(searchinfo[-1], language="markdown")

        for i, sd in enumerate(st.session_state.searchdoc):  # for each arm
            progress = (i + 1) / len(st.session_state.searchdoc)
            progress_bar.progress(progress)
            status_text.text(
                f"Processing arm {i + 1} of {len(st.session_state.searchdoc)}"
            )

            searchinfo.append("\n\n>>> ARM {}:".format(i + 1))
            # st.code(searchinfo[-1], language="markdown")

            st.session_state.search_info_retrieval = []

            selected_attributes = []  # stor attributes to be OR'd together
            for entry in sd:
                if entry[1] == "Free Text Query":
                    myquery = entry[0]
                elif isinstance(entry, tuple):
                    # print(type(entry))
                    # print(entry)
                    # print("Name "+ entry[1])
                    # print("---")
                    # print(st.session_state.picooptions)
                    parentcode_name = entry[1]
                    this_name = entry[0]
                    this_parent = st.session_state.picooptions[parentcode_name][1]
                    for attribute in st.session_state.attributes_list:
                        if (
                            attribute.AttributeName == this_name
                            and attribute.ParentAttributeId == this_parent.AttributeId
                        ):
                            selected_attributes.append(attribute)
                            print(
                                "Successfully identified parent for {}".format(
                                    this_name
                                )
                            )

            if len(selected_attributes) > 0:
                current_arm = id_retrieval(selected_attributes)
                for indx, sir in enumerate(st.session_state.search_info_retrieval):
                    searchinfo.append(
                        "Searched <{}> and retreived {} results".format(
                            selected_attributes[indx].AttributeName, sir
                        )
                    )
                    # st.code(searchinfo[-1], language="markdown")

            else:
                if len(myquery) > 0:
                    myfield = "TitleAbstract"
                    current_arm = refs_per_textsearch(field=myfield, query=myquery)
                    searchinfo.append(
                        "Searched query <{}> on field <{}> and retrieved {} results".format(
                            myquery, myfield, current_arm.shape[0]
                        )
                    )

                else:
                    searchinfo.append(
                        "Warning: No Attribute and no queries found for this search"
                    )

            dfs.append(current_arm)
            # searchinfo.append(">>> query: {}".format(" [OR] ".join([a.AttributeName for a in selected_attributes])))
            searchinfo.append("\n{} results for this arm.".format(dfs[-1].shape[0]))
            # st.code(searchinfo[-1], language="markdown")
            if len(dfs) > 1:
                if (
                    st.session_state.operators[i] == "AND"
                ):  # keep records for which item ids are in both dfs
                    source = dfs[0]
                    target = dfs[1]
                    dfs = [source[source["itemId"].isin(target["itemId"])]]
                else:  # merge all items and remove duplicates only
                    merged = pd.concat(dfs)
                    merged = merged.drop_duplicates(subset=["itemId"], keep="first")
                    dfs = [merged]
                searchinfo.append(
                    "\nUsing [{}]: <{}> aggregated results between this and the previous arm.".format(
                        st.session_state.operators[i], dfs[0].shape[0]
                    )
                )
                # st.code(searchinfo[-1], language="markdown")
        status_text.text("Done! ✅")
        st.code("\n".join(searchinfo), language="markdown")
        st.divider()
        st.markdown(
            '<div id="my-section-{tab_id}"></div>'.format(tab_id="<your-tab-id>"),
            unsafe_allow_html=True,
        )
        st.markdown("## Search Results")

        return dfs[0]

    if st.session_state.submitted:
        outdf = search_all(st.session_state.searchdoc)

        downloader(outdf)
        # with st.popover("Download", icon=":material/download:"):
        #     @st.cache
        #     def convert_ris_download(df):
        #         return to_ris(df)
        #
        #     @st.cache_data
        #     def convert_for_download(df, encoding):
        #         return df.to_csv().encode(encoding)
        #
        #     #csv1 = convert_for_download(dfs[0], "utf-8")
        #     myris=convert_ris_download(dfs[0])
        #     st.download_button(
        #         label="RIS",
        #         data=myris,
        #         file_name="data_{}_records.ris".format(dfs[0].shape[0]),
        #         mime="text/csv",
        #         icon=":material/download:",
        #     )
        #
        #
        #     csv1 = convert_for_download(dfs[0], "utf-8-sig")
        #
        #     st.download_button(
        #         label="Download CSV (UTF-8-sig)",
        #         data=csv1,
        #         file_name="data_{}_records.csv".format(dfs[0].shape[0]),
        #         mime="text/csv",
        #         icon=":material/download:",
        #     )
        #     # csv2 = convert_for_download(dfs[0], "windows-1252")
        #     #
        #     # st.download_button(
        #     #     label="Download Windows-1252 CSV",
        #     #     data=csv2,
        #     #     file_name="data_{}_records.csv".format(dfs[0].shape[0]),
        #     #     mime="text/csv",
        #     #     icon=":material/download:",
        #     # )

        aggrid_view(outdf)

        html(
            """
                  <script>
                      // Time of creation of this script = {now}.
                      // The time changes everytime and hence would force streamlit to execute JS function
                      function scrollToMySection() {{
                          var element = window.parent.document.getElementById("my-section-{tab_id}");
                          if (element) {{
                              element.scrollIntoView({{ behavior: "smooth" }});
                          }} else {{
                              setTimeout(scrollToMySection, 100);
                          }}
                      }}
                      scrollToMySection();
                  </script>
                  """.format(now=timefunc(), tab_id="<your-tab-id>")
        )
