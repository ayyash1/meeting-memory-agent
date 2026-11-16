# Technical write-up

MeetingMind uses a persistent SQLite memory store with one record per original speaker turn. The parser extracts meeting ID, team, sequence, speaker, timestamp, and character offsets while retaining the untouched transcript. SQLite FTS5 provides bounded lexical retrieval; meeting sequence and team scope provide temporal context without replacing older evidence. Re-ingestion replaces a meeting atomically, making repeated ingestion idempotent.

The workflow is query analysis by tokenization, team-scoped hybrid-ready retrieval, evidence selection, optional LLM wording, and ordinary-Python citation verification. The LLM is optional and cannot create source quotes. The offline fallback is intentionally extractive, which is reliable for provenance but weaker at answering synthesis-heavy questions.

On this machine, all 138 meetings (826,709 whitespace-delimited words and 48,148 speaker turns) indexed in 1.097 seconds with no errors. A linear 1,000-meeting estimate is 5,990,645 words; local indexing has no API embedding cost. Provider/model pricing is not fabricated and must be supplied for an LLM cost projection.

The generated assessment file contains 25 answers and 75/75 mechanically valid citations. This is citation validity, not semantic answer accuracy: semantic support, retrieval recall, and failure categories require manual review. The ten custom questions in `evaluation/custom_questions.json` intentionally remain `needs_manual_review` until a human checks the original transcripts.

For production, add a batched embedding index, queue-based retries, object storage, structured temporal fact extraction, model latency/cost telemetry, and a reviewed answer key. The current system's main limitation is that offline FTS does not reliably resolve paraphrases or multi-hop temporal reasoning without optional LLM synthesis.
