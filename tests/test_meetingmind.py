from meetingmind.citations import verify_citation
from meetingmind.ingest import parse_transcript
from meetingmind.models import Citation
from meetingmind.store import Store


def test_parser_and_exact_citation(tmp_path):
    meeting, team, number, content, turns = parse_transcript("transcripts/TS3012a.txt")
    assert (meeting, team, number) == ("TS3012a", "TS3012", 1)
    store = Store(tmp_path / "test.sqlite3")
    store.replace_meeting(meeting, team, number, "fixture", content, turns)
    assert verify_citation(store, Citation(meeting, turns[0].text))[0]
    assert not verify_citation(store, Citation(meeting, "invented quote with enough words"))[0]


def test_incremental_reingestion_is_idempotent(tmp_path):
    meeting, team, number, content, turns = parse_transcript("transcripts/TS3012a.txt")
    store = Store(tmp_path / "test.sqlite3")
    store.replace_meeting(meeting, team, number, "fixture", content, turns)
    store.replace_meeting(meeting, team, number, "fixture", content, turns)
    assert store.db.execute("SELECT COUNT(*) FROM meetings").fetchone()[0] == 1
    assert store.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == len(turns)
