import os
import time
import pandas as pd
import collect_bluesky_v2 as c

PART, DONE = "Data/follows_partial.csv", "Data/follows_done.txt"

posts = pd.read_csv("Data/posts.csv", usecols=["author_did"])
prof = pd.read_csv("Data/author_profiles.csv")
by_posts = posts["author_did"].value_counts().index.tolist()
keep = set(prof.loc[prof["followers_count"] >= c.MIN_FOLLOWERS, "author_did"])
authors = [a for a in by_posts if a in keep][: c.MAX_AUTHORS_FOR_GRAPH]

done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
first = not os.path.exists(PART)
print(f"{len(done)} already done, {len(authors) - len(done)} to go")

for i, did in enumerate(authors):
    if did in done:
        continue
    rows, cursor, n = [], None, 0
    while n < c.MAX_FOLLOWS_PER_USER:
        try:
            res = c.client.app.bsky.graph.get_follows(
                params={"actor": did, "limit": 100, "cursor": cursor})
        except Exception:
            print("follow error:", did)
            break
        rows += [{"source": did, "target": f.did} for f in res.follows]
        n += len(res.follows)
        cursor = res.cursor
        if not cursor:
            break
        time.sleep(0.2)
    pd.DataFrame(rows, columns=["source", "target"]).to_csv(PART, mode="a", header=first, index=False)
    first = False
    with open(DONE, "a") as f:
        f.write(did + "\n")
    if i % 50 == 0:
        print(f"graph: {i} / {len(authors)}")

os.replace(PART, "Data/follows.csv")
print("done: Data/follows.csv saved")