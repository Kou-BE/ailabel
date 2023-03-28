import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime
from github import Github
import time
import os


# Get random pair
@st.cache
def get_random_pair(data, i, session_nb):
    title_idx = np.random.randint(0,99)
    title_row = data.iloc[title_idx]
    images = title_row['images']

    version_indices = list(range(6))
    np.random.shuffle(version_indices)
    v1_idx, v2_idx = version_indices[:2]
    v1, v2 = title_row[f'v{v1_idx}'], title_row[f'v{v2_idx}']

    return title_idx, v1_idx, v1, v2_idx, v2, images


def new_results(title_idx, winner, loser):

    # Add the new result
    new_result = [title_idx, winner, loser]

    return new_result


@st.cache
def load_data(filename):

    data = pd.read_excel('./input/' + filename, usecols=['title','title_0a','title_0b','title_1a','title_1b','title_2b','image'])
    data.columns = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'images']

    data['images'] = data['images'].map(lambda x: clean_img_url(x))
        
    return data


def clean_img_url(x_str):
    if x_str == '[]':
        return ""
    else:
        x_list = x_str.split(', ')
        x_list = [x.strip("'").strip('[').strip(']').strip("'") for x in x_list]
        x_list += [""]*5
        return x_list[:6]


def display_product_images(images):
    if len(images)==0:
        st.write('No image available')
    else:
        cols = st.columns(3)
        for col, img_url in zip(cols, images):
            try:
                response = requests.get(img_url)
                img = Image.open(BytesIO(response.content))
                col.image(img, width=100)
            except:
                pass


def push_to_github(filename, filecontent):
    
    # Get the GitHub token from the Streamlit secrets
    token = st.secrets["github"]["token"]
    _repo = st.secrets["github"]["repository"]
    _branch = st.secrets["github"]["branch"]

    # Create a PyGitHub object with the token
    g = Github(token)

    # Get the repository object
    repo = g.get_repo(f'{_repo}/{_branch}')

    # Create a new Git commit with the file
    repo.create_file(filename, "Add new file", filecontent)
    
    time.sleep(3)


def push_results_to_repo():
    # Get the results dataframe from session state
    results_df = pd.DataFrame(st.session_state['results'], columns=['title_idx', 'winner', 'loser'])
    
    # Convert the dataframe to CSV string
    csv_str = results_df.to_csv(index=False)
    
    # Convert CSV string to bytes
    csv_bytes = BytesIO(csv_str.encode())
    
    # Create filename with datetime and random set of numbers
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    rand_num = str(np.random.randint(1000, 9999))
    filename = f'{now}_{rand_num}.csv'
    
    # Push the file to GitHub
    push_to_github('./output/'+filename, csv_bytes.getvalue())
    
    # Show a success message
    st.success("Results pushed successfully!")     


def display_main_header():
    response = requests.get('https://www.bearingpointcaribbean.com/wp-content/uploads/2021/02/BrP_Logo_RGBW_NG.png')
    img = Image.open(BytesIO(response.content))
    st.image(img, width=200)
    st.title("AILABEL: GPT Title Benchmark")
    st.subheader('Select the best product title between A & B for an e-commerce website.')

    
def get_results_stats():
    # Chemin vers le dossier "output"
    folder_path = './output/'

    # Compter le nombre de fichiers CSV dans le dossier
    csv_count = len(os.listdir(folder_path))

    # Compter le nombre total de lignes dans tous les fichiers CSV
    total_rows = 0
    for file in os.listdir(folder_path):
        df = pd.read_csv(os.path.join(folder_path, file))
        total_rows += len(df)

    return csv_count, total_rows


################################################################################################################################
# STREAMLIT
################################################################################################################################


# Load data data
data = load_data('prompt_benchmark.xlsx')


# Load the next pair of versions to compare
if "nb_comparison" not in st.session_state:
    st.session_state["nb_comparison"] = 0
if "session_nb" not in st.session_state:
    st.session_state["session_nb"] = np.random.rand()
title_idx, v1_idx, v1, v2_idx, v2, images = get_random_pair(data, st.session_state['nb_comparison'],st.session_state["session_nb"])


# Header
display_main_header()
st.subheader(f'Product Number {title_idx}')
display_product_images(images)
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

    title_idx, v1_idx, v1, v2_idx, v2, images = get_random_pair(data, st.session_state['nb_comparison'],st.session_state["session_nb"])

    st.experimental_rerun()


# Show the results of all comparisons so far
if len(st.session_state["results"]) > 0:
    st.write("No comparisons not pushed yet: " + str(len(st.session_state['results'])))
    #st.dataframe(pd.DataFrame(st.session_state['results'], columns=['title_idx', 'winner', 'loser']))
else:
    st.write("No comparisons have been made yet.")


# Button to save results
if st.button('Push results'):
    if len(st.session_state["results"]) > 0:
        push_results_to_repo()
        st.session_state["results"] = []
    else:
        st.write("Please make at least one comparison before pushing -_-'")
        bruh = requests.get('http://i.imgur.com/2CkPjd2.png')
        bruh_img = Image.open(BytesIO(bruh.content))
        st.image(bruh_img, width=200)

# Stats
with st.expander("Ongoing progress"):    
    if st.button('Print stats'):
        csv_count, total_rows = get_results_stats()
        st.write(f'Nb de session de comparaisons : {csv_count}. Nb de comparaisons : {total_rows}')
