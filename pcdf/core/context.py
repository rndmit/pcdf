from typing import Self
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SystemInfo:
    version: str
    framework_version: str

    def labels(self) -> dict[str, str]:
        return {
            "progressive-cd.io/tool-version": self.version,
            "progressive-cd.io/framework-version": self.framework_version,
        }


@dataclass(frozen=True)
class RunInfo:
    id: str

    def labels(self) -> dict[str, str]:
        return {"progressive-cd.io/last-run-id": self.id}


@dataclass(frozen=True)
class Context:
    system: SystemInfo
    run: RunInfo | None = None
    values: dict[str, str] = field(default_factory=dict)

    def with_values(self, values: dict[str, str]) -> "Context":
        return Context(
            system=self.system,
            run=self.run,
            values=self.values | values,
        )

    def with_run_info(self, ri: RunInfo) -> "RunContext":
        return RunContext(
            system=self.system,
            run=ri,
            values=self.values,
        )


@dataclass(frozen=True)
class RunContext(Context):
    run: RunInfo = RunInfo(id="")
