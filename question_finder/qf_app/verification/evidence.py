"""Official AWS documentation evidence generator."""

from pydantic import BaseModel

# Curated reference mapping for AWS in-scope services and concepts
AWS_DOC_REFERENCES = {
    "Amazon S3": {
        "url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
        "title": "Amazon Simple Storage Service Documentation",
        "concept": "Object storage built to retrieve any amount of data from anywhere.",
    },
    "Amazon EC2": {
        "url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
        "title": "Amazon Elastic Compute Cloud Documentation",
        "concept": "Secure and resizable compute capacity in the cloud.",
    },
    "AWS Lambda": {
        "url": "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
        "title": "AWS Lambda Developer Guide",
        "concept": "Serverless, event-driven compute service.",
    },
    "Amazon RDS": {
        "url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html",
        "title": "Amazon Relational Database Service User Guide",
        "concept": "Managed relational database service for MySQL, PostgreSQL, Oracle, SQL Server.",
    },
    "Amazon DynamoDB": {
        "url": "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html",
        "title": "Amazon DynamoDB Developer Guide",
        "concept": "Fast, flexible NoSQL database service for single-digit millisecond performance.",
    },
    "AWS IAM": {
        "url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
        "title": "AWS Identity and Access Management User Guide",
        "concept": "Securely manage access to AWS services and resources with least privilege.",
    },
    "Amazon VPC": {
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
        "title": "Amazon Virtual Private Cloud User Guide",
        "concept": "Logically isolated virtual network for AWS resources.",
    },
    "AWS CloudTrail": {
        "url": "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html",
        "title": "AWS CloudTrail User Guide",
        "concept": "Track user activity and API usage across AWS infrastructure.",
    },
    "Amazon CloudWatch": {
        "url": "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html",
        "title": "Amazon CloudWatch User Guide",
        "concept": "Monitoring and observability service for AWS resources and applications.",
    },
    "AWS Trusted Advisor": {
        "url": "https://docs.aws.amazon.com/awssupport/latest/user/trusted-advisor.html",
        "title": "AWS Trusted Advisor User Guide",
        "concept": "Real-time guidance to help provision resources following AWS best practices.",
    },
    "AWS Shield": {
        "url": "https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html",
        "title": "AWS Shield DDoS Protection Developer Guide",
        "concept": "Managed Distributed Denial of Service (DDoS) protection service.",
    },
    "AWS WAF": {
        "url": "https://docs.aws.amazon.com/waf/latest/developerguide/what-is-aws-waf.html",
        "title": "AWS WAF Developer Guide",
        "concept": "Web application firewall that helps protect web applications from common web exploits.",
    },
}


class EvidenceItem(BaseModel):
    """Citation snippet and supporting URL."""

    source_url: str
    source_title: str
    supporting_text: str
    confidence: float = 1.0


class EvidenceGatherer:
    """Collects authoritative AWS documentation evidence based on services mentioned."""

    def find_evidence(self, services: list[str], stem: str) -> list[EvidenceItem]:
        """Find official AWS citations relevant to the services in the question."""
        items: list[EvidenceItem] = []
        for svc in services:
            for known_name, ref in AWS_DOC_REFERENCES.items():
                if known_name.lower() in svc.lower() or svc.lower() in known_name.lower():
                    items.append(
                        EvidenceItem(
                            source_url=ref["url"],
                            source_title=ref["title"],
                            supporting_text=f"{known_name}: {ref['concept']}",
                            confidence=0.95,
                        )
                    )
                    break

        if not items:
            for known_name, ref in AWS_DOC_REFERENCES.items():
                if known_name.lower() in stem.lower():
                    items.append(
                        EvidenceItem(
                            source_url=ref["url"],
                            source_title=ref["title"],
                            supporting_text=f"{known_name}: {ref['concept']}",
                            confidence=0.90,
                        )
                    )
                    break

        if not items:
            items.append(
                EvidenceItem(
                    source_url="https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html",
                    source_title="AWS Overview & Core Concepts Whitepaper",
                    supporting_text="Authoritative AWS Cloud Practitioner (CLF-C02) foundation curriculum definition.",
                    confidence=0.85,
                )
            )
        return items
