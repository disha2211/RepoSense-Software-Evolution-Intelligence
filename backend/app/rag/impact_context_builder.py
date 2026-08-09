from typing import Any


class ImpactContextBuilder:

    @staticmethod
    def build(
        seed: dict[str, Any],
        context: dict[str, Any],
    ) -> str:

        lines = [
            "REPOSITORY IMPACT CONTEXT",
            "",
            f"Target ID: {seed.get('id')}",
            f"Target Name: {seed.get('name')}",
            f"Target Type: {seed.get('seed_type')}",
            f"Semantic Score: {seed.get('score')}",
            "",
        ]

        if context.get("target_summary"):
            lines.append(
                f"Target Summary: {context['target_summary']}"
            )

        declaring = context.get("declaring_class")

        if declaring:
            lines.append(
                f"Declaring Class: {declaring.get('name')}"
            )

        dependencies = context.get("dependencies") or []

        if dependencies:
            lines.append("")
            lines.append("DIRECT DEPENDENCIES:")

            for item in dependencies:
                lines.append(
                    f"- {item['name']} "
                    f"[{item['relationship']}]"
                )

        dependents = context.get("dependents") or []

        if dependents:
            lines.append("")
            lines.append("DIRECT DEPENDENTS:")

            for item in dependents:
                lines.append(
                    f"- {item['name']} "
                    f"[{item['relationship']}]"
                )

        methods = context.get("methods") or []

        if methods:
            lines.append("")
            lines.append("DECLARED METHODS:")

            for item in methods:
                lines.append(
                    f"- {item['name']}"
                )

        return "\n".join(lines)