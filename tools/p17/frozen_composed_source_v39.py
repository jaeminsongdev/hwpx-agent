"""Compose exact v12, P15, and v20-v39 source-successor evidence."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_history_v1 as history  # noqa: E402
from tools.p17 import frozen_current_source_v39 as anchor  # noqa: E402
from tools.p17 import frozen_source_successor_pairs_v1 as pairs  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
LEGACY_LOCK_CONTRACTS: tuple[tuple[str, str, int, str], ...] = (
    (
        "implementation/p15/p15-auth-tenant-v1.json",
        "8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9",
        3511,
        "7bae38b349e394b53636462fe19cb8e1c057a35ab68e7c23161086af6400ad99",
    ),
    (
        "implementation/p15/p15-handler-contract-v1.json",
        "9e7ed73524be0049292fbdf45f2170df6f997fae",
        3739,
        "f79dfeac599b11a122569e1796d428298f341f53f91d3893460c6d7c1d704f0a",
    ),
    (
        "implementation/p15/p15-async-job-contract-v1.json",
        "4c6224f6001c5daadaaaec907c0bba86db7c6c0f",
        5003,
        "311e9272373da0129693ad87c8a42e1e6c56b17b34ccb1312eed630b7f049c32",
    ),
    (
        "implementation/p15/p15-artifact-delivery-contract-v1.json",
        "dde79ff3fa86953c7f3e6e8e2402479eddee813e",
        7147,
        "df025b658d49991f80b392a8afa693c412ef14ad5e90c770356956405c7e42a5",
    ),
    (
        "implementation/p15/p15-error-mapping-contract-v1.json",
        "f36a07e988558b4481c50955a0f76bd69c516d9d",
        6674,
        "ae33d499350ca53f55534744036fc5830e4748efe943482b90c9e063bf54bd8b",
    ),
    (
        "implementation/p15/p15-quota-contract-v1.json",
        "e15921a59d45056c46b8ae94b6f6af778746c534",
        8570,
        "787f88e79b0b1aa1dff483237cf60e9a30526ab686481ec779fe04a3cd3db872",
    ),
    (
        "implementation/p15/p15-telemetry-contract-v1.json",
        "9f9c6932518175906842a2cbb5915a0fb96d0d49",
        7730,
        "9a0e32959a6129f316f609069e87e22f22fb68b11622935c7ca32c080f44e402",
    ),
    (
        "implementation/p15/p15-inspector-staging-contract-v1.json",
        "7ea2f84c244fe5bbd7926ba3f176dc5acafcf624",
        6658,
        "09335ea42021c782f75010d7e873de11c36c834bb33ba8cafde529f824e3b907",
    ),
    (
        "implementation/p16/p16-widget-shell-contract-v1.json",
        "19d1cf775e5702e1150e35624bf616f1dbf9a34c",
        13758,
        "2d8dad6318bc9090b0a7db70d19f1470e6ce0fa97bb177755cff993f9b94f09e",
    ),
)


class FrozenComposedSourceError(ValueError):
    """Fail-closed composed immutable-source error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenComposedSourceError(code)


def root_key(root: Path) -> str:
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise FrozenComposedSourceError("root") from error
    require(resolved.is_dir(), "root")
    return str(resolved)


def parse_json(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenComposedSourceError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    if not isinstance(value, dict):
        raise FrozenComposedSourceError(f"{code}.object")
    return value


@lru_cache(maxsize=4)
def _frozen_edges(root_text: str) -> dict[str, frozenset[tuple[str, str]]]:
    root = Path(root_text)
    contract = pairs.locked_json(
        root,
        pairs.P15_CONTRACT_RELATIVE,
        pairs.P15_CONTRACT_BYTES,
        pairs.P15_CONTRACT_SHA256,
        "p15.contract",
    )
    contexts = contract.get("contexts")
    require(isinstance(contexts, dict), "p15.contexts")
    if not isinstance(contexts, dict):
        raise FrozenComposedSourceError("p15.contexts")
    edges: dict[str, set[tuple[str, str]]] = {}
    for context in pairs.P15_CONTEXTS:
        entries = contexts.get(context)
        require(isinstance(entries, list), "p15.context")
        if not isinstance(entries, list):
            raise FrozenComposedSourceError("p15.context")
        locks: list[dict[str, str]] = []
        for entry in entries:
            relative = entry.get("path") if isinstance(entry, dict) else None
            predecessor = (
                entry.get("predecessor_sha256") if isinstance(entry, dict) else None
            )
            require(
                isinstance(relative, str) and isinstance(predecessor, str),
                "p15.entry",
            )
            if not isinstance(relative, str) or not isinstance(predecessor, str):
                raise FrozenComposedSourceError("p15.entry")
            locks.append({"path": relative, "sha256": predecessor})
        for relative, pair in pairs.p15_context_replacements(
            root, locks, context
        ).items():
            edges.setdefault(relative, set()).add(pair)

    v12_targets = pairs.v12_source_hashes(root)
    v12_current = pairs.locked_json(
        root,
        pairs.V12_CURRENT_RELATIVE,
        pairs.V12_CURRENT_BYTES,
        pairs.V12_CURRENT_SHA256,
        "v12.current",
    )
    successors = v12_current.get("successors")
    require(isinstance(successors, list) and len(successors) == 14, "v12.successors")
    if not isinstance(successors, list):
        raise FrozenComposedSourceError("v12.successors")
    for entry in successors:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "path",
                "accepted_predecessor_sha256s",
                "composition_predecessor_sha256",
                "current_sha256",
            },
            "v12.successor.shape",
        )
        relative = entry.get("path") if isinstance(entry, dict) else None
        accepted = (
            entry.get("accepted_predecessor_sha256s")
            if isinstance(entry, dict)
            else None
        )
        composition = (
            entry.get("composition_predecessor_sha256")
            if isinstance(entry, dict)
            else None
        )
        current = entry.get("current_sha256") if isinstance(entry, dict) else None
        require(
            isinstance(relative, str)
            and isinstance(accepted, list)
            and len(accepted) > 0
            and accepted == sorted(set(accepted))
            and all(
                isinstance(value, str) and HEX64.fullmatch(value) is not None
                for value in accepted
            )
            and isinstance(composition, str)
            and composition in accepted
            and isinstance(current, str)
            and HEX64.fullmatch(current) is not None
            and v12_targets.get(relative) == current,
            "v12.successor.identity",
        )
        if not isinstance(relative, str) or not isinstance(current, str):
            raise FrozenComposedSourceError("v12.successor.identity")
        require(
            anchor.digest(anchor.git_blob(root, pairs.V12_BASE_COMMIT, relative))
            == current,
            "v12.successor.history",
        )
        if not isinstance(accepted, list):
            raise FrozenComposedSourceError("v12.successor.identity")
        for predecessor in accepted:
            if not isinstance(predecessor, str):
                raise FrozenComposedSourceError("v12.successor.identity")
            edges.setdefault(relative, set()).add((predecessor, current))

    anchor.verify_commit(root, pairs.V12_BASE_COMMIT)
    anchor.require_ancestor(root, pairs.V12_BASE_COMMIT, anchor.QUALIFICATION_COMMIT)
    legacy_states: dict[str, list[tuple[str, str]]] = {}
    previous_contract_commit: str | None = None
    for relative, commit, expected_bytes, expected_sha256 in LEGACY_LOCK_CONTRACTS:
        anchor.verify_commit(root, commit)
        anchor.require_ancestor(root, commit, pairs.V12_BASE_COMMIT)
        if previous_contract_commit is not None:
            anchor.require_ancestor(root, previous_contract_commit, commit)
        previous_contract_commit = commit
        raw = anchor.git_blob(root, commit, relative, 512_000)
        require(len(raw) == expected_bytes, "legacy.contract.bytes")
        require(anchor.digest(raw) == expected_sha256, "legacy.contract.digest")
        source_locks = parse_json(raw, "legacy.contract").get("source_locks")
        require(
            isinstance(source_locks, list) and len(source_locks) > 0,
            "legacy.source_locks",
        )
        if not isinstance(source_locks, list):
            raise FrozenComposedSourceError("legacy.source_locks")
        contract_paths: set[str] = set()
        for source_lock in source_locks:
            require(
                isinstance(source_lock, dict)
                and set(source_lock) == {"path", "sha256"},
                "legacy.source_lock.shape",
            )
            source_relative = (
                source_lock.get("path") if isinstance(source_lock, dict) else None
            )
            predecessor = (
                source_lock.get("sha256") if isinstance(source_lock, dict) else None
            )
            require(
                isinstance(source_relative, str)
                and source_relative not in contract_paths
                and isinstance(predecessor, str)
                and HEX64.fullmatch(predecessor) is not None,
                "legacy.source_lock.identity",
            )
            if not isinstance(source_relative, str) or not isinstance(predecessor, str):
                raise FrozenComposedSourceError("legacy.source_lock.identity")
            contract_paths.add(source_relative)
            anchor.validate_relative_path(source_relative)
            require(
                anchor.digest(anchor.git_blob(root, commit, source_relative))
                == predecessor,
                "legacy.source_lock.history",
            )
            legacy_states.setdefault(source_relative, []).append((commit, predecessor))

    last_qualified: dict[str, str] = {}
    for relative, states in legacy_states.items():
        previous: str | None = None
        for _, current in states:
            if previous is not None and previous != current:
                edges.setdefault(relative, set()).add((previous, current))
            previous = current
        if previous is not None:
            last_qualified[relative] = previous

    for relative, target in v12_targets.items():
        predecessor = last_qualified.get(relative)
        if predecessor is not None and predecessor != target:
            require(
                anchor.digest(anchor.git_blob(root, pairs.V12_BASE_COMMIT, relative))
                == target,
                "v12.legacy_target.history",
            )
            edges.setdefault(relative, set()).add((predecessor, target))
        last_qualified[relative] = target

    for version in range(history.FIRST_VERSION, history.LAST_VERSION + 1):
        state: dict[str, str] = {}
        for relative, entry in history.verified_implementation_sources(
            root, version
        ).items():
            current = entry.get("sha256")
            require(
                isinstance(current, str) and HEX64.fullmatch(current) is not None,
                "history.implementation",
            )
            if not isinstance(current, str):
                raise FrozenComposedSourceError("history.implementation")
            state[relative] = current
        successors_by_path = history.verified_successors(root, version)
        for relative, entry in successors_by_path.items():
            current = entry.get("current_sha256")
            require(
                isinstance(current, str)
                and HEX64.fullmatch(current) is not None
                and (relative not in state or state[relative] == current),
                "history.successor",
            )
            if not isinstance(current, str):
                raise FrozenComposedSourceError("history.successor")
            state[relative] = current
        for relative, current in state.items():
            predecessor = last_qualified.get(relative)
            if predecessor is not None and predecessor != current:
                edges.setdefault(relative, set()).add((predecessor, current))
            last_qualified[relative] = current

        for relative, entry in successors_by_path.items():
            current = entry.get("current_sha256")
            accepted = entry.get("accepted_predecessor_sha256s")
            require(
                isinstance(current, str) and isinstance(accepted, list),
                "history.entry",
            )
            if not isinstance(current, str) or not isinstance(accepted, list):
                raise FrozenComposedSourceError("history.entry")
            for predecessor in accepted:
                require(isinstance(predecessor, str), "history.predecessor")
                if not isinstance(predecessor, str):
                    raise FrozenComposedSourceError("history.predecessor")
                edges.setdefault(relative, set()).add((predecessor, current))

    return {relative: frozenset(values) for relative, values in edges.items()}


@lru_cache(maxsize=2_048)
def _verified_target(
    root_text: str,
    relative: str,
    predecessor: str,
) -> str:
    root = Path(root_text)
    anchor.validate_relative_path(relative)
    require(HEX64.fullmatch(predecessor) is not None, "predecessor")
    edges = set(_frozen_edges(root_text).get(relative, ()))
    target = anchor.digest(anchor.git_blob(root, anchor.QUALIFICATION_COMMIT, relative))
    reachable = {predecessor}
    while True:
        expanded = reachable | {after for before, after in edges if before in reachable}
        if expanded == reachable:
            break
        reachable = expanded
    require(target in reachable, "chain.unreachable")
    return target


def verified_target(
    root: Path,
    relative: str,
    predecessor: str,
) -> str:
    require(isinstance(relative, str), "path")
    require(isinstance(predecessor, str), "predecessor")
    return _verified_target(root_key(root), relative, predecessor)


def clear_cache() -> None:
    _verified_target.cache_clear()
    _frozen_edges.cache_clear()


if __name__ == "__main__":
    raise SystemExit("library-only immutable verifier")
