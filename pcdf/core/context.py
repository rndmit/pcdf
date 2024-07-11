from dataclasses import dataclass

from ksuid import Ksuid


@dataclass(frozen=True)
class SystemInfo:
    version: str
    framework_version: str

    def labels(self) -> dict[str, str]:
        return {
            "progressive-cd.io/version": f"{self.version}t-{self.framework_version}f",
        }


@dataclass(frozen=True)
class RunInfo:
    id: str = Ksuid().__str__()

    def labels(self) -> dict[str, str]:
        return {"progressive-cd.io/last-run-id": self.id}

@dataclass
class Context():
    system: SystemInfo
    values: dict[str, str]

    def with_values(self, values: dict[str, str]) -> "Context":
        return Context(
            system=self.system,
            values=self.values | values,
        )

    def with_run_info(self, ri: RunInfo) -> "RunContext":
        return RunContext(
            system=self.system,
            run=ri,
            values=self.values,
        )

@dataclass
class RunContext(Context):
    run: RunInfo

    def with_values(self, values: dict[str, str]) -> "RunContext":
        return RunContext(
            system=self.system,
            run=self.run,
            values=self.values | values,
        )
