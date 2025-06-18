import os
from pathlib import Path

import requests
import streamlit as st
from all_pages.pg_1 import demo_p1
from all_pages.pg_2 import demo_p2
from all_pages.pg_3 import demo_p3
from all_pages.pg_dashboard import dashbd
from all_pages.pg_home import home
from all_pages.pg_record_view import view_records
from all_pages.pg_boolean_search import boolsearcher
from API_calls import get_all_attributes, get_year_histogram
from utils import initialise_state


def update_ui(session, cookie):
    """
    The primary function used to display a Streamlit application for an EPPI visualisation demo.

    Args:
        session: A requests session connecting to the EPPI-Vis API. Used for further queries.
        cookie: A login cookie for the session.
    """

    # store information upon application launch
    if st.session_state.get("session") is None:
        st.session_state.eppi_base_url = "https://eppi.ioe.ac.uk"
        st.session_state.eppi_icon = os.path.join(Path(__file__).parent, "resources/EPPI_small_logo.png")
        st.session_state.session = session
        st.session_state.cookie = cookie
        get_all_attributes()  # retrieve all and store in session state as list of attribute objects
        get_year_histogram()

    # set basic settings
    st.set_page_config(page_title="EPPI Vis Demo", page_icon=st.session_state.eppi_icon,layout="wide")

    st.logo(st.session_state.eppi_icon, size="large", link="https://eppi.ioe.ac.uk/EPPI-Vis/Review/Index/536")

    # all application pages
    # icons: 'https://fonts.google.com/icons
    homepage = st.Page(home, title="Home", icon=":material/home:")
    record_table = st.Page(view_records, title="View Records", icon=":material/density_medium:")


    p1 = st.Page(demo_p1, title="Demo Page 1: Bar Chart", icon=":material/dashboard:")
    p2 = st.Page(demo_p2, title="Demo Page 2: Pie Chart", icon=":material/data_check:")
    p3 = st.Page(demo_p3, title="Demo Page 3: Terminology Explorer", icon=":material/workspaces:")
    st.session_state.p4=st.Page(boolsearcher, title="Demo Page 4: Advanced Search", icon=":material/workspaces:")#added to sessions tate because I need to link to it on the dashboard

    st.session_state.dashboardpage = st.Page(dashbd, title="Dashboard", icon=":material/dashboard:")#run last since it pulls in figures from other pages such as sunburst

    # display page navigation menu in sidebar
    pages = st.navigation({"": [homepage, record_table, st.session_state.dashboardpage], "Demo Visualisations": [p1, p2, p3, st.session_state.p4]})
    # settings_menu()

    pages.run()


def main():
    # set up session
    initialise_state()  # initialises some session state variables
    session = requests.session()
    session.get("https://eppi.ioe.ac.uk/EPPI-Vis/Login/Open?WebDBid=536")
    # get login cookie
    cookie = session.cookies["WebDbErLoginCookie"]
    # display ui
    update_ui(session, cookie)


if __name__ == "__main__":
    main()
