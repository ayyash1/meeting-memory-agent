from pathlib import Path
from .agent import MeetingAgent
from .briefing import generate_brief
from .ingest import ingest_directory
from .store import Store


def create_app(db_path: str = "data/meetingmind.sqlite3"):
    from fastapi import FastAPI
    from pydantic import BaseModel
    store = Store(db_path)
    agent = MeetingAgent(store)
    app = FastAPI(title="MeetingMind", version="0.1.0")

    class AskRequest(BaseModel):
        question: str
        team_id: str | None = None

    class IngestRequest(BaseModel):
        transcripts: str = "transcripts"

    @app.get("/health")
    def health():
        return {"status": "ok", "meetings": len(store.meetings())}

    @app.post("/ingest")
    def ingest(request: IngestRequest):
        return ingest_directory(request.transcripts, store)

    @app.post("/ask")
    def ask(request: AskRequest):
        result = agent.ask(request.question, request.team_id)
        return {"answer": result.answer, "confidence": result.confidence,
                "citations": [c.__dict__ for c in result.citations],
                "evidence": [t.__dict__ for t in result.evidence], "trace": result.trace}

    @app.post("/brief")
    def brief(team_id: str = "TS3012"):
        return {"team_id": team_id, "brief": generate_brief(agent, team_id)}

    return app
