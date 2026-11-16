import sqlite3
import re
from pathlib import Path
from .models import Turn


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS meetings(
          meeting_id TEXT PRIMARY KEY, team_id TEXT NOT NULL, meeting_number INTEGER NOT NULL,
          source_path TEXT NOT NULL, content TEXT NOT NULL, word_count INTEGER NOT NULL,
          ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS turns(
          id INTEGER PRIMARY KEY, meeting_id TEXT NOT NULL, team_id TEXT NOT NULL,
          meeting_number INTEGER NOT NULL, speaker TEXT NOT NULL, timestamp TEXT NOT NULL,
          text TEXT NOT NULL, start_offset INTEGER NOT NULL, end_offset INTEGER NOT NULL,
          UNIQUE(meeting_id, start_offset)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
          text, meeting_id UNINDEXED, team_id UNINDEXED, speaker UNINDEXED,
          content='turns', content_rowid='id'
        );
        CREATE TABLE IF NOT EXISTS ingestion_runs(
          id INTEGER PRIMARY KEY, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          completed_at TEXT, files_seen INTEGER, turns_written INTEGER, errors TEXT
        );
        """)
        self.db.commit()

    def replace_meeting(self, meeting_id: str, team_id: str, number: int,
                        source: str, content: str, turns: list[Turn]) -> None:
        self.db.execute("DELETE FROM turns_fts WHERE rowid IN (SELECT id FROM turns WHERE meeting_id=?)", (meeting_id,))
        self.db.execute("DELETE FROM turns WHERE meeting_id=?", (meeting_id,))
        self.db.execute("DELETE FROM meetings WHERE meeting_id=?", (meeting_id,))
        self.db.execute(
            "INSERT INTO meetings VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (meeting_id, team_id, number, source, content, len(content.split())),
        )
        for turn in turns:
            cur = self.db.execute(
                """INSERT INTO turns(meeting_id,team_id,meeting_number,speaker,timestamp,text,start_offset,end_offset)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (turn.meeting_id, turn.team_id, turn.meeting_number, turn.speaker,
                 turn.timestamp, turn.text, turn.start_offset, turn.end_offset),
            )
            self.db.execute("INSERT INTO turns_fts(rowid,text,meeting_id,team_id,speaker) VALUES(?,?,?,?,?)",
                            (cur.lastrowid, turn.text, turn.meeting_id, turn.team_id, turn.speaker))
        self.db.commit()

    def search(self, query: str, team_id: str | None = None, limit: int = 12) -> list[Turn]:
        tokens = re.findall(r"[A-Za-z0-9_]+", query)
        expanded = []
        for token in tokens:
            if len(token) > 2:
                expanded.append("L_C_D_" if token.casefold() == "lcd" else token)
        terms = " OR ".join(expanded)
        if not terms:
            return []
        sql = """SELECT t.meeting_id, t.team_id, t.meeting_number, t.speaker,
                        t.timestamp, t.text, t.start_offset, t.end_offset
                 FROM turns_fts f JOIN turns t ON t.id=f.rowid
                 WHERE turns_fts MATCH ?"""
        args: list[object] = [terms]
        if team_id:
            sql += " AND t.team_id=?"
            args.append(team_id)
        sql += " ORDER BY bm25(turns_fts) LIMIT ?"
        args.append(limit)
        try:
            rows = self.db.execute(sql, args).fetchall()
        except sqlite3.OperationalError:
            rows = []
        return [Turn(**dict(row)) for row in rows]

    def meetings(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM meetings ORDER BY team_id, meeting_number").fetchall()

    def get_content(self, meeting_id: str) -> str | None:
        row = self.db.execute("SELECT content FROM meetings WHERE meeting_id=?", (meeting_id,)).fetchone()
        return row["content"] if row else None

    def close(self) -> None:
        self.db.close()
