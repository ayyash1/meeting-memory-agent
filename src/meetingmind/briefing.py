from .agent import MeetingAgent


def generate_brief(agent: MeetingAgent, team_id: str) -> str:
    rows = agent.store.db.execute(
        "SELECT meeting_id, meeting_number FROM meetings WHERE team_id=? ORDER BY meeting_number",
        (team_id,)).fetchall()
    lines = [f"# {team_id} pre-meeting brief", "", "This brief is generated from verified transcript evidence.",
             "", "## Meetings consulted"]
    lines.extend(f"- {row['meeting_id']} (meeting {row['meeting_number']})" for row in rows)
    for topic in ("decision budget cost", "action owner follow up", "disagreement risk final design"):
        result = agent.ask(topic, team_id)
        lines += ["", f"## Evidence: {topic}", result.answer]
        for citation in result.citations:
            lines.append(f'- {citation.meeting_id} ({citation.speaker}, {citation.timestamp}): "{citation.quote}"')
    return "\n".join(lines) + "\n"
