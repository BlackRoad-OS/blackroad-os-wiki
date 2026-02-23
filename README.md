# BlackRoad Wiki

Wiki and knowledge base system with full-text search, revision history, and hierarchical namespaces.

## Features

- **Pages**: Markdown-based content with versioning
- **Namespaces**: Organize pages in hierarchical structure
- **Revisions**: Complete revision history with restore capability
- **Search**: Full-text search on titles and content
- **Soft Delete**: Non-destructive page deletion
- **Export**: Export wiki pages as markdown
- **Statistics**: Track page count, authors, and revisions

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Create a page
```bash
python src/wiki.py create "Getting Started" --content "# Welcome\n..." --namespace /docs
```

### Search pages
```bash
python src/wiki.py search "authentication"
```

### View namespace tree
```bash
python src/wiki.py tree /docs
```

### Export wiki
```bash
python src/wiki.py export --output-dir ./wiki_export
```

## Database

SQLite database with FTS5 virtual table at `~/.blackroad/wiki.db`

## API

### WikiEngine Class

- `create_page(title, content, namespace, author, tags, parent_id)` - Create page
- `update_page(slug, content, author, summary)` - Create new revision
- `get_page(slug, version)` - Get page at version (latest if not specified)
- `delete_page(slug)` - Soft delete page
- `search(query, namespace)` - Full-text search
- `get_revisions(slug)` - Get revision history
- `restore_revision(slug, version)` - Revert to previous version
- `get_namespace_tree(namespace)` - Get hierarchical tree
- `export_markdown(namespace, output_dir)` - Export pages as markdown
- `get_recent_changes(limit)` - Get recently updated pages
- `get_stats()` - Get wiki statistics

## License

MIT
