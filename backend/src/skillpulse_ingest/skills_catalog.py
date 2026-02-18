from __future__ import annotations

from collections import OrderedDict

# Ordered catalog keeps deterministic extraction output.
SKILL_PATTERNS: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    {
        "Python": (r"\bpython(?:3)?\b",),
        "Java": (r"\bjava\b(?!\s*script)",),
        "JavaScript / TypeScript": (
            r"\bjavascript\b",
            r"\btypescript\b",
            r"\bjs\b",
            r"\bts\b",
        ),
        "Node.js": (r"\bnode(?:\.js|js)?\b",),
        "React": (r"\breact(?:\.js|js)?\b",),
        "Angular": (r"\bangular(?:\.js|js)?\b",),
        "SQL / Databases": (
            r"\bsql\b",
            r"\bpostgres(?:ql)?\b",
            r"\bmysql\b",
            r"\boracle\b",
            r"\bmongodb\b",
            r"\bdynamodb\b",
            r"\brds\b",
            r"\bredis\b",
            r"\bdb2\b",
            r"\bsnowflake\b",
        ),
        "REST APIs": (
            r"\brest(?:ful)?\b",
            r"\brest\s*api(?:s)?\b",
            r"\bweb\s+services?\b",
            r"\bhttp\s+api(?:s)?\b",
        ),
        "Git / Version Control": (
            r"\bgit\b",
            r"\bgithub\b",
            r"\bgitlab\b",
            r"\bsvn\b",
            r"\btortoisesvn\b",
            r"\bmercurial\b",
        ),
        "Docker / Containers": (
            r"\bdocker\b",
            r"\bcontainer(?:s|ization)?\b",
            r"\bkubernetes\b",
            r"\bk8s\b",
            r"\bpodman\b",
        ),
        "AWS": (r"\baws\b", r"\bamazon\s+web\s+services\b"),
        "Terraform": (r"\bterraform\b",),
        "Kubernetes": (r"\bkubernetes\b", r"\bk8s\b"),
        "CI/CD": (
            r"\bci\/?cd\b",
            r"\bjenkins\b",
            r"\bgithub\s+actions\b",
            r"\bcircleci\b",
        ),
        "Go": (
            r"\bgolang\b",
            r"\bgo\b(?=\s+(?:developer|engineer|service|services|microservice|backend|programming))",
        ),
        "C": (
            r"\bc\s+language\b",
            r"\bc\s+developer\b",
            r"\bc\s+programming\b",
        ),
        "C++": (r"\bc\+\+\b",),
        "C#": (r"\bc#\b", r"\bc\s*sharp\b"),
        "Spring": (r"\bspring(?:\s+boot)?\b",),
        "Django": (r"\bdjango\b",),
        "Flask": (r"\bflask\b",),
        "GraphQL": (r"\bgraphql\b",),
        "Redis": (r"\bredis\b",),
        "PostgreSQL": (r"\bpostgres(?:ql)?\b",),
        "MySQL": (r"\bmysql\b",),
    }
)
