import streamlit as st
from bs4 import BeautifulSoup
from titlecase import titlecase


def home():
    """
    Home page. Features EPPI-Vis description.
    """

    # get home page content
    eppi_html = st.session_state.session.get(
        "".join([st.session_state.eppi_base_url, "/EPPI-Vis/Review/Index"])
    )
    # parse html response
    soup = BeautifulSoup(eppi_html.text, "html.parser")
    # get title and subtitle
    main_panel = soup.find("div", class_="main-panel")
    page_title = titlecase(main_panel.find("h2").text)
    page_subtitle = titlecase(main_panel.find("h5").text)
    # get description
    card_category = soup.find("div", class_="card-category")
    page_description = card_category.find_all("p")
    # get logos
    logos = soup.find_all("img", class_="pb-2 ml-auto")
    eppi_logo = "".join([st.session_state.eppi_base_url, logos[0].attrs["src"]])
    campbell_logo = "".join([st.session_state.eppi_base_url, logos[1].attrs["src"]])

    # display content
    st.markdown("## {0}".format(page_title))
    st_col, logo_col = st.columns(2, vertical_alignment="center")
    with st_col:
        st.markdown("#### {0}".format(page_subtitle))
    with logo_col:
        logo_1, logo_2 = st.columns(2)
        with logo_1:
            st.markdown(
                "<img src='{0}' width='90' "
                "style='display: block; float: right; margin: 0 auto;'>".format(
                    eppi_logo
                ),
                unsafe_allow_html=True,
            )
        with logo_2:
            st.markdown(
                "<img src='{0}' width='140' "
                "style='display: block; float: right; margin: 0 auto;'>".format(
                    campbell_logo
                ),
                unsafe_allow_html=True,
            )
    st.markdown(
        "<style> [data-testid='stExpander'] details {border-style: none;} </style>",
        unsafe_allow_html=True,
    )
    st.markdown("##### Introduction")
    for p in page_description:
        # split and join improve formatting of original text
        st.write(" ".join(p.text.split()))
    st.link_button(
        "Visit the original EPPI-Vis page",
        "https://eppi.ioe.ac.uk/EPPI-Vis/Review/Index/536",
    )
