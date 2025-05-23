# -*- coding: utf-8 -*-
"""Kopi af Topic_modelling_pipeline.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Ea52kvUIs9od7Uj4cwthLlg719uJmQsB

# **Installing Packages**
"""

from google.colab import drive
drive.mount('/content/drive')

# File path
file_path = "/content/drive/MyDrive/Theses/chunked_df.csv"

!pip install -U numpy

!pip install --upgrade numpy

pip install -U sentence-transformers

!pip install bertopic

!pip install --upgrade bertopic

!pip install bertopic transformers torch

!pip install git+https://github.com/colaberry/ctfidf.git

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np
from bertopic import BERTopic
import torch
from sentence_transformers import SentenceTransformer
import re
import random

# Commented out IPython magic to ensure Python compatibility.
from umap import UMAP
from sklearn.decomposition import PCA
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import hdbscan
from hdbscan import HDBSCAN
# %matplotlib inline

import pickle
from bertopic import BERTopic
from bertopic.dimensionality import BaseDimensionalityReduction
from bertopic.representation import KeyBERTInspired, PartOfSpeech
from bertopic.cluster import BaseCluster
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

"""# **Bertopic**

## **Creating Embeddings**
"""

df = pd.read_csv(file_path)

chunk_texts = df["chunk"].tolist()

sentence_model = SentenceTransformer('AI-Growth-Lab/PatentSBERTa')

# creating embeddings
embeddings = sentence_model.encode(chunk_texts, convert_to_numpy=True, show_progress_bar=True)
assert len(embeddings) == len(df)
df["embedding"] = list(embeddings)

#saving embeddings
np.save('/content/drive/MyDrive/Theses/embedded_chunks', embeddings)
df.to_pickle('/content/drive/MyDrive/Theses/chunked_df_with_embeddings.pkl')

df.info()
df.head()

print(f"Number of unique Application no's: {len(df.ApplicationNumber.unique())}")

"""## **Dimension reduction**"""

embeddings = np.load('/content/drive/MyDrive/Theses/embedded_chunks.npy')

print(embeddings.shape)

df = pickle.load(open('/content/drive/MyDrive/Theses/chunked_df_with_embeddings.pkl', 'rb'))

#rescaling embeddings for convergence issues as best suggested approach
#https://maartengr.github.io/BERTopic/getting_started/tips_and_tricks/tips_and_tricks.html#speed-up-umap
def rescale(x, inplace=False):
    if not inplace:
        x = np.array(x, copy=True)
    x /= np.std(x[:, 0]) * 10000
    return x

#dim reduction using pca
rescaled_embeddings = rescale(embeddings)

# PCA 50 dim
pca_50 = PCA(n_components=50)
pca_embeddings_50 = pca_50.fit_transform(rescaled_embeddings)
with open('pca_model_50.pkl', 'wb') as pca_output_50:
    pickle.dump(pca_50, pca_output_50, protocol=pickle.HIGHEST_PROTOCOL)

# PCA 100 dim
pca_100 = PCA(n_components=100)
pca_embeddings_100 = pca_100.fit_transform(rescaled_embeddings)
with open('pca_model_100.pkl', 'wb') as pca_output_100:
    pickle.dump(pca_100, pca_output_100, protocol=pickle.HIGHEST_PROTOCOL)

# UMAP 50 dim
umap_model_50 = UMAP(n_neighbors=30, n_components=2, min_dist=0.0, metric='cosine')
umap_embeddings_50 = umap_model_50.fit_transform(pca_embeddings_50)

with open("umap_model_50.pkl", "wb") as umap_output_50:
    pickle.dump(umap_model_50, umap_output_50, protocol=pickle.HIGHEST_PROTOCOL)

np.save('/content/drive/MyDrive/Theses/umap_embeddings_50.npy', umap_embeddings_50)

# UMAP 100 dim
umap_model_100 = UMAP(n_neighbors=30, n_components=2, min_dist=0.0, metric='cosine')
umap_embeddings_100 = umap_model_100.fit_transform(pca_embeddings_100)

with open("umap_model_100.pkl", "wb") as umap_output_100:
    pickle.dump(umap_model_100, umap_output_100, protocol=pickle.HIGHEST_PROTOCOL)

np.save('/content/drive/MyDrive/Theses/umap_embeddings_100.npy', umap_embeddings_100)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# UMAP 50 dim
axes[0].scatter(umap_embeddings_50[:, 0], umap_embeddings_50[:, 1], s=1, alpha=0.5)
axes[0].set_title('UMAP Embeddings (50 Dimensions PCA)')
axes[0].set_xlabel('UMAP Dimension 1')
axes[0].set_ylabel('UMAP Dimension 2')

# UMAP 100 dim
axes[1].scatter(umap_embeddings_100[:, 0], umap_embeddings_100[:, 1], s=1, alpha=0.5)
axes[1].set_title('UMAP Embeddings (100 Dimensions PCA)')
axes[1].set_xlabel('UMAP Dimension 1')
axes[1].set_ylabel('UMAP Dimension 2')
plt.tight_layout()
plt.show()

# UMAP 50 dim
umap_model_50_3d = UMAP(n_neighbors=30, n_components=3, min_dist=0.0, metric='cosine')
umap_embeddings_50_3d = umap_model_50_3d.fit_transform(pca_embeddings_50)

with open("umap_model_50_3d.pkl", "wb") as umap_output_50_3d:
    pickle.dump(umap_model_50_3d, umap_output_50_3d, protocol=pickle.HIGHEST_PROTOCOL)

np.save('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy', umap_embeddings_50_3d)

"""## **Clustering** (HDBSCAN)"""

final_umap_embeddings = np.load('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy')
final_umap_embeddings.shape

df = pickle.load(open('/content/drive/MyDrive/Theses/chunked_df_with_embeddings.pkl', 'rb'))
df.info()

df['chunk'] = df['chunk'].astype(str)

df.head()

print(f"Number of rows in dataframe: {df.shape[0]}")
print(f"Number of rows in UMAP embeddings: {final_umap_embeddings.shape[0]}")

hdbscan_model_25 = hdbscan.HDBSCAN(min_cluster_size=25, cluster_selection_method='eom',metric='euclidean',algorithm='best',prediction_data=True)
hdbscan_labels_25 = hdbscan_model_25.fit_predict(final_umap_embeddings)

with open('hdbscan_model_25.pkl', 'wb') as hdbscan_file_25:
    pickle.dump(hdbscan_model_25, hdbscan_file_25, protocol=pickle.HIGHEST_PROTOCOL)

hdbscan_model_60 = hdbscan.HDBSCAN(min_cluster_size=60, cluster_selection_method='eom',metric='euclidean',algorithm='best',prediction_data=True)
hdbscan_labels_60 = hdbscan_model_60.fit_predict(final_umap_embeddings)

with open('hdbscan_model_60.pkl', 'wb') as hdbscan_file_60:
    pickle.dump(hdbscan_model_60, hdbscan_file_60, protocol=pickle.HIGHEST_PROTOCOL)

hdbscan_model_100 = hdbscan.HDBSCAN(min_cluster_size=100, cluster_selection_method='eom',metric='euclidean',algorithm='best',prediction_data=True)
hdbscan_labels_100 = hdbscan_model_100.fit_predict(final_umap_embeddings)

with open('hdbscan_model_100.pkl', 'wb') as hdbscan_file_100:
    pickle.dump(hdbscan_model_100, hdbscan_file_100, protocol=pickle.HIGHEST_PROTOCOL)

df['hdbscan_cluster_25'] = hdbscan_labels_25
df[df['hdbscan_cluster_25'] != -1]
df['hdbscan_cluster_60'] = hdbscan_labels_60
df[df['hdbscan_cluster_60'] != -1]
df['hdbscan_cluster_100'] = hdbscan_labels_100
df[df['hdbscan_cluster_100'] != -1]
df.to_pickle('/content/drive/MyDrive/Theses/df.pkl')

df_loaded = pd.read_pickle('/content/drive/MyDrive/Theses/df.pkl')

df = pd.DataFrame(df)
df.info()

df.head()

# plot hdbscan
def remove_outliers(embeddings, labels):
    mask = labels != -1
    return embeddings[mask], labels[mask]

umap_25, labels_25_no_noise = remove_outliers(final_umap_embeddings, hdbscan_labels_25)
umap_60, labels_60_no_noise = remove_outliers(final_umap_embeddings, hdbscan_labels_60)
umap_100, labels_100_no_noise = remove_outliers(final_umap_embeddings, hdbscan_labels_100)

# subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
plt.suptitle('Clustering on dif min_cluster_size')

axes[0].scatter(umap_25[:, 0], umap_25[:, 1], c=labels_25_no_noise, cmap='Spectral', s=5)
axes[0].set_title('HDBSCAN (min_cluster_size=25)')

axes[1].scatter(umap_60[:, 0], umap_60[:, 1], c=labels_60_no_noise, cmap='Spectral', s=5)
axes[1].set_title('HDBSCAN (min_cluster_size=60)')

axes[2].scatter(umap_100[:, 0], umap_100[:, 1], c=labels_100_no_noise, cmap='Spectral', s=5)
axes[2].set_title('HDBSCAN (min_cluster_size=100)')

for ax in axes:
    ax.set_xlabel('UMAP 1')
    ax.set_ylabel('UMAP 2')

plt.tight_layout()
plt.show()

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def plot_3d(embeddings, labels, title="3D UMAP"):
    mask = labels != -1
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(embeddings[mask, 0], embeddings[mask, 1], embeddings[mask, 2],
               c=labels[mask], cmap='Spectral', s=5)
    ax.set_title(title)
    plt.show()

plot_3d(final_umap_embeddings, hdbscan_labels_100, title="HDBSCAN (min_cluster=100) on 3D UMAP")

from sklearn.metrics import silhouette_score

# calc silhouette core
silhouette_avg_25 = silhouette_score(umap_25, labels_25_no_noise)
print(f"Silhouette Score (min_cluster_size=25): {silhouette_avg_25}")

silhouette_avg_60 = silhouette_score(umap_60, labels_60_no_noise)
print(f"Silhouette Score (min_cluster_size=60): {silhouette_avg_60}")

silhouette_avg_100 = silhouette_score(umap_100, labels_100_no_noise)
print(f"Silhouette Score (min_cluster_size=100): {silhouette_avg_100}")

def plot_cluster_distribution(df, cluster_col, min_cluster_size=15):
    df_no_outliers = df[df[cluster_col] != -1]

    print(f'Number of topics for min_cluster_size={min_cluster_size}: {len(df_no_outliers[cluster_col].unique())}')
    print(f'Amount of noise (outliers): {len(df) - len(df_no_outliers)}')
    print(f'Top cluster size: {df_no_outliers[cluster_col].value_counts().head(1).iloc[0]}')

    top_clusters = df_no_outliers[cluster_col].value_counts().head(20)
    ax = sns.barplot(x=top_clusters.values, y=top_clusters.index, orient='h', order=top_clusters.index)
    ax.set_ylabel('Topic number')
    ax.set_xlabel('Count')
    ax.set_title(f'Top 20 Largest Topics for min_cluster_size={min_cluster_size}')
    plt.rcParams.update({'font.size': 7})
    ax.bar_label(ax.containers[0])
    plt.rcParams.update({'font.size': 10})
    plt.show()

plot_cluster_distribution(df, 'hdbscan_cluster_25', min_cluster_size=25)
plot_cluster_distribution(df, 'hdbscan_cluster_60', min_cluster_size=60)
plot_cluster_distribution(df, 'hdbscan_cluster_100', min_cluster_size=100)

with open('hdbscan_model_100.pkl', 'rb') as inp:
    hdbscan_model = pickle.load(inp)

# df cluster
cluster_df = pd.DataFrame({
    'ApplicationNumber': df['ApplicationNumber'],
    'chunk': df['chunk'],
    'chunk_id': df['chunk_id'],
    'cluster_label': hdbscan_model_100.labels_
})
cluster_df_no_outliers = cluster_df[cluster_df['cluster_label'] != -1]

cluster_labels = cluster_df_no_outliers['cluster_label'].unique()

docu_ls = []
for label in cluster_labels:
    temp_df = cluster_df_no_outliers[cluster_df_no_outliers['cluster_label'] == label]
    document = ''.join(temp_df['chunk'].to_list())
    docu_ls.append(document)

cluster_document_df = pd.DataFrame({'cluster': cluster_labels, 'cluster_document': docu_ls})

print(cluster_document_df.shape)

"""Add custom stopwords"""

Extended_Stopwords = pd.read_csv("/content/drive/MyDrive/Theses/extended_stopwords").to_numpy().flatten().tolist()

count_vectorizer = CountVectorizer(stop_words=Extended_Stopwords, min_df=2, ngram_range=(1, 3)).fit(cluster_document_df.cluster_document)
count = count_vectorizer.transform(cluster_document_df.cluster_document)
words = count_vectorizer.get_feature_names_out() ; print('Vectorizer done')
ctfidf_transformer = ClassTfidfTransformer(reduce_frequent_words=True)
ctfidf_matrix = ctfidf_transformer.fit_transform(count).toarray()
print("c-TF-IDF done")

# top 10 words per cluster
words_per_class = {
    cluster: [words[i] for i in ctfidf_matrix[idx].argsort()[-10:]]
    for idx, cluster in enumerate(cluster_document_df.cluster)
}

# save clus
df_words_per_class = pd.DataFrame.from_dict(words_per_class, orient='index', columns=[f'Word_{i+1}' for i in range(10)])
df_words_per_class.to_csv('/content/drive/MyDrive/Theses/ctfidf_100.csv')

print("Saved top words per cluster to CSV")

df_words_per_class.head()

r_umap_embeddings = np.load('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy')

df = pd.read_pickle('/content/drive/MyDrive/Theses/df.pkl')
df

model_chunks = df['chunk'].astype(str).tolist()
print(len(model_chunks))

"""# Vizualize topics"""

details_df = pd.read_csv('/content/drive/MyDrive/Theses/final_patent_text.csv', usecols=['ApplicationNumber', 'ProbablePatentAssignee', 'Year'])
details_df

df = pd.read_pickle('/content/drive/MyDrive/Theses/df.pkl')
df

df = df.merge(details_df[['ApplicationNumber', 'Year', 'ProbablePatentAssignee']], on='ApplicationNumber', how='left')

df

r_umap_embeddings = np.load('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy')

model_chunks = df['chunk'].astype(str).tolist()

Extended_Stopwords = pd.read_csv("/content/drive/MyDrive/Theses/extended_stopwords").to_numpy().flatten().tolist()

empty_reduction_model = BaseDimensionalityReduction()
empty_cluster_model = BaseCluster()

vectorizer_model = CountVectorizer(
    stop_words=Extended_Stopwords,
    min_df=2,
    ngram_range=(1, 3)
)

ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

keybert_model = KeyBERTInspired()
pos_model = PartOfSpeech("en_core_web_sm")
representation_model = {
    "KeyBERT": keybert_model,
    "POS": pos_model
}

#pipeline
topic_model = BERTopic(
    umap_model=empty_reduction_model,
    hdbscan_model=empty_cluster_model,
    vectorizer_model=vectorizer_model,
    ctfidf_model=ctfidf_model,
    representation_model=representation_model,
    top_n_words=10,
    verbose=True
)

topics, probabilities = topic_model.fit_transform(model_chunks,y= df['hdbscan_cluster_100'])

topic_model.fit_transform

topic_model.visualize_topics()

topic_model.get_topic_info()

topic_model = BERTopic.load("/content/drive/MyDrive/Theses/BERT_v1")

df_info = topic_model.get_document_info(model_chunks)

df_info['ApplicationNumber'] = df['ApplicationNumber'].values

df_info['Year'] = df['Year'].values

df_info['ProbablePatentAssignee'] = df['ProbablePatentAssignee'].values

df_info

df.to_csv("/content/drive/MyDrive/Theses/topic_df.csv", index=False)

topic_model.get_topic(1, full=True)

# diversity
top_n = 10
topics_words = [
    [word for word, _ in topic_model.get_topic(topic)[:top_n]]
    for topic in topic_model.get_topics() if topic_model.get_topic(topic)
]

all_words = [word for topic in topics_words for word in topic]
unique_words = set(all_words)

diversity = len(unique_words) / len(all_words)
print(f"Topic Diversity: {diversity:.4f}")

from itertools import combinations

df_words_per_class = pd.read_csv('/content/drive/MyDrive/Theses/ctfidf_100.csv', index_col=0)
topic_words = df_words_per_class.values.tolist()
documents = cluster_document_df.cluster_document.tolist()

# manual coherence fnc
def manual_coherence_score_for_topic(topic_words, documents):
    topic_coherence_scores = []
    total_docs = len(documents)

    for topic in topic_words:
        word_pairs = list(combinations(topic, 2))
        pair_scores = []

        for w1, w2 in word_pairs:
            count = sum(1 for doc in documents if w1 in doc and w2 in doc)
            normalized_score = count / total_docs
            pair_scores.append(normalized_score)

        topic_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0
        topic_coherence_scores.append(topic_score)

    return topic_coherence_scores

#individual coherence
topic_scores = manual_coherence_score_for_topic(topic_words, documents)
normalized_topic_scores = [min(1, max(0, score)) for score in topic_scores]

# avg coherence
overall_coherence = sum(normalized_topic_scores) / len(normalized_topic_scores) if normalized_topic_scores else 0

#print coherence
for i, score in enumerate(normalized_topic_scores):
    print(f"Topic {i+1} Normalized Coherence Score = {score:.4f}")

print(f"Overall Normalized Coherence Score = {overall_coherence:.4f}")

df_words_per_class = pd.read_csv('/content/drive/MyDrive/Theses/ctfidf_100.csv', index_col=0)
df_words_per_class.head()

hierachy_fig = topic_model.visualize_hierarchy()
hierachy_fig.write_html("/content/drive/MyDrive/Theses/hierachy.html")

hierachy_fig

distance_map = topic_model.visualize_topics()
distance_map.write_html("/content/drive/MyDrive/Theses/topics.html")

distance_map

barchart = topic_model.visualize_barchart()
barchart.write_html("/content/drive/MyDrive/Theses/barchart.html")

barchart

topic_model.save('/content/drive/MyDrive/Theses/BERT')

"""## LLM Representation"""

!pip install -U bitsandbytes

!pip install accelerate xformers adjustText

!pip install bertopic

import pandas as pd
import numpy as np
from bertopic import BERTopic
import torch
from bertopic.dimensionality import BaseDimensionalityReduction
from bertopic.representation import KeyBERTInspired, TextGeneration
from bertopic.cluster import BaseCluster
import re
import random
import pickle
from torch import bfloat16
import transformers
from torch import cuda
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

from huggingface_hub import notebook_login
notebook_login()

model_id = 'meta-llama/Llama-2-7b-chat-hf'
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

print(device)

bnb_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=bfloat16
)

#llama2 model
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    quantization_config=bnb_config,
    device_map='auto',
)
model.eval()

generator = transformers.pipeline(
    model=model, tokenizer=tokenizer,
    task='text-generation',
    temperature=0.1,
    max_new_tokens=500,
    repetition_penalty=1.1
)

#llama2 system prompt
system_prompt = """
<s>[INST] <<SYS>>
You are a helpful, truthful and honest patent analysis assistant that generates short, meaningful topic labels based on keywords or representative documents. Your labels are concise (2–5 words), human-readable, and summarize the theme of the topic. If the topic is unclear, don't just say something, use a generic label like "Miscellaneous".

<</SYS>>
"""

example_prompt = """
I have a topic that contains the following documents:
- A surgical robotic system that includes a precisely controlled robotic arm for performing delicate operations with high accuracy and minimal patient intervention.
- A system for controlling the position of the second robotic arm to assist in complex surgical procedures, providing enhanced precision.
- A robotic surgical system featuring a dual-arm configuration for multi-tasking in surgery, with an advanced control mechanism to optimize surgical outcomes.

The topic is described by these keywords: 'robotic arm, surgical robotic system, position control, robotic surgical system, multi-arm, control mechanism, precision'.

Based on the information about the topic above, please create a short label of this topic. Make sure you to only return the label and nothing more.

[/INST] Robotic arm systems for precise surgical control
"""

main_prompt = """
[INST]
I have a topic that contains the following documents:
[DOCUMENTS]

The topic is described by these keywords: '[KEYWORDS]'.

Based on the information about the topic above, please create a short label of this topic. Make sure you to only return the label and nothing more.
[/INST]
"""

prompt = system_prompt + example_prompt + main_prompt

df = pd.read_pickle('/content/drive/MyDrive/Theses/df.pkl')
df

model_chunks = df['chunk'].astype(str).tolist()

Extended_Stopwords = pd.read_csv("/content/drive/MyDrive/Theses/extended_stopwords").to_numpy().flatten().tolist()

empty_reduction_model = BaseDimensionalityReduction()
empty_cluster_model = BaseCluster()

vectorizer_model = CountVectorizer(
    stop_words=Extended_Stopwords,
    min_df=2,
    ngram_range=(1, 3)
)

ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

keybert_model = KeyBERTInspired()
llama2 = TextGeneration(generator, prompt=prompt)
representation_model = {
    "KeyBERT": keybert_model,
    "Llama2": llama2,
}

#pipeline
topic_model2 = BERTopic(
    umap_model=empty_reduction_model,
    hdbscan_model=empty_cluster_model,
    vectorizer_model=vectorizer_model,
    ctfidf_model=ctfidf_model,
    representation_model=representation_model,
    top_n_words=10,
    verbose=True
)

topics, probabilities = topic_model2.fit_transform(model_chunks,y= df['hdbscan_cluster_100'])

topic_model2.fit_transform

topic_model2.visualize_topics()

topic_model2.get_topic_info()

#topic_model2.save('/content/drive/MyDrive/Theses/BERTv2')

llama2_labels = [label[0][0].split("\n")[0] for label in topic_model2.get_topics(full=True)["Llama2"].values()]
topic_model2.set_topic_labels(llama2_labels)

r_umap_embeddings = np.load('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy')

doctopic_map = topic_model2.visualize_documents(model_chunks, reduced_embeddings=r_umap_embeddings, custom_labels=True, hide_annotations=True)
doctopic_map.write_html("/content/drive/MyDrive/Theses/doctopic_map.html")

doctopic_map

hierachy_fig2 = topic_model2.visualize_hierarchy(custom_labels=True)
hierachy_fig2.write_html("/content/drive/MyDrive/Theses/hierachy2.html")

hierachy_fig2

distance_map2 = topic_model2.visualize_topics(custom_labels=True)
distance_map2.write_html("/content/drive/MyDrive/Theses/topics2.html")

distance_map2

r_umap_embeddings = np.load('/content/drive/MyDrive/Theses/umap_embeddings_50_3d.npy')

topic_model2.visualize_documents(titles, reduced_embeddings=r_umap_embeddings, hide_annotations=True, hide_document_hover=False, custom_labels=True)

details_df = pd.read_csv('/content/drive/MyDrive/Theses/final_patent_text.csv', usecols=['ApplicationNumber', 'ProbablePatentAssignee', 'Year'])
details_df

df = df.merge(details_df[['ApplicationNumber', 'Year', 'ProbablePatentAssignee']], on='ApplicationNumber', how='left')

final_topic_df = topic_model2.get_document_info(model_chunks)

final_topic_df['ApplicationNumber'] = df['ApplicationNumber'].values

final_topic_df['Year'] = df['Year'].values

final_topic_df['ProbablePatentAssignee'] = df['ProbablePatentAssignee'].values

final_topic_df

final_topic_df.to_csv("/content/drive/MyDrive/Theses/final_topic2_df.csv", index=False)

#new prompts
system_prompt = """
<s>[INST] <<SYS>>
You are a helpful, truthful and honest patent analysis assistant that summarize the topics a ProbablePatentAssignee has. You are an expert in analyzing patent topics for medical devices, especially in the field of endoscopy. Your goal is to interpret the topics generated from patents and identify what types of products or innovations the companies are working on.
This should be in a concise and human-readable language. If it is unclear, don't just say something, but say something like "Miscellaneous".
<</SYS>>
"""

example_prompt = """
I have a list of patent topics for a single Company:
1. Imaging system with enhanced resolution for internal organ visualization.
2. Robotic system for performing minimally invasive surgeries with precise control.
3. Endoscopic device with integrated AI for detecting anomalies during procedures.
4.rhinolaryngoscope

Based on these topics, please identify what type of product or innovation the assignee is likely developing. Provide a concise and human-readable description.
Make sure you to only return a short precise summarization of topics and analysis.
[/INST] Rhinolaryngoscope with assisted AI system
"""

main_prompt = """
[INST]
I have a [ProbablePatentAssignee] with the following patent topics:
[Llama2]
[Llama2]

Based on these topics, please identify what type of product, products or innovation the assignee is likely developing. Provide a concise and human-readable description.
Make sure you to only return a short precise summarization of topics and analysis.
[/INST]
"""

prompt = system_prompt + example_prompt + main_prompt

final_topic_df = pd.read_csv("/content/drive/MyDrive/Theses/final_topic2_df.csv")

company = "OLYMPUS CORP"

filtered_df = final_topic_df[final_topic_df["ProbablePatentAssignee"] == company]
topic_summary = (
    filtered_df
    .groupby(["ProbablePatentAssignee", "Topic"])
    .agg({
        "Llama2": "first",
        "Top_n_words": "first",
        "ApplicationNumber": "nunique"
    })
    .rename(columns={"ApplicationNumber": "ApplicationNoCount"})
    .reset_index()
)
#prompts
prompt_parts = [f"### Company: {company}\n"]
for _, row in topic_summary.iterrows():
    prompt_parts.append(
        f"Topic {row['Topic']} ({row['ApplicationNoCount']} chunks): {row['Llama2']}\n"
        f"Keywords: {row['Top_n_words']}\n"
    )

main_prompt = "\n".join(prompt_parts)

final_prompt = f"""
Company: {company}
Based on the following patent topics, please summarize the type of product(s) or innovation the company is likely developing. Provide a concise, human-readable description that connects these topics to potential products or technological areas.

{main_prompt}

Summarize the above into a concise and human-readable description of the company’s products or innovations, focusing on the connection between the topics and the company's technology.
"""

response = generator(final_prompt, max_length=500, temperature=0.7, top_p=0.9)[0]['generated_text']
print(f"Analysis for {company}:\n{response}")

company = "AMBU A S"

filtered_df = final_topic_df[final_topic_df["ProbablePatentAssignee"] == company]
topic_summary = (
    filtered_df
    .groupby(["ProbablePatentAssignee", "Topic"])
    .agg({
        "Llama2": "first",
        "Top_n_words": "first",
        "ApplicationNumber": "nunique"
    })
    .rename(columns={"ApplicationNumber": "ApplicationNoCount"})
    .reset_index()
)
#prompts
prompt_parts = [f"### Company: {company}\n"]
for _, row in topic_summary.iterrows():
    prompt_parts.append(
        f"Topic {row['Topic']} ({row['ApplicationNoCount']} chunks): {row['Llama2']}\n"
        f"Keywords: {row['Top_n_words']}\n"
    )

main_prompt = "\n".join(prompt_parts)

final_prompt = f"""
Company: {company}
Based on the following patent topics, please summarize the type of product(s) or innovation the company is likely developing. Provide a concise, human-readable description that connects these topics to potential products or technological areas.

{main_prompt}

Summarize the above into a concise and human-readable description of the company’s products or innovations, focusing on the connection between the topics and the company's technology.
"""

response = generator(final_prompt, max_length=500, temperature=0.7, top_p=0.9)[0]['generated_text']
print(f"Analysis for {company}:\n{response}")

company = "CILAG GMBH INT"

filtered_df = final_topic_df[final_topic_df["ProbablePatentAssignee"] == company]
topic_summary = (
    filtered_df
    .groupby(["ProbablePatentAssignee", "Topic"])
    .agg({
        "Llama2": "first",
        "Top_n_words": "first",
        "ApplicationNumber": "nunique"
    })
    .rename(columns={"ApplicationNumber": "ApplicationNoCount"})
    .reset_index()
)
#prompts
prompt_parts = [f"### Company: {company}\n"]
for _, row in topic_summary.iterrows():
    prompt_parts.append(
        f"Topic {row['Topic']} ({row['ApplicationNoCount']} chunks): {row['Llama2']}\n"
        f"Keywords: {row['Top_n_words']}\n"
    )

main_prompt = "\n".join(prompt_parts)

final_prompt = f"""
Company: {company}
Based on the following patent topics, please summarize the type of product(s) or innovation the company is likely developing. Provide a concise, human-readable description that connects these topics to potential products or technological areas.

{main_prompt}

Summarize the above into a concise and human-readable description of the company’s products or innovations, focusing on the connection between the topics and the company's technology.
"""

response = generator(final_prompt, max_length=500, temperature=0.7, top_p=0.9)[0]['generated_text']
print(f"Analysis for {company}:\n{response}")

company = "CILAG GMBH INT"

filtered_df = final_topic_df[final_topic_df["ProbablePatentAssignee"] == company]
topic_summary = (
    filtered_df
    .groupby(["ProbablePatentAssignee", "Topic"])
    .agg({
        "Llama2": "first",
        "Top_n_words": "first",
        "ApplicationNumber": "nunique"
    })
    .rename(columns={"ApplicationNumber": "ApplicationNoCount"})
    .reset_index()
)
#prompts
prompt_parts = [f"### Company: {company}\n"]
for _, row in topic_summary.iterrows():
    prompt_parts.append(
        f"Topic {row['Topic']} ({row['ApplicationNoCount']} chunks): {row['Llama2']}\n"
        f"Keywords: {row['Top_n_words']}\n"
    )

main_prompt = "\n".join(prompt_parts)

final_prompt = f"""
Company: {company}
Based on the following patent topics, please summarize the type of product(s) or innovation the company is likely developing. Provide a concise, human-readable description that connects these topics to potential products or technological areas.

{main_prompt}

Summarize the above into a concise and human-readable description of the company’s products or innovations, focusing on the connection between the topics and the company's technology.
"""

response = generator(final_prompt, max_length=500, temperature=0.7, top_p=0.9)[0]['generated_text']
print(f"Analysis for {company}:\n{response}")
