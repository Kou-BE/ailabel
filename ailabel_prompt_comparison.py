import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# Get random pair
@st.cache
def get_random_pair(data, i):
    title_idx = np.random.choice(data.index.unique())
    title_row = data.iloc[title_idx]
    title = title_row['title']

    version_indices = list(range(6))
    np.random.shuffle(version_indices)
    v1_idx, v2_idx = version_indices[:2]
    v1, v2 = title_row[f'v{v1_idx}'], title_row[f'v{v2_idx}']

    return title, title_idx, v1_idx, v1, v2_idx, v2


def new_results(title_idx, winner, loser):

    # Add the new result
    new_result = pd.DataFrame({
        'title_idx': [title_idx],
        'winner_version': [winner],
        'loser_version': [loser],
    })

    return new_result

@st.cache
def load_data(filename):

    data = pd.read_excel('./input/' + filename, usecols=['title','title_0a','title_0b','title_1a','title_1b','title_2a','title_2b'])
    data.columns = ['title', 'v0', 'v1', 'v2', 'v3', 'v4', 'v5']
    
    return data


################################################################################################################################
# STREAMLIT
################################################################################################################################

# Load data data
data = load_data('prompt_benchmark.xlsx')

# Load the next pair of versions to compare
if "nb_comparison" not in st.session_state:
    st.session_state["nb_comparison"] = 0
title, title_idx, v1_idx, v1, v2_idx, v2 = get_random_pair(data, st.session_state["nb_comparison"])

# Header
response = requests.get('https://www.bearingpointcaribbean.com/wp-content/uploads/2021/02/BrP_Logo_RGBW_NG.png')
img = Image.open(BytesIO(response.content))
st.image(img, width=200)
st.title("AILABEL: GPT Title Benchmark")
st.subheader('Select the best product title between A & B to be used for an e-commerce website.')
st.write("Original Title: " + title)
st.markdown("""---""")
st.write("Version A: " + v1)
st.markdown("""---""")
st.write("Version B: " + v2)
st.markdown("""---""")

# Buttons to select the best version
col1, col2 = st.columns(2)
with col1:
    selected_v1 = st.button(f"Select Version A")
with col2:
    selected_v2 = st.button(f"Select Version B")

# Comparison save
if "results" not in st.session_state:    
    st.session_state["results"] = []

if selected_v1 or selected_v2:

    if selected_v1:
        winner = v1_idx
        loser = v2_idx
    else:
        winner = v2_idx
        loser = v1_idx

    # Append the new results to the list in the session state
    st.session_state["results"].append(new_results(title_idx, winner, loser))

    st.session_state["nb_comparison"] += 1

    title, title_idx, v1_idx, v1, v2_idx, v2 = get_random_pair(data, st.session_state["nb_comparison"])

    st.experimental_rerun()

# Show the results of all comparisons so far
if len(st.session_state["results"]) > 0:
    st.dataframe(pd.concat(st.session_state["results"], ignore_index=True))
    st.write("No comparisons made: " + str(st.session_state["nb_comparison"]))
else:
    st.write("No comparisons have been made yet.")
