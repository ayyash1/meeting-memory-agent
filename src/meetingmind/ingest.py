import re
import time
from pathlib import Path
from .models import Turn
from .store import Store

HEADER = re.compile(r"Meeting:\s*(\S+).*?Team:\s*(\S+).*?Meeting number:\s*(\d+)", re.S)
TURN = re.compile(r"(?m)^(?P<timestamp>\d{2}:\d{2}:\d{2}) (?P<speaker>Speaker [A-D])\s*$")


def parse_transcript(path: str | Path) -> tuple[str, str, int, str, list[Turn]]:
    source = Path(path)
    content = source.read_text(encoding="utf-8")
    meta = HEADER.search(content[:1500])
    if not meta:
        raise ValueError(f"Missing AMI metadata header: {source}")
    meeting_id, team_id, number = meta.group(1), meta.group(2), int(meta.group(3))
    markers = list(TURN.finditer(content))
    turns: list[Turn] = []
    for index, marker in enumerate(markers):
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(content)
        text = re.sub(r"\s+", " ", content[start:end]).strip()
        if text:
            turns.append(Turn(meeting_id, team_id, number, marker.group("speaker"),
                              marker.group("timestamp"), text, start, end))
    return meeting_id, team_id, number, content, turns


def ingest_directory(directory: str | Path, store: Store) -> dict:
    started = time.perf_counter()
    files = sorted(Path(directory).glob("*.txt"))
    errors: list[str] = []
    written = 0
    for path in files:
        try:
            meeting_id, team_id, number, content, turns = parse_transcript(path)
            store.replace_meeting(meeting_id, team_id, number, str(path), content, turns)
            written += len(turns)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
    elapsed = time.perf_counter() - started
    return {"files_seen": len(files), "turns_written": written, "errors": errors,
            "seconds": round(elapsed, 3), "words": sum(len(r["content"].split()) for r in store.meetings())}
