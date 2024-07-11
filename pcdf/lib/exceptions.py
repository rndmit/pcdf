from dataclasses import dataclass


@dataclass
class IncorrectManifestError(Exception):
    entname: str

    def __str__(self) -> str:
        return f"{self.entname} exited because given Deployment manifest is not correct"
