"""Collect posts, author follower counts and the follow graph from Bluesky.
Credentials come from .env (BSKY_HANDLE, BSKY_APP_PASSWORD). Output goes to Data/."""
import os
import time
import pandas as pd
from atproto import Client
from dotenv import load_dotenv

load_dotenv(override=True)

KEYWORDS = {   # delete domains or keywords to collect less
    "tech": ["artificial intelligence", "openai", "open source", "cybersecurity", "semiconductor"],
    "politics": ["election", "parliament", "policy", "senate", "democracy"],
    "sports": ["cricket", "football", "premier league", "olympics", "nba"],
    "entertainment": ["movie", "netflix", "music", "anime", "gaming"],
    "health": ["mental health", "vaccine", "fitness", "healthcare", "nutrition"],
    "climate": ["climate change", "renewable energy", "electric vehicle", "wildfire", "sustainability"],
    "finance": ["inflation", "stock market", "bitcoin", "interest rates", "economy"],
    "science": ["nasa", "space", "physics", "biology", "research"],
    "education": ["university", "students", "exam", "scholarship", "teaching"],
}
POSTS_PER_KEYWORD = 500
MAX_AUTHORS_FOR_GRAPH = 200
MAX_FOLLOWS_PER_USER = 1000
MIN_FOLLOWERS = 0        # e.g. 100 keeps only accounts with 100+ followers in the graph
OUT = "Data"

os.makedirs(OUT, exist_ok=True)
client = Client()
client.login(os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"])


def collect_posts():
    rows = []
    for domain, words in KEYWORDS.items():
        for kw in words:
            cursor, got = None, 0
            while got < POSTS_PER_KEYWORD:
                try:
                    res = client.app.bsky.feed.search_posts(
                        params={"q": kw, "limit": 100, "cursor": cursor, "lang": "en"})
                except Exception as e:
                    print("search error:", kw, e)
                    time.sleep(5)
                    break
                for p in res.posts:
                    rows.append({
                        "uri": p.uri, "author_did": p.author.did, "author_handle": p.author.handle,
                        "text": getattr(p.record, "text", ""),
                        "created_at": getattr(p.record, "created_at", ""),
                        "likes": p.like_count, "reposts": p.repost_count, "replies": p.reply_count,
                        "keyword": kw, "seed_domain": domain})
                got += len(res.posts)
                cursor = res.cursor
                if not cursor or not res.posts:
                    break
                time.sleep(0.3)
            print(f"{domain}/{kw}: {got} posts")
    df = pd.DataFrame(rows).drop_duplicates("uri")
    df.to_csv(f"{OUT}/posts.csv", index=False)
    return df


def collect_profiles(dids):
    rows = []
    for i in range(0, len(dids), 25):
        try:
            res = client.app.bsky.actor.get_profiles(params={"actors": dids[i:i + 25]})
        except Exception as e:
            print("profile error:", e)
            time.sleep(3)
            continue
        for pr in res.profiles:
            rows.append({"author_did": pr.did, "followers_count": pr.followers_count or 0,
                         "follows_count": pr.follows_count or 0, "posts_count": pr.posts_count or 0})
        time.sleep(0.2)
        if (i // 25) % 20 == 0:
            print(f"profiles: {i} / {len(dids)}")
    prof = pd.DataFrame(rows)
    prof.to_csv(f"{OUT}/author_profiles.csv", index=False)
    return prof


def collect_follows(authors):
    edges = []
    for i, did in enumerate(authors[:MAX_AUTHORS_FOR_GRAPH]):
        cursor, n = None, 0
        while n < MAX_FOLLOWS_PER_USER:
            try:
                res = client.app.bsky.graph.get_follows(params={"actor": did, "limit": 100, "cursor": cursor})
            except Exception as e:
                print("follow error:", did, e)
                break
            edges += [{"source": did, "target": f.did} for f in res.follows]
            n += len(res.follows)
            cursor = res.cursor
            if not cursor:
                break
            time.sleep(0.2)
        if i % 50 == 0:
            print(f"graph: {i} users done")
    pd.DataFrame(edges).to_csv(f"{OUT}/follows.csv", index=False)


if __name__ == "__main__":
    posts = collect_posts()
    print("total unique posts:", len(posts))
    by_posts = posts["author_did"].value_counts().index.tolist()
    prof = collect_profiles(by_posts)
    keep = set(prof.loc[prof["followers_count"] >= MIN_FOLLOWERS, "author_did"])
    authors = [a for a in by_posts if a in keep]
    print(f"authors for graph: {min(len(authors), MAX_AUTHORS_FOR_GRAPH)} of {len(authors)}")
    collect_follows(authors)
    print(f"done: saved posts.csv, author_profiles.csv, follows.csv in {OUT}/")
