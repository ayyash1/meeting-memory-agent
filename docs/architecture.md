# MeetingMind: Architecture and Production Assessment

## Architecture

MeetingMind is an evidence-grounded meeting-memory system for the AMI Meeting Corpus. Its central design choice is to preserve the transcript as the source of truth rather than storing only generated summaries. During ingestion, each transcript is parsed into meeting metadata and speaker turns containing the meeting ID, team ID, meeting sequence, speaker, timestamp, original text, and character offsets. The untouched transcript is retained alongside those turns so that every answer can be traced back to the source.

The current memory design has three practical layers. **Episodic memory** is the original transcript and its speaker turns. **Search memory** is a SQLite FTS5 index over those turns, supporting bounded lexical retrieval instead of placing the entire corpus in a prompt. **Temporal context** is represented by team scope and meeting sequence, allowing earlier and later meetings to be compared without overwriting prior evidence. Re-ingestion replaces the records for a meeting, which makes the pipeline repeatable and prevents duplicate chunks.

The answering workflow is deliberately bounded: retrieve relevant turns, select source evidence, optionally synthesize a concise answer, and verify citations before returning the result. The API exposes the answer, citations, retrieved evidence, confidence, and a short retrieval trace; it does not expose private chain-of-thought. Citation verification is ordinary Python. It checks that the meeting exists and that each quote of at least six words appears in the original transcript, with whitespace normalization to tolerate formatting differences.

## Model versus code

Code owns deterministic operations: file discovery, metadata parsing, turn extraction, offsets, persistence, FTS querying, team filtering, duplicate prevention, citation verification, and output formatting. These operations need repeatability and auditability, so delegating them to a language model would introduce unnecessary failure modes.

The model is optional and limited to answer wording. If `OPENAI_API_KEY` is configured, retrieved evidence can be supplied to an LLM to produce a more concise response. The model is instructed to use evidence only, but it is not trusted to create citations. If no API key is available, MeetingMind falls back to an extractive answer. This is less fluent and weaker for multi-hop reasoning, but it remains honest and usable offline. The project therefore avoids pretending that a keyword retriever has semantic understanding or that unreviewed answers are benchmark scores.

For the supplied assessment, the generated output contains 25 answers and 75 mechanically valid citations. That is a provenance result, not a claim of semantic correctness: answer quality, retrieval recall, and genuine failure cases still require human review against the transcripts.

## Tools used and where they broke

The implementation uses Python, the standard library, SQLite, SQLite FTS5, `pytest`, `setuptools`, and optional FastAPI/OpenAI integrations. SQLite was chosen for the baseline because it is persistent, portable, dependency-light, and sufficient for 138 meetings. The CLI supports ingestion, question answering, briefing generation, and scale estimation.

Several practical issues shaped the implementation. The environment used Python 3.10 rather than the initially recommended 3.11, so the package requirement was set to Python 3.10+ without using newer language features. The first FTS query implementation used an invalid table alias in `MATCH` and returned no results; tests and live smoke queries exposed the issue, which was corrected and followed by successful multi-meeting retrieval. The corpus also writes “LCD” in transcript form as `L_C_D_`, so retrieval needed a small deterministic query expansion for that domain-specific spelling.

The largest functional limitation is lexical retrieval. Exact terms work well, but paraphrases, implicit references, and multi-hop temporal questions can be missed. No embedding service was added to the offline baseline, and no semantic answer scores were invented. The optional LLM improves synthesis but cannot compensate for evidence that retrieval never found.

## What production would need

At real scale, the SQLite baseline should be replaced or complemented by durable object storage for raw transcripts, a relational metadata store, and a managed hybrid search layer combining BM25 with batched embeddings. Ingestion should run through a queue with idempotency keys, retry policies, dead-letter handling, and per-file checkpoints. Embeddings and extraction should be batched and rate-limited, with model, token, latency, and cost telemetry recorded for every job.

Temporal memory also needs to become an explicit, reviewed data model: decisions, proposals, confirmations, revisions, owners, actions, completion status, supersession links, and uncertainty should all retain source evidence. Retrieval should use query decomposition, reranking, meeting chronology, contradiction detection, and a bounded evidence budget. Production serving would additionally require authentication, tenant isolation, secrets management, structured logs, tracing, health checks, dashboards, backups, retention policies, and load testing.

The observed corpus indexed locally in about 1.1 seconds with 138 files and 48,148 speaker turns. A linear 1,000-meeting estimate is approximately 6.0 million words. That estimate is useful for sizing storage and throughput, but real production cost depends on the selected embedding and LLM providers, batching, concurrency, retries, and traffic patterns; those costs should be measured from provider pricing rather than guessed.
