from typing import Any


class HistoricalContextBuilder:
    """
    Converts historical graph retrieval results into
    deterministic context for the LLM.
    """

    @staticmethod
    def build(
        question: str,
        class_ids: list[str],
        events: list[dict[str, Any]],
    ) -> str:

        lines = [
            "REPOSITORY HISTORICAL CONTEXT",
            "",
            f"Question: {question}",
            "",
            "Relevant Class IDs:",
        ]

        for class_id in class_ids:
            lines.append(
                f"- {class_id}"
            )

        lines.extend(
            [
                "",
                "CHRONOLOGICAL COMMIT HISTORY:",
                "",
            ]
        )

        for index, event in enumerate(events, start=1):

            lines.append(
                f"EVENT {index}"
            )

            lines.append(
                f"Commit: {event.get('commit_hash')}"
            )

            lines.append(
                f"Timestamp: {event.get('timestamp')}"
            )

            lines.append(
                f"Author: {event.get('author')}"
            )

            lines.append(
                f"Message: {event.get('message')}"
            )

            intent = event.get("intent")

            lines.append(
                f"Intent: {intent or 'Not available'}"
            )

            affected_files = (
                event.get("affected_files") or []
            )

            if affected_files:
                lines.append(
                    "Affected Files: "
                    + ", ".join(affected_files)
                )
            else:
                lines.append(
                    "Affected Files: None available"
                )

            lines.append("")

        return "\n".join(lines)