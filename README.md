# BlackRoad Wiki

![License](https://img.shields.io/badge/license-Proprietary-red)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![npm](https://img.shields.io/badge/npm-ready-brightgreen)
![Stripe](https://img.shields.io/badge/stripe-integrated-blueviolet)
![Status](https://img.shields.io/badge/status-production-success)

> **The enterprise wiki and knowledge base engine powering BlackRoad OS.** Full-text search, complete revision history, hierarchical namespaces, Stripe billing integration, and an npm-ready JavaScript client — built for teams that ship at scale.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
   - [Python Package](#python-package)
   - [npm Client](#npm-client)
5. [Quick Start](#quick-start)
6. [Configuration](#configuration)
7. [CLI Reference](#cli-reference)
   - [create](#create)
   - [search](#search)
   - [tree](#tree)
   - [export](#export)
8. [Python API Reference](#python-api-reference)
   - [WikiEngine](#wikiengine)
   - [Page](#page)
   - [Revision](#revision)
9. [Stripe Integration](#stripe-integration)
10. [Database](#database)
11. [End-to-End Testing](#end-to-end-testing)
12. [License](#license)

---

## Overview

BlackRoad Wiki is the production-grade knowledge management layer of the **BlackRoad OS** platform. It provides a battle-tested wiki engine with versioned Markdown pages, hierarchical namespaces, and full-text search — all backed by a zero-dependency SQLite store that scales to 125,000+ pages.

The engine ships as both a **Python library** (for backend integration) and an **npm-compatible JavaScript client** (for frontend and Node.js applications), and integrates natively with **Stripe** for subscription-gated content and metered knowledge-base access.

---

## Features

| Feature | Description |
|---|---|
| **Versioned Pages** | Every save creates an immutable revision; roll back to any point in time |
| **Hierarchical Namespaces** | Organize content in `/docs`, `/api`, `/guides`, or any custom tree |
| **Full-Text Search** | SQLite FTS5-powered search across titles and content |
| **Revision History** | Complete audit trail with diff sizes and author attribution |
| **Soft Delete** | Non-destructive deletion; pages can be restored at any time |
| **Markdown Export** | Bulk-export any namespace to a directory of `.md` files |
| **Statistics** | Page count, unique authors, total revisions, and namespace counts |
| **Stripe Billing** | Gate content behind subscription plans; track metered API usage |
| **npm Client** | Drop-in JavaScript/TypeScript client for React, Next.js, and Node.js apps |
| **Parent/Child Pages** | Hierarchical page relationships with breadcrumb support |

---

## Requirements

- **Python** 3.9 or higher
- **SQLite** 3.35+ with FTS5 enabled (bundled with CPython ≥ 3.6)
- **Node.js** 18+ / **npm** 9+ *(npm client only)*
- **Stripe** account with API keys *(billing features only)*

---

## Installation

### Python Package

Install directly from the repository:

```bash
pip install -r requirements.txt
```

Or install the package in editable mode for development:

```bash
pip install -e .
```

### npm Client

The BlackRoad Wiki JavaScript client will be published to npm. Once available:

```bash
npm install @blackroad-os/wiki-client
```

```bash
yarn add @blackroad-os/wiki-client
```

```bash
pnpm add @blackroad-os/wiki-client
```

#### Basic npm usage

```js
import { WikiClient } from '@blackroad-os/wiki-client';

const wiki = new WikiClient({
  apiUrl: 'https://api.blackroad.io/wiki',
  apiKey: process.env.BLACKROAD_API_KEY,
});

// Fetch a page
const page = await wiki.getPage('getting-started');

// Search
const results = await wiki.search('authentication');
```

---

## Quick Start

```python
from src.wiki import WikiEngine

# Initialize the engine (creates ~/.blackroad/wiki.db automatically)
wiki = WikiEngine()

# Create a page
page = wiki.create_page(
    title="Getting Started",
    content="# Welcome to BlackRoad Wiki\n\nThis is your first page.",
    namespace="/docs",
    author="alice",
    tags=["onboarding", "docs"],
)
print(page.slug)  # getting-started

# Search
results = wiki.search("welcome")
for p in results:
    print(p.title, p.slug)

# Get revision history
revisions = wiki.get_revisions(page.slug)

# Export namespace to markdown files
wiki.export_markdown(namespace="/docs", output_dir="./wiki_export")
```

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `BLACKROAD_DB_PATH` | `~/.blackroad/wiki.db` | Path to the SQLite database file |
| `BLACKROAD_STRIPE_SECRET_KEY` | *(required for billing)* | Stripe secret key (`sk_live_…` or `sk_test_…`) |
| `BLACKROAD_STRIPE_WEBHOOK_SECRET` | *(required for billing)* | Stripe webhook signing secret |
| `BLACKROAD_API_KEY` | *(required for npm client)* | API key for the hosted REST gateway |

Set variables in your environment or in a `.env` file:

```bash
BLACKROAD_DB_PATH=/var/lib/blackroad/wiki.db
BLACKROAD_STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
BLACKROAD_STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
BLACKROAD_API_KEY=bk_live_xxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **Never commit API keys or secrets to source control.** Use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault) or a `.env` file that is listed in `.gitignore`.

---

## CLI Reference

Run via Python module:

```bash
python src/wiki.py <command> [options]
```

### create

Create a new wiki page.

```bash
python src/wiki.py create "Page Title" \
  --content "# Page Title\n\nContent here..." \
  --namespace /docs
```

| Argument | Required | Description |
|---|---|---|
| `title` | ✅ | Human-readable page title |
| `--content` | | Page body in Markdown |
| `--namespace` | | Target namespace (default: `/`) |

### search

Full-text search across all pages.

```bash
python src/wiki.py search "authentication"
```

| Argument | Required | Description |
|---|---|---|
| `query` | ✅ | Search string |

### tree

Display the page hierarchy for a namespace.

```bash
python src/wiki.py tree /docs
```

| Argument | Required | Description |
|---|---|---|
| `namespace` | | Namespace to inspect (default: `/`) |

### export

Export all pages in a namespace to Markdown files.

```bash
python src/wiki.py export --output-dir ./wiki_export
```

| Argument | Required | Description |
|---|---|---|
| `--output-dir` | | Destination directory (default: `./wiki_export`) |

---

## Python API Reference

### WikiEngine

```python
WikiEngine(db_path: Path = DB_PATH)
```

The central engine class. All methods are synchronous and thread-safe via per-call SQLite connections.

| Method | Signature | Returns | Description |
|---|---|---|---|
| `create_page` | `(title, content, namespace="/", author="", tags=None, parent_id=None)` | `Page` | Create a new page and its initial revision |
| `update_page` | `(slug, content, author="", summary="")` | `Page` | Save new content and create a revision |
| `get_page` | `(slug, version=None)` | `Page` | Retrieve the latest page or a specific revision |
| `delete_page` | `(slug)` | `None` | Soft-delete a page (recoverable) |
| `search` | `(query, namespace=None)` | `List[Page]` | Full-text search on title and content |
| `get_revisions` | `(slug)` | `List[Revision]` | Full revision history, newest first |
| `restore_revision` | `(slug, version)` | `Page` | Revert page to a prior version |
| `get_namespace_tree` | `(namespace="/")` | `Dict` | Hierarchical page tree for a namespace |
| `export_markdown` | `(namespace="/", output_dir="./wiki_export")` | `Path` | Write all pages to `.md` files |
| `get_recent_changes` | `(limit=20)` | `List[Page]` | Most recently updated pages |
| `get_stats` | `()` | `Dict` | Page count, namespace count, revision count, author count |

### Page

```python
@dataclass
class Page:
    id: str           # UUID
    slug: str         # URL-safe identifier derived from title
    title: str
    content: str      # Markdown body
    version: int      # Current version number
    author: str
    tags: List[str]
    namespace: str    # e.g. "/docs/api"
    created_at: str   # ISO 8601 timestamp
    updated_at: str   # ISO 8601 timestamp
    view_count: int
    is_locked: bool
    parent_id: Optional[str]  # UUID of parent page, if any
```

### Revision

```python
@dataclass
class Revision:
    id: str           # UUID
    page_id: str      # UUID of the owning page
    version: int
    content: str      # Markdown body at this revision
    author: str
    summary: str      # Commit-style change summary
    created_at: str   # ISO 8601 timestamp
    diff_size: int    # Absolute character delta vs. previous version
```

---

## Stripe Integration

BlackRoad Wiki integrates with [Stripe](https://stripe.com) to support subscription-gated namespaces and metered knowledge-base access.

### How It Works

1. **Subscription Plans** — Map Stripe products/prices to wiki namespaces. A user with an active `pro` subscription gains read/write access to `/docs/pro` and `/api`.
2. **Metered Usage** — Each `get_page` call can be reported to Stripe Billing as a metered event, enabling pay-per-read pricing.
3. **Webhook Sync** — Customer subscription events (`customer.subscription.updated`, `customer.subscription.deleted`) automatically revoke or grant namespace access.

### Setup

```bash
# Install the Stripe Python library
pip install stripe
```

Set your keys in the environment:

```bash
BLACKROAD_STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
BLACKROAD_STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
```

### Stripe Webhook Endpoint

Register the following endpoint in your [Stripe Dashboard](https://dashboard.stripe.com/webhooks):

```
POST https://your-domain.com/webhooks/stripe
```

Listen for the following events:

- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

### Test Mode

Use Stripe test keys (`sk_test_…`) and the [Stripe CLI](https://stripe.com/docs/stripe-cli) to forward webhooks locally:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

### Enforcing Access in WikiEngine

Wrap `get_page` and `create_page` calls with a subscription check before delegating to the engine:

```python
import stripe
stripe.api_key = os.environ["BLACKROAD_STRIPE_SECRET_KEY"]

def get_page_gated(wiki: WikiEngine, slug: str, customer_id: str) -> Page:
    subscriptions = stripe.Subscription.list(customer=customer_id, status="active")
    active_plans = {item.price.id for sub in subscriptions for item in sub["items"]["data"]}
    if not active_plans:
        raise PermissionError("Active subscription required")
    return wiki.get_page(slug)
```

---

## Database

BlackRoad Wiki uses an **SQLite** database with the following schema:

```
~/.blackroad/wiki.db   (default location)
```

### Tables

| Table | Purpose |
|---|---|
| `pages` | Current state of every wiki page |
| `revisions` | Full revision history for all pages |
| `page_links` | Tracks inter-page hyperlinks |

### Indexes

| Index | Columns | Purpose |
|---|---|---|
| `idx_pages_slug` | `pages(slug)` | Fast page lookup by URL slug |
| `idx_pages_namespace` | `pages(namespace)` | Namespace filtering and tree views |
| `idx_pages_parent` | `pages(parent_id)` | Parent–child hierarchy traversal |
| `idx_revisions_page` | `revisions(page_id)` | Revision list retrieval |
| `idx_revisions_version` | `revisions(page_id, version)` | Point-in-time version lookup |

---

## End-to-End Testing

Run the full end-to-end test suite to verify all components before deploying to production:

```bash
# Python unit and integration tests
python -m pytest tests/ -v

# Stripe webhook integration test (requires Stripe CLI)
stripe listen --forward-to localhost:8000/webhooks/stripe &
python -m pytest tests/e2e/test_stripe.py -v
```

All CI checks must pass on the `main` branch before any production deployment.

---

## License

Proprietary — © BlackRoad OS, Inc. All rights reserved.  
See [LICENSE](./LICENSE) for full terms.
