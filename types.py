from typing import Any, TypedDict


class RobotProcessResultBase(TypedDict):
    ok: bool


class RobotProcessResult(RobotProcessResultBase, total=False):
    error: str
    result: Any
    payload: Any
