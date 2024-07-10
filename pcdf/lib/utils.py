from .datamodel import Metadata


def default_labels(metadata: Metadata) -> dict[str, str]:
    return {
        "app.kubernetes.io/instance": f"{metadata.name}@{metadata.namespace}",
        "app.kubernetes.io/name": metadata.name,
        "app.kubernetes.io/part-of": metadata.project,
        "app.kubernetes.io/component": metadata.type,
        "app.kubernetes.io/managed-by": "progressive-cd",
    }
