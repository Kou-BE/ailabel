import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime


# Get random pair
@st.cache
def get_random_pair(data, i):
    title_idx = np.random.choice(data.index.unique())
    title_row = data.iloc[title_idx]
    images = title_row['images']

    version_indices = list(range(6))
    np.random.shuffle(version_indices)
    v1_idx, v2_idx = version_indices[:2]
    v1, v2 = title_row[f'v{v1_idx}'], title_row[f'v{v2_idx}']

    return title_idx, v1_idx, v1, v2_idx, v2, images


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

    data = pd.read_excel('./input/' + filename, usecols=['title','title_0a','title_0b','title_1a','title_1b','title_2b','image'])
    data.columns = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'images']

    data['images'] = data['images'].map(lambda x: clean_img_url(x))
    
    return data

def clean_img_url(x_str):
    if x_str == '[]':
        return np.nan
    else:
        x_list = x_str.split(', ')
        x_list = [x.strip("'").strip('[').strip(']').strip("'") for x in x_list]
        x_list += [""]*5
        return x_list[:6]

def display_product_images():

    if len(images)==0:
        st.write('No image available')

    else:
        col0, col1, col2, col3, col4, col5 = st.columns(6)
        with col0:
            get_img(images[0])
        with col1:
            get_img(images[1])
        with col2:
            get_img(images[2])
        with col3:
            get_img(images[3])
        with col4:
            get_img(images[4])
        with col5:
            get_img(images[5])

def get_img(url):
    if len(url)==0:
        a = 0
    else:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        st.image(img)

def push_results_to_repo():
    
    # Create filename with datetime and random set of numbers
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    rand_num = str(np.random.randint(1000, 9999))
    filename = f'{now}_{rand_num}.csv'
    filepath = './output/' + filename
    
    # Save results DataFrame to CSV file
    results = st.session_state["results"]
    results.to_csv(filepath, index=False)
    
    # Read CSV contents from file
    with open(filepath, 'r') as f:
        file_list = f.read()
    
    # Repo info
    repo = st.secrets["repository"]
    branch = st.secrets["branch"]
    token = st.secrets["token"]
    
    # Push
    updategitfiles(filepath, file_list, repo, branch, token)


def updategitfiles(filepath,file_list,repo,branch,token):

    g = Github(token)
    repo = g.get_user().get_repo(repo)
    repo.create_file(filepath, "committing files", file_list, branch=branch)
    time.sleep(3)

################################################################################################################################
# STREAMLIT
################################################################################################################################

# Load data data
data = load_data('prompt_benchmark.xlsx')

# Load the next pair of versions to compare
if "nb_comparison" not in st.session_state:
    st.session_state["nb_comparison"] = 0
title_idx, v1_idx, v1, v2_idx, v2, images = get_random_pair(data, st.session_state["nb_comparison"])

# Header
response = requests.get('https://www.bearingpointcaribbean.com/wp-content/uploads/2021/02/BrP_Logo_RGBW_NG.png')
img = Image.open(BytesIO(response.content))
st.image(img, width=200)
st.title("AILABEL: GPT Title Benchmark")
st.subheader('Select the best product title between A & B for an e-commerce website.')
st.subheader(f'Product Number {title_idx}')
display_product_images()
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

    title_idx, v1_idx, v1, v2_idx, v2, images = get_random_pair(data, st.session_state["nb_comparison"])

    st.experimental_rerun()

# Show the results of all comparisons so far
if len(st.session_state["results"]) > 0:
    st.dataframe(pd.concat(st.session_state["results"], ignore_index=True))
    st.write("No comparisons made: " + str(st.session_state["nb_comparison"]))
else:
    st.write("No comparisons have been made yet.")
    
# Button to save results
if st.button('Push results'):
    if len(st.session_state["results"]) > 0:
        push_results_to_repo()
        st.success('Thanks!')
    else:
        st.write("Please make at least one comparison before pushing -_-'")
        bruh = requests.get('http://i.imgur.com/2CkPjd2.png')
        bruh_img = Image.open(BytesIO(bruh.content))
        st.image(bruh_img, width=200)
