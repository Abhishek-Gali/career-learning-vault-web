"""Query matrix builder for systematic search coverage."""

from qf_app.config.settings import get_queries_data


class QueryMatrixBuilder:
    """Generates cross-product of curriculum topics, domains, services, and search modifiers."""

    def __init__(self, query_data: dict | None = None) -> None:
        self.query_data = query_data or get_queries_data()
        self.intent_modifiers: list[str] = self.query_data.get("intent_modifiers", [
            "practice questions", "exam questions", "quiz questions answers"
        ])
        self.domain_topics: list[dict] = self.query_data.get("domain_topics", [])
        self.services: list[str] = self.query_data.get("services", [])

    def build_query_matrix(self) -> list[str]:
        """Generate full list of unique search queries."""
        queries: set[str] = set()

        # Domain level queries
        for dt in self.domain_topics:
            topic = dt.get("topic", "")
            for mod in self.intent_modifiers[:3]:
                queries.add(f"AWS CLF-C02 {topic} {mod}")

        # Service level queries
        for svc in self.services:
            for mod in self.intent_modifiers[:2]:
                queries.add(f"AWS CLF-C02 {svc} {mod}")

        # Core certification queries
        for mod in self.intent_modifiers:
            queries.add(f"AWS Certified Cloud Practitioner CLF-C02 {mod}")
            queries.add(f"CLF-C02 {mod}")

        return sorted(queries)
