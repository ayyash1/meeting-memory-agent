import os
from .citations import verify_citation
from .models import Answer, Citation, Turn
from .store import Store


class MeetingAgent:
    """Bounded retrieval and synthesis. LLM use is optional and never owns citations."""

    def __init__(self, store: Store):
        self.store = store

    def retrieve(self, question: str, team_id: str | None = None) -> list[Turn]:
        return self.store.search(question, team_id=team_id, limit=16)

    def ask(self, question: str, team_id: str | None = None) -> Answer:
        evidence = self.retrieve(question, team_id)
        trace = [f"FTS lexical retrieval scoped to {team_id or 'all teams'}",
                 f"Retrieved {len(evidence)} speaker turns",
                 "Citation verifier checks exact source text before returning"]
        if not evidence:
            return Answer("I could not find sufficient transcript evidence.", [], [], trace, "insufficient")
        citations: list[Citation] = []
        for turn in evidence:
            quote = " ".join(turn.text.split()[:45])
            candidate = Citation(turn.meeting_id, quote, turn.speaker, turn.timestamp)
            if verify_citation(self.store, candidate)[0] and candidate not in citations:
                citations.append(candidate)
            if len(citations) == 3:
                break
        answer = self._synthesize(question, evidence, citations)
        confidence = "high" if len({c.meeting_id for c in citations}) >= 2 else "medium" if citations else "insufficient"
        return Answer(answer, citations, evidence[:8], trace, confidence)

    def _synthesize(self, question: str, evidence: list[Turn], citations: list[Citation]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                context = "\n".join(f"[{t.meeting_id} {t.speaker}] {t.text}" for t in evidence[:10])
                response = OpenAI(api_key=api_key).chat.completions.create(
                    model=os.getenv("MEETINGMIND_MODEL", "gpt-4o-mini"),
                    temperature=0,
                    messages=[{"role": "system", "content":
                        "Answer concisely from evidence only. Do not invent facts or citations."},
                              {"role": "user", "content": f"Question: {question}\nEvidence:\n{context}"}],
                )
                return response.choices[0].message.content or self._extractive(evidence)
            except Exception:
                pass
        return self._extractive(evidence)

    @staticmethod
    def _extractive(evidence: list[Turn]) -> str:
        snippets = [" ".join(t.text.split()[:32]) for t in evidence[:2]]
        return "Evidence found in the transcripts: " + " ".join(snippets)
