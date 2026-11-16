import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcripts", default="transcripts")
    parser.add_argument("--meetings", type=int, default=1000)
    args = parser.parse_args()
    files = list(Path(args.transcripts).glob("*.txt"))
    words = sum(len(p.read_text(encoding="utf-8").split()) for p in files)
    average = words / len(files) if files else 0
    estimate = {"observed_meetings": len(files), "observed_words": words,
                "estimated_meetings": args.meetings,
                "estimated_words": round(average * args.meetings),
                "assumptions": ["linear word volume", "local FTS indexing", "LLM and embedding pricing excluded unless configured"],
                "measured_input": "transcripts/*.txt"}
    print(json.dumps(estimate, indent=2))


if __name__ == "__main__":
    main()
