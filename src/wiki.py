"""
BlackRoad Wiki and Knowledge Base System
Taiga-inspired wiki engine with full-text search and revision history
"""

import sqlite3
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import argparse
from contextlib import contextmanager
from urllib.parse import quote


DB_PATH = Path.home() / ".blackroad" / "wiki.db"


@dataclass
class Page:
    """Wiki page with versioning support"""
    id: str
    slug: str
    title: str
    content: str
    version: int
    author: str
    tags: List[str]
    namespace: str
    created_at: str
    updated_at: str
    view_count: int = 0
    is_locked: bool = False
    parent_id: Optional[str] = None


@dataclass
class Revision:
    """Page revision with diff tracking"""
    id: str
    page_id: str
    version: int
    content: str
    author: str
    summary: str
    created_at: str
    diff_size: int = 0


class WikiEngine:
    """Wiki and knowledge base engine"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        try:
            # Try to load FTS5
            try:
                conn.enable_load_extension(True)
                conn.load_extension('fts5')
            except:
                pass
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database with schema"""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pages (
                    id TEXT PRIMARY KEY,
                    slug TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    author TEXT,
                    tags TEXT,
                    namespace TEXT DEFAULT '/',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    is_locked BOOLEAN DEFAULT 0,
                    parent_id TEXT,
                    is_deleted BOOLEAN DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS revisions (
                    id TEXT PRIMARY KEY,
                    page_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    diff_size INTEGER DEFAULT 0,
                    FOREIGN KEY (page_id) REFERENCES pages(id)
                );
                
                CREATE TABLE IF NOT EXISTS page_links (
                    id TEXT PRIMARY KEY,
                    from_page_id TEXT NOT NULL,
                    to_slug TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (from_page_id) REFERENCES pages(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_pages_slug ON pages(slug);
                CREATE INDEX IF NOT EXISTS idx_pages_namespace ON pages(namespace);
                CREATE INDEX IF NOT EXISTS idx_pages_parent ON pages(parent_id);
                CREATE INDEX IF NOT EXISTS idx_revisions_page ON revisions(page_id);
                CREATE INDEX IF NOT EXISTS idx_revisions_version ON revisions(page_id, version);
            """)
            conn.commit()

    def _slug_from_title(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def create_page(self, title: str, content: str, namespace: str = "/", 
                   author: str = "", tags: List[str] = None, parent_id: Optional[str] = None) -> Page:
        """Create a new page"""
        from uuid import uuid4
        
        page_id = str(uuid4())
        slug = self._slug_from_title(title)
        
        # Ensure slug uniqueness
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM pages WHERE slug = ?", (slug,)
            ).fetchone()
            
            if existing:
                slug = f"{slug}-{page_id[:8]}"
        
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])
        
        page = Page(
            id=page_id, slug=slug, title=title, content=content,
            version=1, author=author, tags=tags or [], namespace=namespace,
            created_at=now, updated_at=now, parent_id=parent_id
        )
        
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO pages 
                   (id, slug, title, content, version, author, tags, namespace, created_at, updated_at, parent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, slug, title, content, 1, author, tags_json, namespace, now, now, parent_id)
            )
            
            # Create initial revision
            rev_id = str(uuid4())
            conn.execute(
                """INSERT INTO revisions 
                   (id, page_id, version, content, author, summary, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (rev_id, page_id, 1, content, author, "Initial version", now)
            )
            
            conn.commit()
        
        return page

    def update_page(self, slug: str, content: str, author: str = "", summary: str = "") -> Page:
        """Update page content and create new revision"""
        from uuid import uuid4
        
        with self._get_conn() as conn:
            page = conn.execute(
                "SELECT * FROM pages WHERE slug = ? AND is_deleted = 0", (slug,)
            ).fetchone()
            
            if not page:
                raise ValueError(f"Page not found: {slug}")
            
            now = datetime.now().isoformat()
            new_version = page['version'] + 1
            
            # Calculate diff size
            diff_size = abs(len(content) - len(page['content']))
            
            # Update page
            conn.execute(
                """UPDATE pages SET content = ?, version = ?, author = ?, updated_at = ?
                   WHERE slug = ?""",
                (content, new_version, author, now, slug)
            )
            
            # Create revision
            rev_id = str(uuid4())
            conn.execute(
                """INSERT INTO revisions 
                   (id, page_id, version, content, author, summary, created_at, diff_size)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (rev_id, page['id'], new_version, content, author, summary, now, diff_size)
            )
            
            conn.commit()
        
        return self.get_page(slug)

    def get_page(self, slug: str, version: Optional[int] = None) -> Page:
        """Get page by slug, optionally at specific version"""
        with self._get_conn() as conn:
            if version:
                # Get specific revision
                rev = conn.execute(
                    """SELECT * FROM revisions 
                       WHERE page_id = (SELECT id FROM pages WHERE slug = ?) AND version = ?""",
                    (slug, version)
                ).fetchone()
                
                if not rev:
                    raise ValueError(f"Revision not found: {slug} v{version}")
                
                page = conn.execute(
                    "SELECT * FROM pages WHERE id = ?", (rev['page_id'],)
                ).fetchone()
            else:
                # Get latest
                page = conn.execute(
                    "SELECT * FROM pages WHERE slug = ? AND is_deleted = 0", (slug,)
                ).fetchone()
                
                if not page:
                    raise ValueError(f"Page not found: {slug}")
            
            # Increment view count
            conn.execute("UPDATE pages SET view_count = view_count + 1 WHERE id = ?", (page['id'],))
            conn.commit()
        
        tags = json.loads(page['tags'] or '[]')
        return Page(
            id=page['id'], slug=page['slug'], title=page['title'],
            content=rev['content'] if version else page['content'],
            version=version or page['version'], author=page['author'],
            tags=tags, namespace=page['namespace'], created_at=page['created_at'],
            updated_at=page['updated_at'], view_count=page['view_count'],
            is_locked=page['is_locked'], parent_id=page['parent_id']
        )

    def delete_page(self, slug: str):
        """Soft delete a page"""
        with self._get_conn() as conn:
            conn.execute("UPDATE pages SET is_deleted = 1 WHERE slug = ?", (slug,))
            conn.commit()

    def search(self, query: str, namespace: Optional[str] = None) -> List[Page]:
        """Full-text search on title and content"""
        with self._get_conn() as conn:
            sql = """SELECT * FROM pages 
                     WHERE is_deleted = 0 
                     AND (title LIKE ? OR content LIKE ?)"""
            params = [f"%{query}%", f"%{query}%"]
            
            if namespace:
                sql += " AND namespace = ?"
                params.append(namespace)
            
            results = conn.execute(sql, params).fetchall()
        
        pages = []
        for row in results:
            tags = json.loads(row['tags'] or '[]')
            page = Page(
                id=row['id'], slug=row['slug'], title=row['title'],
                content=row['content'], version=row['version'], author=row['author'],
                tags=tags, namespace=row['namespace'], created_at=row['created_at'],
                updated_at=row['updated_at'], view_count=row['view_count'],
                is_locked=row['is_locked'], parent_id=row['parent_id']
            )
            pages.append(page)
        
        return pages

    def get_revisions(self, slug: str) -> List[Revision]:
        """Get revision history for a page"""
        with self._get_conn() as conn:
            page = conn.execute(
                "SELECT id FROM pages WHERE slug = ?", (slug,)
            ).fetchone()
            
            if not page:
                raise ValueError(f"Page not found: {slug}")
            
            revisions = conn.execute(
                """SELECT * FROM revisions WHERE page_id = ? ORDER BY version DESC""",
                (page['id'],)
            ).fetchall()
        
        result = []
        for row in revisions:
            rev = Revision(
                id=row['id'], page_id=row['page_id'], version=row['version'],
                content=row['content'], author=row['author'], summary=row['summary'],
                created_at=row['created_at'], diff_size=row['diff_size']
            )
            result.append(rev)
        
        return result

    def restore_revision(self, slug: str, version: int) -> Page:
        """Revert page to a previous version"""
        from uuid import uuid4
        
        revision = self.get_revisions(slug)[version - 1] if version > 0 else None
        if not revision:
            raise ValueError(f"Revision not found: {slug} v{version}")
        
        return self.update_page(
            slug, 
            revision.content,
            author="system",
            summary=f"Restored to version {version}"
        )

    def get_namespace_tree(self, namespace: str = "/") -> Dict[str, Any]:
        """Get hierarchical page tree for namespace"""
        with self._get_conn() as conn:
            pages = conn.execute(
                """SELECT id, slug, title, parent_id FROM pages 
                   WHERE namespace = ? AND is_deleted = 0 ORDER BY title""",
                (namespace,)
            ).fetchall()
        
        tree = {"namespace": namespace, "pages": []}
        for page in pages:
            if not page['parent_id']:
                tree["pages"].append({
                    "id": page['id'],
                    "slug": page['slug'],
                    "title": page['title'],
                    "children": []
                })
        
        return tree

    def export_markdown(self, namespace: str = "/", output_dir: str = "./wiki_export") -> Path:
        """Export all pages as markdown files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        with self._get_conn() as conn:
            pages = conn.execute(
                "SELECT * FROM pages WHERE namespace = ? AND is_deleted = 0 ORDER BY created_at",
                (namespace,)
            ).fetchall()
        
        for page in pages:
            file_path = output_path / f"{page['slug']}.md"
            content = f"# {page['title']}\n\n{page['content']}"
            file_path.write_text(content, encoding='utf-8')
        
        return output_path

    def get_recent_changes(self, limit: int = 20) -> List[Page]:
        """Get recently updated pages"""
        with self._get_conn() as conn:
            pages = conn.execute(
                """SELECT * FROM pages WHERE is_deleted = 0 
                   ORDER BY updated_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
        
        result = []
        for row in pages:
            tags = json.loads(row['tags'] or '[]')
            page = Page(
                id=row['id'], slug=row['slug'], title=row['title'],
                content=row['content'], version=row['version'], author=row['author'],
                tags=tags, namespace=row['namespace'], created_at=row['created_at'],
                updated_at=row['updated_at'], view_count=row['view_count'],
                is_locked=row['is_locked'], parent_id=row['parent_id']
            )
            result.append(page)
        
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get wiki statistics"""
        with self._get_conn() as conn:
            pages = conn.execute(
                "SELECT COUNT(*) as count FROM pages WHERE is_deleted = 0"
            ).fetchone()
            
            namespaces = conn.execute(
                "SELECT DISTINCT namespace FROM pages WHERE is_deleted = 0"
            ).fetchall()
            
            revisions = conn.execute(
                "SELECT COUNT(*) as count FROM revisions"
            ).fetchone()
            
            authors = conn.execute(
                "SELECT DISTINCT author FROM pages WHERE author IS NOT NULL"
            ).fetchall()
        
        return {
            "page_count": pages['count'],
            "namespaces": len(namespaces),
            "total_revisions": revisions['count'],
            "unique_authors": len(authors)
        }


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description="BlackRoad Wiki")
    subparsers = parser.add_subparsers(dest="command")
    
    # create command
    create_parser = subparsers.add_parser("create", help="Create page")
    create_parser.add_argument("title", help="Page title")
    create_parser.add_argument("--content", help="Page content")
    create_parser.add_argument("--namespace", default="/", help="Page namespace")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search pages")
    search_parser.add_argument("query", help="Search query")
    
    # tree command
    tree_parser = subparsers.add_parser("tree", help="Show namespace tree")
    tree_parser.add_argument("namespace", default="/", nargs="?", help="Namespace")
    
    args = parser.parse_args()
    
    wiki = WikiEngine()
    
    if args.command == "create":
        page = wiki.create_page(args.title, args.content or "", namespace=args.namespace)
        print(f"Created: {page.slug}")
    
    elif args.command == "search":
        results = wiki.search(args.query)
        for page in results:
            print(f"- {page.title} ({page.slug})")
    
    elif args.command == "tree":
        tree = wiki.get_namespace_tree(args.namespace)
        print(f"Pages in {tree['namespace']}:")
        for page in tree['pages']:
            print(f"  - {page['title']}")


if __name__ == "__main__":
    main()
