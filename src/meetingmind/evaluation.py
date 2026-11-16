import json
from pathlib import Path
from .agent import MeetingAgent
from .citations import verify_citation


def answer_questions(agent: MeetingAgent, questions_path: str | Path) -> dict:
    payload = json.loads(Path(questions_path).read_text(encoding="utf-8"))
    answers = []
    for item in payload["questions"]:
        result = agent.ask(item["question"], item.get("team"))
        citations = [{"meeting_id": c.meeting_id, "quote": c.quote} for c in result.citations]
        answers.append({"question_id": item["question_id"], "answer": result.answer,
                        "citations": citations})
    return {"answers": answers, "brief": ""}


def citation_metrics(agent: MeetingAgent, answers: dict) -> dict:
    total = valid = 0
    for item in answers["answers"]:
        for raw in item["citations"]:
            total += 1
            valid += verify_citation(agent.store, type("C", (), raw)())[0]
    return {"citation_count": total, "valid_citations": valid,
            "citation_validity": valid / total if total else 0.0,
            "note": "Answer correctness and support quality require manual review."}
