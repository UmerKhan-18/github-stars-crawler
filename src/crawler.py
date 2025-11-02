from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import MAX_REPOS, PAGE_SIZE, THREAD_COUNT
from src.github_api import fetch_page, handle_rate_limit
from src.db import SessionLocal, Repo
from datetime import datetime
import pandas as pd, os

def upsert_repo(session, repo_node):
    repo_id = repo_node["id"]
    full_name = repo_node["nameWithOwner"]
    owner, name = full_name.split("/", 1)
    stars = repo_node.get("stargazerCount", 0)
    repo = Repo(
        repo_id=repo_id,
        full_name=full_name,
        owner=owner,
        name=name,
        stargazers_count=stars,
        last_crawled=datetime.utcnow(),
        metadata={}
    )
    session.merge(repo)

def crawl_and_persist():
    """Crawl GitHub repos in parallel using THREAD_COUNT threads."""
    session = SessionLocal()
    total = 0
    cursor = None
    print(f"Starting crawl with {THREAD_COUNT} parallel threads...")
    try:
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = [executor.submit(fetch_page, cursor) for _ in range(THREAD_COUNT)]
            while total < MAX_REPOS:
                for future in as_completed(futures):
                    repos, page_info, rate_limit = future.result()
                    if not repos:
                        continue
                    for node in repos:
                        upsert_repo(session, node)
                        total += 1
                        if total >= MAX_REPOS:
                            break
                    session.commit()
                    handle_rate_limit(rate_limit)
                    if page_info.get("hasNextPage") and total < MAX_REPOS:
                        next_cursor = page_info.get("endCursor")
                        futures.append(executor.submit(fetch_page, next_cursor))
                    if total >= MAX_REPOS:
                        break
                if total >= MAX_REPOS:
                    break
        print(f"Crawl finished: {total} repos fetched.")
        return total
    finally:
        session.close()

def export_csv(output_path):
    from src.db import engine
    query = "SELECT repo_id, full_name, owner, name, stargazers_count, last_crawled, metadata FROM repos ORDER BY stargazers_count DESC"
    df = pd.read_sql(query, engine)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f" CSV exported: {output_path}")
