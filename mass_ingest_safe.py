import os
import re
import json
import time
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

DB_FILE = r"C:\Users\wjhmo\liljr-unstoppable\liljr_neural_matrix.db"

TARGET_PATHS = [
    r"C:\Users\wjhmo\LILJR-DEEP",
    r"C:\Users\wjhmo\liljr-unstoppable",
    r"C:\Users\wjhmo\Desktop",
]

SKIP_DIR_NAMES = {
    "node_modules", ".git", ".next", "dist", "build", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "AppData", "Windows", "Program Files", "Program Files (x86)",
    ".expo", ".gradle", ".idea", ".vscode", "target", "out",
}

SKIP_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_rsa.pub", "known_hosts", "credentials.json",
    "token.json", "secrets.json", "service-account.json",
}

SKIP_NAME_PATTERNS = [
    re.compile(r".*secret.*", re.I),
    re.compile(r".*password.*", re.I),
    re.compile(r".*private[_-]?key.*", re.I),
    re.compile(r".*api[_-]?key.*", re.I),
]

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt", ".csv",
    ".html", ".css", ".scss", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".env.example", ".sql", ".sh", ".bat", ".ps1", ".java", ".kt", ".xml",
    ".gradle", ".properties", ".dockerfile", ".gitignore", ".tsx", ".jsx",
}

MAX_FILE_BYTES = 2_000_000
COMMIT_EVERY = 250
REPORT_EVERY = 500


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def should_skip_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(SKIP_DIR_NAMES):
        return True

    name = path.name
    if name in SKIP_FILE_NAMES:
        return True

    for pattern in SKIP_NAME_PATTERNS:
        if pattern.match(name):
            return True

    return False


def is_allowed_text_file(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()

    if name in {"dockerfile", "makefile", "readme", "license"}:
        return True

    if suffix in TEXT_EXTENSIONS:
        return True

    if name.endswith(".env.example"):
        return True

    return False


def read_text_safely(path: Path) -> Optional[str]:
    try:
        size = path.stat().st_size
        if size <= 0 or size > MAX_FILE_BYTES:
            return None

        if not is_allowed_text_file(path):
            return None

        raw = path.read_bytes()

        if b"\x00" in raw[:4096]:
            return None

        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return None


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS neural_vault (
            file_path TEXT PRIMARY KEY,
            extension TEXT,
            content TEXT,
            weight REAL DEFAULT 1.0,
            size_bytes INTEGER,
            modified_at REAL,
            sha256 TEXT,
            ingested_at TEXT
        )
    """)

    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(neural_vault)").fetchall()
    }

    extra_cols = {
        "size_bytes": "INTEGER",
        "modified_at": "REAL",
        "sha256": "TEXT",
        "ingested_at": "TEXT",
    }

    for col, col_type in extra_cols.items():
        if col not in existing_cols:
            try:
                conn.execute(f"ALTER TABLE neural_vault ADD COLUMN {col} {col_type}")
            except Exception:
                pass

    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_neural_vault_ext ON neural_vault(extension)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_neural_vault_path ON neural_vault(file_path)")
    except Exception:
        pass

    conn.commit()
    return conn


def already_current(conn: sqlite3.Connection, path: Path, size: int, mtime: float) -> bool:
    try:
        row = conn.execute(
            "SELECT size_bytes, modified_at FROM neural_vault WHERE file_path = ? LIMIT 1",
            (str(path),),
        ).fetchone()
        if not row:
            return False

        old_size, old_mtime = row
        return old_size == size and abs(float(old_mtime or 0) - float(mtime)) < 0.001
    except Exception:
        return False


def iter_files(paths: Iterable[str]) -> Iterable[Path]:
    for raw_path in paths:
        base = Path(raw_path)
        if not base.exists():
            print(f"⚠️ Missing path, skipped: {base}")
            continue

        for root, dirs, files in os.walk(base):
            root_path = Path(root)

            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIR_NAMES and not should_skip_path(root_path / d)
            ]

            if should_skip_path(root_path):
                continue

            for file_name in files:
                path = root_path / file_name
                if not should_skip_path(path):
                    yield path


def upsert_file(conn: sqlite3.Connection, path: Path, content: str) -> None:
    stat = path.stat()
    extension = path.suffix.lower()
    digest = sha256_text(content)

    # Delete first so this works even if the old table was created without a primary key.
    conn.execute("DELETE FROM neural_vault WHERE file_path = ?", (str(path),))
    conn.execute(
        """
        INSERT INTO neural_vault
        (file_path, extension, content, weight, size_bytes, modified_at, sha256, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(path),
            extension,
            content,
            1.0,
            stat.st_size,
            stat.st_mtime,
            digest,
            now_iso(),
        ),
    )


def mass_ingestion() -> None:
    print("🧠 STARTING SAFE MASS INGESTION...")
    print(f"DB: {DB_FILE}")
    print("Targets:")
    for p in TARGET_PATHS:
        print(f" - {p}")

    conn = connect_db()

    scanned = 0
    ingested = 0
    skipped_current = 0
    skipped_unreadable = 0
    started = time.time()

    try:
        for path in iter_files(TARGET_PATHS):
            scanned += 1

            try:
                stat = path.stat()
                if already_current(conn, path, stat.st_size, stat.st_mtime):
                    skipped_current += 1
                    continue
            except Exception:
                skipped_unreadable += 1
                continue

            content = read_text_safely(path)
            if content is None or not content.strip():
                skipped_unreadable += 1
                continue

            try:
                upsert_file(conn, path, content)
                ingested += 1
            except Exception as e:
                skipped_unreadable += 1
                if skipped_unreadable % 100 == 0:
                    print(f"⚠️ Skipped unreadable/problem files: {skipped_unreadable}")

            if ingested and ingested % COMMIT_EVERY == 0:
                conn.commit()

            if scanned % REPORT_EVERY == 0:
                elapsed = max(time.time() - started, 1)
                rate = scanned / elapsed
                print(
                    f"Scanned={scanned} | Ingested={ingested} | "
                    f"AlreadyCurrent={skipped_current} | Skipped={skipped_unreadable} | "
                    f"Rate={rate:.1f}/sec"
                )

        conn.commit()

        total = conn.execute("SELECT COUNT(*) FROM neural_vault").fetchone()[0]

        print("")
        print("✅ MASS INGESTION COMPLETE")
        print(f"Scanned files: {scanned}")
        print(f"New/updated ingested files: {ingested}")
        print(f"Already current files skipped: {skipped_current}")
        print(f"Unreadable/binary/secret/oversize skipped: {skipped_unreadable}")
        print(f"Total neural_vault rows: {total}")
        print(f"Elapsed seconds: {round(time.time() - started, 2)}")

    finally:
        conn.close()


if __name__ == "__main__":
    mass_ingestion()
