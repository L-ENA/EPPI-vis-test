from typing import List

import numpy as np
import pandas as pd
import streamlit as st
from data_definitions import Attribute


def build_nested_structure(attributes_list):
    nodes = []
    for attr in attributes_list:
        label = attr.get("attributeName", "").strip()
        value = str(attr.get("attributeId"))  # convert to string for consistency
        nested = attr.get("attributes", {}).get("attributesList", [])

        node = {"label": label, "value": value}

        if nested:
            node["children"] = build_nested_structure(nested)

        nodes.append(node)

    return nodes


def extract_structure(data, setnr=0):
    top_level_attrs = data[setnr].get("attributes", {}).get("attributesList", [])
    # print("Retrieved and stored tree structure.")
    return build_nested_structure(top_level_attrs)


def parse_attributes(attributes_list, result, parent_id=None):
    for attr in attributes_list:
        nested = attr.get("attributes", {}).get("attributesList", [])
        has_children = bool(nested)

        this_attribute = Attribute()
        this_attribute.AttributeName = attr.get("attributeName", "").strip()
        this_attribute.AttributeId = attr.get("attributeId")
        this_attribute.ParentAttributeId = attr.get("parentAttributeId", parent_id)
        this_attribute.SetId = attr.get("setId")
        this_attribute.AttributeSetDescription = attr.get(
            "attributeSetDescription", ""
        ).strip()
        this_attribute.HasChildren = has_children
        result.append(this_attribute)

        # recursively parse nested attributes
        if has_children:
            parse_attributes(nested, result, parent_id=attr.get("attributeId"))


def extract_all_attributes(data, setnr=0):
    all_attributes = []
    top_level_attrs = data[setnr].get("attributes", {}).get("attributesList", [])
    parse_attributes(top_level_attrs, all_attributes)
    return all_attributes


def get_all_attributes(return_list: bool = False):
    """
    if return_list, return the list as an object as well
    as saving to session state
    """
    req = st.session_state.session.get(
        "https://eppi.ioe.ac.uk/eppi-vis/ReviewSetList/FetchJSON",
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    attribute_list = req.json()

    # update attribute list only once at the start, or when specifically requested
    if (
        "attributes_list" not in st.session_state
        and "treestructures" not in st.session_state
    ):
        st.session_state.attributes_list = []
        st.session_state.treestructures = []

        for i, _ in enumerate(attribute_list):
            attribute_data = extract_all_attributes(attribute_list, i)
            st.session_state.treestructures = extract_structure(attribute_list, i)
            st.session_state.attributes_list.extend(attribute_data)

    # st.write(attribute_list)

    if return_list:
        return attribute_list

    # print("Retrieved and stored attributes.")


def get_frequency_counts(attId: int, setId: int, included: bool = True):
    """
    Retrieve frequency counts for a specific attribute
    :param attId: int
    :param setId: int
    :param included: bool
    :return: dict
    """

    df = pd.DataFrame()
    codes = []
    counts = []
    ids = []
    sets = []

    payload = {"attId": attId, "setId": setId, "included": included}
    # headers = {
    #     "Content-Type": "application/json"
    # }

    req = st.session_state.session.post(
        "https://eppi.ioe.ac.uk/eppi-vis/Frequencies/GetFrequenciesJSON",
        data=payload,
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    my_attributes = req.json().get("results", [])

    for entry in my_attributes:
        if entry["attributeId"] > 0:
            codes.append(entry["attribute"])
            counts.append(entry["itemCount"])
            ids.append(entry["attributeId"])
            sets.append(entry["setId"])

    df["Codes"] = codes
    df["Counts"] = counts
    df["attId"] = ids
    df["setId"] = sets

    return df


def clean_dedupe_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """
    NOTE: moved to API_calls from utils.

    cleans the attributes df for plotting.
    """
    # Step 1: Make 'character' entries unique by appending 'parent' if duplicates exist
    duplicates = df["character"].duplicated(keep=False)
    df["character"] = df.apply(
        lambda row: f"{row['character']} ({row['parent']})"
        if duplicates[row.name] and row["parent"] != ""
        else row["character"],
        axis=1,
    )

    # Step 2: Build mapping of each parent to the sum of its children's values
    value_sums = df.groupby("parent")["value"].sum()

    # Step 3: Add own value only if character is not referenced as a parent anywhere
    df["new_value"] = df["character"].map(value_sums).fillna(0)
    not_in_parent = ~df["character"].isin(df["parent"].dropna().unique())
    df.loc[not_in_parent, "new_value"] += df.loc[not_in_parent, "value"]

    # Step 4: Replace 'value' with the updated values
    df["value"] = df["new_value"].astype(int)
    df.drop(columns=["new_value"], inplace=True)

    return df


def attributes_to_hierarchical(clean: bool = True) -> pd.DataFrame:
    """
    produces a pandas df (required for producing plots
    with plotly) from the processed attributes retrieved
    from the API.

    args:
        clean: bool, whether to run clean_dedupe_attributes

    returns:
        df of attributes
    """
    sunburst_data = []

    id_to_name = {
        att.AttributeId: att.AttributeName for att in st.session_state.attributes_list
    }

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

    for att in st.session_state.attributes_list:
        current_id = att.AttributeId
        current_name = att.AttributeName
        parent_id = att.ParentAttributeId

        parent_name = id_to_name.get(parent_id, "") if parent_id != 0 else ""

        try:
            freqs = st.session_state.frequency_counts[
                "{}_{}".format(parent_id, attribute.SetId)
            ]

            sunburst_data.append(
                {
                    "character": current_name,
                    "parent": parent_name,
                    "value": freqs.loc[freqs["attId"] == current_id, "Counts"].iloc[0],
                }
            )
        except KeyError as e:
            # st.write(f"Error type: {type(e).__name__}")
            # st.write(f"Error message: {str(e)}")
            sunburst_data.append(
                {"character": current_name, "parent": parent_name, "value": 0}
            )

    df = pd.DataFrame(sunburst_data)

    if clean:
        df = clean_dedupe_attributes(df)

    return df


def add_years_to_attribute_df(
    df: pd.DataFrame,
    year_range: list[int] = list(range(2000, 2026)),
    random_seed: int | None = None,
) -> pd.DataFrame:
    """
    appends another column - `year` - to our attributes df,
    to allow subsetting our plot by a user-specified
    date range.

    for now (18/06/25) this will output **FAKE** data
    in order to experiment with the viz.

    NOTE: replace with real api-derived data.

    args:
        - df: pd.DataFrame returned from attributes_to_hierarchical()

    returns:
        - attributes_years_df: attribute_df with years column
        and hence more rows
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    new_rows = []
    n_years = len(year_range)

    for _, row in df.iterrows():
        # random weights summing to 1
        random_weights = np.random.dirichlet(np.ones(n_years))
        distributed_values = row["value"] * random_weights

        for year, dist_value in zip(year_range, distributed_values):
            new_row = row.copy()
            new_row["year"] = year
            new_row["value"] = int(np.floor(dist_value))
            new_rows.append(new_row)

    attributes_years_df = pd.DataFrame(new_rows)

    return attributes_years_df


def refs_per_textsearch(field="TitleAbstract", query="equity"):
    payload = {
        "onlyIncluded": True,
        "showDeleted": False,
        "sourceId": 0,
        "searchId": 0,
        "xAxisSetId": 0,
        "xAxisAttributeId": 0,
        "yAxisSetId": 0,
        "yAxisAttributeId": 0,
        "filterSetId": 0,
        "filterAttributeId": 0,
        "attributeSetIdList": "",
        "listType": "WebDbSearch",
        "pageNumber": 0,
        "pageSize": 100,
        "totalItems": 0,
        "startPage": 0,
        "endPage": 0,
        "startIndex": 0,
        "endIndex": 0,
        "workAllocationId": 0,
        "comparisonId": 0,
        "magSimulationId": 0,
        "description": "Search results for web-application",
        "contactId": 0,
        "setId": 0,
        "showInfoColumn": False,
        "showScoreColumn": False,
        "webDbId": 536,
        "withAttributesIds": "",
        "withSetIdsList": "",
        "withOutAttributesIdsList": "",
        "withOutSetIdsList": "",
        "searchWhat": field,
        "searchString": query,
    }
    headers = {"Content-Type": "application/json"}

    r4 = st.session_state.session.post(
        "https://eppi.ioe.ac.uk/eppi-vis/ItemList/ListFromCritJson",
        data=payload,
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    refs = r4.json()["items"]["items"]
    refdf = pd.DataFrame(refs)
    st.session_state.search_info_retrieval.append(refdf.shape[0])
    return refdf


def refs_per_code(attId, attName):
    payload = {"attId": attId, "attName": attName}
    # headers = {
    #     "Content-Type": "application/json"
    # }

    req = st.session_state.session.post(
        "https://eppi.ioe.ac.uk/eppi-vis/ItemList/GetFreqListJSON",
        data=payload,
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    refs = req.json()["items"]["items"]
    refdf = pd.DataFrame(refs)
    st.session_state.search_info_retrieval.append(refdf.shape[0])
    # print("Retrieved {} records".format(refdf.shape[0]))

    return refdf


def id_retrieval(my_atts: List[Attribute]):
    """
    This function retrieves references based on a list of attributes,
    where attributes will be OR'ed, meaning that there is once call to retrieve refs,
    they are added to the same dataframe, and as last step the frame is deduplicated
    based on reference ID.
    Args:
        my_atts:

    Returns: Pandas DataFrame

    """
    df_list = []
    for a in my_atts:
        df_list.append(refs_per_code(a.AttributeId, a.SetId))
    if len(df_list) > 0:
        merged = pd.concat(df_list)
        merged = merged.drop_duplicates(subset=["itemId"], keep="first")
    else:
        merged = pd.DataFrame()
    return merged


@st.cache_data
def update_display_df(idlist, setlist):
    filtered_atts = []
    for i, entry in enumerate(idlist):
        for a in st.session_state.attributes_list:
            if entry == a.AttributeId and setlist[i] == a.SetId:
                filtered_atts.append(a)

    my_data = id_retrieval(filtered_atts)
    st.session_state.display_df = my_data

    return my_data


def get_year_histogram():
    """
    This function retrieves year histogram and stores it in session state variable st.session_state.year_histogram_df
    Returns:

    """
    req = st.session_state.session.get(
        "https://eppi.ioe.ac.uk/eppi-vis/Review/YearHistogramJSON",
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )

    # st.write(req.json())

    counts = []
    years = []
    for entry in req.json():
        years.append(entry["year"])
        counts.append(entry["count"])

    st.session_state.year_histogram_df["Year"] = years
    st.session_state.year_histogram_df["Counts"] = counts
    st.session_state.year_histogram_df.sort_values(
        by=["Year"], ascending=True, inplace=True
    )

    # print("Retrieved and stored year histogram.")


@st.cache_data
def req_first_page(attribute_ids, set_ids):
    """
    Get the first page of results for an attribute search.
    """

    payload = {
        "WithAttIds": ",".join(map(str, attribute_ids)),
        "WithSetId": ",".join(map(str, set_ids)),
        "WithoutAttIds": "",
        "WithoutSetId": "",
        "included": True,
    }
    record_json = st.session_state.session.post(
        "https://eppi.ioe.ac.uk/eppi-vis/ItemList/GetListWithWithoutAttsJSON",
        data=payload,
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    # read as dataframe
    df = pd.DataFrame(record_json.json()["items"]["items"])
    total_records = record_json.json()["items"]["totalItemCount"]

    return df, total_records


@st.cache_data
def req_next_page(page_no, description, attribute_ids, set_ids):
    """
    Get subsequent pages of an attribute search.
    """

    payload = {
        "onlyIncluded": True,
        "showDeleted": False,
        "sourceId": 0,
        "searchId": 0,
        "xAxisSetId": 0,
        "xAxisAttributeId": 0,
        "yAxisSetId": 0,
        "yAxisAttributeId": 0,
        "filterSetId": 0,
        "filterAttributeId": 0,
        "attributeSetIdList": "",
        "listType": "WebDbWithWithoutCodes",
        "pageNumber": page_no,
        "pageSize": 100,
        "totalItems": 0,
        "startPage": 0,
        "endPage": 0,
        "startIndex": 0,
        "endIndex": 0,
        "workAllocationId": 0,
        "comparisonId": 0,
        "magSimulationId": 0,
        "description": description,
        "contactId": 0,
        "setId": 0,
        "showInfoColumn": False,
        "showScoreColumn": False,
        "webDbId": 536,
        "withAttributesIds": ",".join(map(str, attribute_ids)),
        "withSetIdsList": ",".join(map(str, set_ids)),
        "withOutAttributesIdsList": "",
        "withOutSetIdsList": "",
        "searchWhat": "",
        "searchString": "",
    }

    record_json = st.session_state.session.post(
        "https://eppi.ioe.ac.uk/eppi-vis/ItemList/ListFromCritJson",
        data=payload,
        cookies={"WebDbErLoginCookie": st.session_state.cookie},
    )
    # read as dataframe
    df = pd.DataFrame(record_json.json()["items"]["items"])

    return df

def get_total_n():
    r1 = st.session_state.session.get('https://eppi.ioe.ac.uk/eppi-vis/ItemList/IndexJSON', cookies={'WebDbErLoginCookie': st.session_state.cookie})
    res = r1.json()

    total_n = res["items"]["totalItemCount"]
    return total_n
