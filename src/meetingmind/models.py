from dataclasses import dataclass, field


@dataclass(frozen=True)
class Turn:
    meeting_id: str
    team_id: str
    meeting_number: int
    speaker: str
    timestamp: str
    text: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class Citation:
    meeting_id: str
    quote: str
    speaker: str | None = None
    timestamp: str | None = None


@dataclass
class Answer:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    evidence: list[Turn] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    confidence: str = "insufficient"
