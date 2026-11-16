# Architecture

MeetingMind preserves three memory layers: episodic memory is the original transcript and speaker turns; lexical semantic access is the FTS index; temporal context is represented by meeting sequence and team scope, allowing later meetings to be retrieved alongside earlier ones without overwriting evidence. Every answer is bounded to retrieved turns and citations are verified against raw source content.

The current implementation is intentionally honest about the offline baseline. It does not claim semantic evaluation scores or invented failure cases. Optional LLM synthesis improves phrasing, while retrieval and citation validation remain ordinary Python.
