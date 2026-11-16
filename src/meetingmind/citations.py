import re
from .models import Citation
from .store import Store


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def verify_citation(store: Store, citation: Citation, min_words: int = 6) -> tuple[bool, str]:
    if len(citation.quote.split()) < min_words:
        return False, "quote has fewer than six words"
    content = store.get_content(citation.meeting_id)
    if content is None:
        return False, "meeting does not exist"
    if _norm(citation.quote) not in _norm(content):
        return False, "quote is not present verbatim"
    return True, "verified"


def verify_all(store: Store, citations: list[Citation]) -> list[str]:
    return [reason for citation in citations if not (ok := verify_citation(store, citation))[0]
            for reason in [f"{citation.meeting_id}: {ok[1]}"]]
