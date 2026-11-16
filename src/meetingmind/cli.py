import argparse
import json
from pathlib import Path
from .agent import MeetingAgent
from .briefing import generate_brief
from .evaluation import answer_questions
from .ingest import ingest_directory
from .store import Store


def main() -> None:
    parser = argparse.ArgumentParser(prog="meetingmind")
    parser.add_argument("--db", default="data/meetingmind.sqlite3")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest"); p.add_argument("--transcripts", default="transcripts")
    p = sub.add_parser("ask"); p.add_argument("question"); p.add_argument("--team")
    p = sub.add_parser("answer"); p.add_argument("--questions", default="questions.json"); p.add_argument("--output", default="outputs/answers.json")
    p = sub.add_parser("brief"); p.add_argument("--team", default="TS3012"); p.add_argument("--output", default="outputs/brief.md")
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == "ingest":
        print(json.dumps(ingest_directory(args.transcripts, store), indent=2))
    elif args.command == "ask":
        result = MeetingAgent(store).ask(args.question, args.team)
        print(json.dumps({"answer": result.answer, "confidence": result.confidence,
                          "citations": [c.__dict__ for c in result.citations],
                          "trace": result.trace}, indent=2))
    elif args.command == "answer":
        result = answer_questions(MeetingAgent(store), args.questions)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {args.output}")
    elif args.command == "brief":
        result = generate_brief(MeetingAgent(store), args.team)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Wrote {args.output}")
    store.close()


if __name__ == "__main__":
    main()
