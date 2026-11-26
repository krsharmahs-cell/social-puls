"""SocialPulse dashboard.  Run:  streamlit run dashboard.py"""
import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DATA = "Data" if os.path.isdir("Data") else "data"
PAL = ["#6C8CFF", "#FF7A90", "#35D0BA", "#FFC857", "#B388FF", "#4DD0E1", "#FF9F6B", "#9CCC65", "#F06292"]

st.set_page_config(page_title="SocialPulse", page_icon="📡", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1250px;}
.hero {padding: 1.6rem 1.8rem; border-radius: 18px; margin-bottom: 1.2rem;
  background: linear-gradient(120deg, #1d2a5b 0%, #3b2a6b 55%, #5b2a56 100%);}
.hero h1 {margin: 0; font-size: 2.3rem; color: #fff;}
.hero p {margin: .3rem 0 0; color: #d6d9f5; font-size: 1.02rem;}
div[data-testid="stMetric"] {background: #161a2b; border: 1px solid #2a3050; border-radius: 14px;
  padding: .9rem 1.1rem;}
div[data-testid="stMetricValue"] {font-size: 1.8rem;}
button[data-baseweb="tab"] {font-size: 1rem; padding: .6rem 1rem;}
.note {background:#161a2b; border-left: 4px solid #6C8CFF; padding: .8rem 1rem; border-radius: 8px;
  color:#c9cde8; margin: .5rem 0 1rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load(name, **kw):
    path = os.path.join(DATA, name)
    if not os.path.exists(path) or os.path.getsize(path) < 5:
        return None
    return pd.read_csv(path, **kw)


def style(fig, h=420):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=h,
                      margin=dict(l=10, r=10, t=45, b=10), colorway=PAL)
    return fig


def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


topics = load("topic_info.csv")
share = load("community_topic_share.csv", index_col=0)
summary = load("community_topic_summary.csv")
users = load("user_summary.csv")
posts = load("posts_with_topics.csv", usecols=["created_at", "seed_domain", "topic_reduced", "topic_name"])
ucomm = load("user_communities.csv")
prof = load("author_profiles.csv")

if topics is None:
    st.error("Run notebook 02 first: topic_info.csv is missing.")
    st.stop()

label = {int(r.Topic): f"T{r.Topic}: " + " ".join(str(r.Name).split("_")[1:4]) for r in topics.itertuples()}

st.markdown('<div class="hero"><h1>📡 SocialPulse</h1>'
            '<p>What online communities talk about, and how they are connected. '
            'Topic modeling + follower-network communities on Bluesky.</p></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar
p = None
if posts is not None:
    p = posts[posts["topic_reduced"] != -1].copy()
    p["domain"] = p["seed_domain"].str.title()
    opts = sorted(p["domain"].unique())
    with st.sidebar:
        st.header("Filters")
        chosen = st.multiselect("Domains", opts, default=opts)
        st.caption("Filters apply to the Topics tab. Community views use the whole dataset.")
    p = p[p["domain"].isin(chosen)]

tabs = st.tabs(["Overview", "Topics", "Communities", "Bridges", "Followers", "About"])

# ----------------------------------------------------------------- overview
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Posts analysed", f"{len(p):,}" if p is not None else "n/a")
    c[1].metric("Topics", int((topics["Topic"] != -1).sum()))
    c[2].metric("Domains", p["domain"].nunique() if p is not None else "n/a")
    c[3].metric("Communities", len(share) if share is not None else "n/a")
    c[4].metric("Bridge users", int(users["is_bridge"].sum()) if users is not None else "n/a")

    left, right = st.columns([3, 2])
    if p is not None and len(p):
        top = p["topic_reduced"].value_counts().head(12).index
        d = p[p["topic_reduced"].isin(top)].groupby(["topic_reduced", "domain"]).size().reset_index(name="posts")
        d["topic"] = d["topic_reduced"].map(label)
        fig = px.bar(d, x="posts", y="topic", color="domain", orientation="h", title="Biggest topics by domain")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        left.plotly_chart(style(fig, 460), width="stretch")
        pie = px.pie(p, names="domain", hole=0.6, title="Share of posts by domain")
        right.plotly_chart(style(pie, 460), width="stretch")
    else:
        t = topics[topics["Topic"] != -1].head(12).copy()
        t["topic"] = t["Topic"].map(label)
        left.plotly_chart(style(px.bar(t, x="Count", y="topic", orientation="h", title="Biggest topics"), 460), width="stretch")

# ------------------------------------------------------------------- topics
with tabs[1]:
    if p is None or not len(p):
        st.info("posts_with_topics.csv is needed for this tab.")
    else:
        names = {label[t]: t for t in p["topic_reduced"].value_counts().index if t in label}
        pick = st.multiselect("Compare topics", list(names), default=list(names)[:5])
        q = p[p["topic_reduced"].isin([names[n] for n in pick])].copy()
        q["when"] = pd.to_datetime(q["created_at"], utc=True, errors="coerce")
        q = q.dropna(subset=["when"])
        if len(q):
            span = (q["when"].max() - q["when"].min()).days
            q["period"] = q["when"].dt.tz_localize(None).dt.floor("D" if span < 21 else "W")
            tr = q.groupby(["period", "topic_reduced"]).size().reset_index(name="posts")
            tr["topic"] = tr["topic_reduced"].map(label)
            st.plotly_chart(style(px.line(tr, x="period", y="posts", color="topic", markers=True,
                                          title="Topic volume over time"), 440), width="stretch")
            note("Search returns recent posts, so the time window is short. Read this as descriptive, not a long-term trend.")
        mix = p.groupby(["domain", "topic_reduced"]).size().reset_index(name="posts")
        mix = mix[mix["topic_reduced"].isin(p["topic_reduced"].value_counts().head(15).index)]
        mix["topic"] = mix["topic_reduced"].map(label)
        mix["share"] = mix["posts"] / mix.groupby("topic")["posts"].transform("sum")
        st.plotly_chart(style(px.bar(mix, x="topic", y="share", color="domain",
                                     title="Which domains does each topic come from?"), 420), width="stretch")

# -------------------------------------------------------------- communities
with tabs[2]:
    if share is None or summary is None:
        st.warning("Run notebook 04 (and lower MIN_USERS if it finds no communities) to fill this tab.")
    else:
        note("Each row is a network community (users who follow each other). A brighter cell means "
             "the community spends more of its posts on that topic. Different rows = communities differ by topic.")
        n_max = share.shape[1]
        n = st.slider("Topics to show", min(3, n_max), n_max, min(12, n_max)) if n_max > 3 else n_max
        cols = share.mean().sort_values(ascending=False).head(n).index
        hm = share[cols].copy()
        hm.columns = [label.get(int(c), str(c)) for c in hm.columns]
        hm.index = [f"Community {i}" for i in hm.index]
        fig = px.imshow(hm, aspect="auto", color_continuous_scale="Viridis", labels=dict(color="share"))
        fig.update_xaxes(tickangle=55)
        st.plotly_chart(style(fig, 120 + 48 * len(hm)), width="stretch")

        one = st.selectbox("Inspect a community", list(share.index), format_func=lambda i: f"Community {i}")
        r = share.loc[one].sort_values(ascending=False).head(8)
        d = pd.DataFrame({"topic": [label.get(int(i), str(i)) for i in r.index], "share": r.values})
        fig = px.bar(d, x="share", y="topic", orientation="h", title=f"Community {one}: top topics")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(style(fig, 360), width="stretch")
        st.dataframe(summary, width="stretch", hide_index=True)

# ------------------------------------------------------------------ bridges
with tabs[3]:
    if users is None:
        st.info("user_summary.csv is needed (notebook 04).")
    else:
        note("Bridge users have many follow links into other communities. They are shown by anonymous ID only.")
        g = users.assign(group=np.where(users["is_bridge"], "Bridge", "Other"))
        a, b = st.columns(2)
        a.plotly_chart(style(px.box(g, x="group", y="entropy", color="group",
                                    title="Topic variety (entropy)"), 380), width="stretch")
        b.plotly_chart(style(px.histogram(g, x="n_posts", color="group", nbins=30, barmode="overlay",
                                          title="Posts per user"), 380), width="stretch")
        st.dataframe(users[users["is_bridge"]].sort_values("n_posts", ascending=False).head(25),
                     width="stretch", hide_index=True)
        if os.path.exists("network.png"):
            st.image("network.png", caption="Follower network coloured by community")

# ---------------------------------------------------------------- followers
with tabs[4]:
    if prof is None or ucomm is None:
        st.info("Run the new collect_bluesky.py (it saves author_profiles.csv), then notebooks 01-04, "
                "to see follower counts by community.")
    else:
        m = ucomm.merge(prof, on="author_did", how="inner")
        top_c = m["community"].value_counts().head(8).index
        mm = m[m["community"].isin(top_c)].copy()
        mm["community"] = "C" + mm["community"].astype(str)
        c = st.columns(3)
        c[0].metric("Users with profiles", f"{len(m):,}")
        c[1].metric("Median followers", f"{int(m['followers_count'].median()):,}")
        c[2].metric("Max followers", f"{int(m['followers_count'].max()):,}")
        st.plotly_chart(style(px.box(mm, x="community", y="followers_count", log_y=True,
                                     title="Follower counts by community (log scale)"), 440), width="stretch")
        st.plotly_chart(style(px.scatter(m, x="followers_count", y="degree", log_x=True, opacity=0.5,
                                         color=m["is_bridge"].map({True: "Bridge", False: "Other"}),
                                         title="Audience size vs links inside our network"), 420), width="stretch")
        st.dataframe(m.sort_values("followers_count", ascending=False)
                     [["anon_id", "community", "followers_count", "degree", "is_bridge"]].head(25),
                     width="stretch", hide_index=True)

# -------------------------------------------------------------------- about
with tabs[5]:
    st.markdown("""
**Method**: BERTopic finds topics from post meaning; Louvain finds communities in the follower graph;
NMI against a shuffled baseline tests whether community predicts topic.

**Limitations**
- Posts come from keyword search, so only people discussing those keywords are included.
- Bluesky users are not representative of the general population.
- Following someone does not mean agreeing with them.
- Only aggregated results and anonymous IDs are shown. Raw data is not published.
""")