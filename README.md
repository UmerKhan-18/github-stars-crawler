# GitHub Stars Crawler

This project automatically crawls public GitHub repositories using the **GitHub GraphQL API** and stores their star counts in a **PostgreSQL database**.  
It runs entirely within **GitHub Actions** and supports **parallel crawling** for faster performance.

---

## Overview

The system connects to the **GitHub GraphQL API**, fetches repository data (ID, name, owner, stars, etc.), and stores it into a PostgreSQL database.  
Data is automatically exported as a **CSV artifact** after every workflow run.

---

## Features

- Fetches up to **100K+ repositories** (configurable to 500M+)
- Uses **SQLAlchemy ORM** instead of raw SQL
- Stores data in **PostgreSQL**
- Handles **pagination**, **rate limits**, and **automatic retries**
- **Parallel fetching** – configurable number of threads via environment variable
- Generates and uploads a **CSV dump artifact** in each workflow run
- Modular and production-ready folder structure

---

## Architecture

GitHub GraphQL API → Python Crawler (Parallel Threads)

↓

PostgreSQL (ORM via SQLAlchemy)

↓

CSV Dump Artifact (Uploaded by GitHub Actions)

---

## Database Schema

The schema is defined via ORM in `src/db.py`.

```sql
CREATE TABLE IF NOT EXISTS repos (
  repo_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  owner TEXT NOT NULL,
  name TEXT NOT NULL,
  stargazers_count BIGINT,
  last_crawled TIMESTAMP WITH TIME ZONE DEFAULT now(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_repos_last_crawled ON repos(last_crawled);
```

---

### Why this design:

- repo_id → unique GitHub identifier (used for upserts)
- metadata → flexible JSON column for future fields like forks, issues, PRs
- last_crawled → supports incremental crawling

### Responsibilities

- Fetch repository data from **GitHub GraphQL API**
- Insert or update rows in **PostgreSQL** using **SQLAlchemy ORM**
- Handle **pagination**, **rate limits**, and **retries**
- Support **parallel crawling** for faster throughput
- Commit data in safe, consistent batches
- Export final dataset as a **CSV artifact** after each run

---

# GitHub Actions Workflow

The entire pipeline runs automatically via the workflow file:  
`.github/workflows/crawl.yml`

---

## Workflow Steps

1. **Checkout the repository**
2. **Setup Python environment**
3. **Start PostgreSQL service container**
4. **Apply database schema (`setup.sql`)**
5. **Run the crawler script (`main.py`)**
6. **Export database contents to CSV (`repos_dump.csv`)**
7. **Upload CSV as an artifact** for later download or inspection

---

### Trigger Options

- **Manual:** From GitHub → **Actions tab → “Crawl GitHub Repositories” → Run workflow**
- **Automatic:** Scheduled daily at **02:00 UTC**

---

### Output Artifact (repos_dump.csv)

After each run, the crawler uploads a CSV file as a GitHub Actions artifact.

Example contents:

```csv
repo_id,full_name,owner,name,stargazers_count,last_crawled,metadata
MDEwOlJlcG9zaXRvcnkyMzI1Mjk4,torvalds/linux,torvalds,linux,206128,2025-11-02T02:09:10Z,{}
MDEwOlJlcG9zaXRvcnkxMzI3NTA3MjQ=,codecrafters-io/build-your-own-x,codecrafters-io,build-your-own-x,432517,2025-11-02T02:09:10Z,{}
```

# Technologies Used

- Python 3.10
- PostgreSQL 15
- SQLAlchemy ORM (database layer)
- Requests (GraphQL API calls)
- Pandas (CSV export)
- GitHub Actions (automation pipeline)
- ThreadPoolExecutor (parallel crawling)
- GitHub GraphQL API v4

# Project Structure

```pgsql
.
├── main.py
├── src/
│ ├── config.py # Environment config & constants
│ ├── db.py # SQLAlchemy ORM setup & models
│ ├── github_api.py # GitHub GraphQL API helper
│ └── crawler.py # Main crawling logic (parallel)
├── sql/
│ └── setup.sql # DB schema
├── .github/
│ └── workflows/
│   └── crawl.yml
├── .env.example
├── requirements.txt
└── README.md

```

# Future Improvements

1. Extend to Pull Requests, Issues & Comments
   Add new tables:

   ```sql
   CREATE TABLE pull_requests (pr_id TEXT PRIMARY KEY, repo_id TEXT, metadata JSONB, last_updated TIMESTAMP);
   CREATE TABLE issues (issue_id TEXT PRIMARY KEY, repo_id TEXT, metadata JSONB, last_updated TIMESTAMP);
   CREATE TABLE comments (comment_id TEXT PRIMARY KEY, pr_id TEXT, metadata JSONB, last_updated TIMESTAMP);
   Use last_updated for incremental updates.

   ```

2. Scale for 500M+ Repositories

- Shard repositories across multiple workers
- Use message queues (e.g., Kafka) between crawler and database
- Store cold data in S3/Parquet, hot data in Postgres
- Rotate tokens for distributed rate-limit management

3. Monitoring & Reliability

- Add detailed logs & metrics
- Slack/email notifications for job status
- Add checkpoints to resume interrupted crawls
