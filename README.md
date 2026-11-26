# SocialPulse: Social Media Topic & Community Clustering

> Understanding an online community requires seeing beyond individual posts to the underlying **topics** and **follower-network structure**, which is not visible from raw feeds alone.

**Authors:** Keshav Sharma, Chodisiti Nithya, Shiv Shankar
**Programme:** B.Tech, Computer Science and Engineering, Lovely Professional University, Phagwara, Punjab, India
**Data source:** Bluesky (AT Protocol), public posts and follow relationships
**Language / tools:** Python, Jupyter, BERTopic, NetworkX, Streamlit

---

## 1. The Problem

A social media feed is a stream of posts, one after another. Scrolling through it does not tell you:

- what the main **topics** of discussion are,
- which **groups of people** exist,
- how those groups are **connected** to each other.

Two kinds of structure are hidden behind the feed:

| Hidden structure | Question it answers | Data it comes from |
|---|---|---|
| **Content structure** | What are people talking about? | Post text |
| **Network structure** | Who is connected to whom? | Follow relationships |

Each view alone is incomplete. Topics do not say who forms a group, and a network does not say what a group talks about.

## 2. The Idea

SocialPulse looks at the same community in **two ways and then joins them**.

Think of a college canteen:

- the **topics** are the subjects being discussed (cricket, exams, AI),
- the **communities** are the friend groups sitting at the tables,
- **SocialPulse tells you which table talks about what, and who moves between tables.**

## 3. Objectives and Research Questions

**Objectives**

1. Build a clean, documented dataset of public Bluesky discussions.
2. Discover topics automatically, without labels (unsupervised learning).
3. Discover user communities from the follower network.
4. Measure how strongly topics and communities are related, with a significance test.
5. Present the findings in an interactive dashboard that protects user privacy.

**Research questions**

- **RQ1:** What topics emerge across the nine domains, and are they separated or mixed between domains?
- **RQ2:** Does the follower network split into stable communities?
- **RQ3:** Do communities differ in the topics they discuss, and do bridge users discuss a wider range of topics?

## 4. Dataset

| Item | Value |
|---|---|
| Platform | Bluesky, via the official API |
| Domains | 9 (technology, politics, sports, entertainment, health, climate, finance, science, education) |
| Search keywords | 45 (five per domain) |
| Posts requested per keyword | up to 500, English only |
| Unique posts collected | **25,620** |
| Unique authors | **16,355** |
| Extra data | author profile statistics (follower count) and follow lists of the most active authors (up to 1,000 follows per user) |

**Keywords by domain**

| Domain | Keywords |
|---|---|
| Technology | artificial intelligence, openai, open source, cybersecurity, semiconductor |
| Politics | election, parliament, policy, senate, democracy |
| Sports | cricket, football, premier league, olympics, nba |
| Entertainment | movie, netflix, music, anime, gaming |
| Health | mental health, vaccine, fitness, healthcare, nutrition |
| Climate | climate change, renewable energy, electric vehicle, wildfire, sustainability |
| Finance | inflation, stock market, bitcoin, interest rates, economy |
| Science | nasa, space, physics, biology, research |
| Education | university, students, exam, scholarship, teaching |

The project started with technology and politics and was then widened to nine domains and more users to get a richer dataset and more varied topics.

## 5. How It Works: The Pipeline

```
Collect  ->  Clean  ->  +-- Topic modeling (what) --+  ->  Link & evaluate  ->  Dashboard
                        +-- Network analysis (who) -+
```

### Step 1: Collect
A Python script downloads posts, author profiles and follow lists. It pauses between requests, skips accounts that cannot be read (deleted or restricted), and saves progress while building the follow graph so an interrupted run can be resumed.

### Step 2: Clean
- Remove missing values and duplicate posts.
- Strip links, @mentions and hashtag symbols (the hashtag word is kept).
- Remove posts shorter than 5 words, posts with more than 5 hashtags, and repeated texts.
- Keep at most 50 posts per author, so no single account dominates a topic.
- Keep follow edges only when both users are retained authors.

### Step 3: Topic modeling (the "what")
1. Each post is converted into a 384-number vector (a **sentence embedding**) that captures its meaning, using the `all-MiniLM-L6-v2` model.
2. **UMAP** compresses the vectors to 5 dimensions.
3. **HDBSCAN** finds dense clusters. Each cluster is a topic. Posts that fit nowhere are outliers.
4. **c-TF-IDF** picks the words that best describe each topic.
5. Outliers are reassigned to their nearest topic so every user has a topic profile.

The tool that combines these steps is **BERTopic**.

### Step 4: Network and communities (the "who")
- Each user is a **node** and each follow is an **edge**.
- The **Louvain algorithm** groups users who are more connected to each other than to outsiders. Each group is a **community**.
- **Bridge users** are users with at least 40% of their links in other communities and at least 5 connections.

### Step 5: Link the two views (the key step)
Every post gets the community of its author. Then we compute:

- the **share of each community's posts** in each topic (heatmap),
- the **lift** of each topic in each community (which topics are distinctive),
- each user's **dominant topic** and its agreement with their community (NMI),
- each user's **topic entropy** (how varied their topics are).

### Step 6: Dashboard
A Streamlit dashboard shows everything in tabs, using anonymous IDs only.

## 6. Measurements Explained Simply

| Measure | What it tells you |
|---|---|
| **Coherence (c_v)** | Whether the top words of a topic make sense together |
| **Topic diversity** | Whether topics use different words from each other |
| **Modularity** | How clearly the network splits into communities. About 0.3 to 0.7 usually means clear communities |
| **Stability** | Whether Louvain finds the same groups across 10 random seeds (measured by NMI) |
| **Lift** | How much more a community discusses a topic than the average. Lift 3 means three times more |
| **NMI** | How closely communities match dominant topics. 0 is unrelated, 1 is identical |
| **Shuffled baseline** | NMI after randomly shuffling community labels 200 times. The real NMI must clearly beat it, or the match is luck |
| **Permutation p-value** | The share of shuffled runs that did as well as the real one. Small means significant |
| **Topic entropy** | How spread out a user's posts are across topics |
| **Mann-Whitney test** | Compares bridge users with other users without assuming a normal distribution |

## 7. Outputs

- Topic table with size and top words of each topic.
- Follower network drawn with users coloured by community (`network.png`).
- Community by topic heatmap (`heatmap.png`).
- Bridge-user analysis (topic variety and over-represented topics).
- Follower counts by community.
- Interactive dashboard with six tabs: Overview, Topics, Communities, Bridges, Followers, About.

## 8. Results

> Add your final numbers here after the full run: number of topics, coherence, number of communities, modularity, stability, NMI against the shuffled baseline, and the number of bridge users. Then add two or three sentences on what they show.

## 9. Technology Stack

| Purpose | Tools |
|---|---|
| Data collection | Python, `atproto` (Bluesky API) |
| Data handling | pandas, NumPy |
| Topic modeling | Sentence-Transformers, BERTopic, UMAP, HDBSCAN, gensim |
| Network analysis | NetworkX, scikit-learn, SciPy |
| Visualisation | Matplotlib, Plotly |
| Dashboard | Streamlit |
| Workflow | Jupyter notebooks, Git and GitHub |

## 10. Project Structure

```
Social-Pulse/
├── collect_bluesky_v2.py          collect posts, profiles and follows
├── run_graph_only.py              resumable follow-graph collection
├── 01_cleaning.ipynb              clean posts and edges
├── 02_topic_modeling.ipynb        BERTopic topics and evaluation
├── 03_network_communities.ipynb   graph, Louvain, stability, bridge users
├── 04_combine_and_visualize.ipynb heatmap, lift, NMI, entropy, tables
├── dashboard.py                   Streamlit dashboard
├── README.md
└── Data/                          generated files (not committed)
```

Each notebook reads the previous stage's output and writes its own, so any stage can be rerun alone.

## 11. How to Run

```bash
git clone https://github.com/krsharmahs-cell/Social-Pulse.git
cd Social-Pulse
python -m venv venv
source venv/bin/activate
pip install atproto pandas python-dotenv bertopic sentence-transformers gensim \
            networkx scikit-learn scipy matplotlib plotly streamlit nbformat ipython
```

Create a `.env` file (never commit it) with a Bluesky **app password**:

```
BSKY_HANDLE=your-handle.bsky.social
BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

Then:

1. `python collect_bluesky_v2.py`, then `python run_graph_only.py` if the follow stage needs resuming.
2. Run notebooks `01` to `04` in order.
3. `streamlit run dashboard.py`

## 12. Limitations

- Posts come from keyword search, so only people discussing those keywords are included.
- Bluesky users are not representative of the general population, especially for political content.
- Following someone does not mean agreeing with them.
- A user's dominant topic simplifies someone who posts about many subjects.
- Results depend on settings such as the minimum topic size and the Louvain resolution.
- The follow graph covers only the most active authors, not every author.
- Search returns recent posts, so the time window is short and no long-term trends are claimed.

## 13. Ethics and Privacy

- Only public posts collected through the official API are used.
- Credentials are kept in a local `.env` file that is not committed.
- Users appear only as anonymous IDs in outputs and the dashboard.
- Raw data is not published in this repository.

## 14. Future Work

- Use mutual-follow graphs for a stricter definition of connection.
- Compare with a second platform to reduce platform bias.
- Add multilingual embeddings to include non-English posts.
- Collect over several months to track how topics and communities change.
- Repeat community detection with the Leiden algorithm to check robustness.

## 15. References

1. D. M. Blei, A. Y. Ng, M. I. Jordan, "Latent Dirichlet allocation," *JMLR*, 2003.
2. M. Grootendorst, "BERTopic: Neural topic modeling with a class-based TF-IDF procedure," arXiv:2203.05794, 2022.
3. N. Reimers, I. Gurevych, "Sentence-BERT," *EMNLP-IJCNLP*, 2019.
4. L. McInnes, J. Healy, J. Melville, "UMAP," arXiv:1802.03426, 2018.
5. R. Campello, D. Moulavi, J. Sander, "Density-based clustering based on hierarchical density estimates," *PAKDD*, 2013.
6. M. E. J. Newman, "Modularity and community structure in networks," *PNAS*, 2006.
7. V. Blondel et al., "Fast unfolding of communities in large networks," *J. Stat. Mech.*, 2008.
8. M. Kleppmann et al., "Bluesky and the AT Protocol: Usable decentralized social media," arXiv:2402.03239, 2024.
9. M. Röder, A. Both, A. Hinneburg, "Exploring the space of topic coherence measures," *WSDM*, 2015.
10. A. Strehl, J. Ghosh, "Cluster ensembles," *JMLR*, 2002.

---

## Suggested Slide Outline (for presentation tools)

1. **Title:** SocialPulse and the three authors
2. **The problem:** a feed hides topics and groups
3. **The idea:** two views joined, with the canteen analogy
4. **Objectives and research questions**
5. **Dataset:** 9 domains, 45 keywords, 25,620 posts, 16,355 authors
6. **Pipeline overview:** collect, clean, topics and network, link, dashboard
7. **Cleaning:** what was removed and why
8. **Topic modeling:** embeddings, UMAP, HDBSCAN, c-TF-IDF
9. **Network and communities:** Louvain, modularity, bridge users
10. **Linking the views:** heatmap, lift, NMI against a shuffled baseline
11. **Measurements explained simply**
12. **Dashboard:** the six tabs
13. **Results:** final numbers and key findings
14. **Limitations and ethics**
15. **Future work and conclusion**
16. **References and thank you**
