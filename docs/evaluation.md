# Evaluation

Run `python -m meetingmind.cli answer --questions questions.json` and inspect the generated answers. Citation validity is checked by `meetingmind.citations.verify_citation` and covered by tests. Semantic answer accuracy, support quality, retrieval recall, and genuine failure cases require manual review against the supplied transcripts; the system does not manufacture those scores.
