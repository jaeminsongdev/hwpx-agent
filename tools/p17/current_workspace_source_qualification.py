"""Verify the exact current-source successor without rewriting predecessor contracts."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable


def load_acceptance() -> Any:
    path = Path(__file__).resolve().with_name("run_current_workspace_source_checks.py")
    specification = importlib.util.spec_from_file_location(
        "p17_current_workspace_source_acceptance", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("acceptance.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


acceptance = load_acceptance()


ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p17/qualification/current-workspace-source-v9-20260906"
QUALIFICATION = ROOT / BASE
RUN_ID = "bec4941448134e6e99f8b0c4cc393eb3"
BASE_COMMIT = "4be56eaf3f5b5eaf29233ba56f0769e25b99c503"
RECEIPT_SHA256 = "fc8c2fd42fcf38326108f1efb5b2890d6c43eeb19c8a5218935926ee18919f67"
CARGO_METADATA_PROJECTION_SHA256 = (
    "d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d"
)
WORKSPACE_MEMBER_COUNT = 23
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v8-20260906/contract.json",
    "541d7afead5e00d875e0676f69818d868f9b56086148a5f6d09926a799e67eac",
)
IMPLEMENTATION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "path": "crates/hwpx-package/src/lib.rs",
        "bytes": 6737,
        "sha256": "af517aa9b10110d887484d8f14be26ce635896e836c286183a20be29f55ea3f5",
    },
    {
        "path": "crates/hwpx-package/src/vs1_layout.rs",
        "bytes": 41224,
        "sha256": "afe3a9061c5827456f464c8999df07816e6412237477d107c67d0436f53b0292",
    },
    {
        "path": "crates/hwpx-package/tests/vs1_layout.rs",
        "bytes": 2549,
        "sha256": "3a0094752123426c271ed12dfc6bb30a5397f0862f73732cb21795a150062525",
    },
    {
        "path": "crates/hwpx-package/examples/p05_07_dense_column_flow_target_fixture.rs",
        "bytes": 6775,
        "sha256": "d1a151eecd00fa4678ab5dbdb4c7813a659e28c0b991c1dbdbaf6481916085f8",
    },
    {
        "path": "implementation/p05/P05-07_SECTION_COLUMNS_POLICY.md",
        "bytes": 7824,
        "sha256": "6749418b3a8a5c698165e88343a2355bbe810a6bef68beb5ca1e4ae6b3243a10",
    },
    {
        "path": "implementation/p05/P05-07_DENSE_COLUMN_FLOW_POLICY.md",
        "bytes": 5012,
        "sha256": "87db4e5a132d7e7286e5c4a23eb01fabaeb333c057bc1fbe81f04cc4d728698d",
    },
    {
        "path": "implementation/p05/P05-07_DENSE_COLUMN_FLOW_ATTEMPT02.md",
        "bytes": 5329,
        "sha256": "111e6141f18303a75b2a51bf4270d2628fd82828006e22c9175d8da5ff66823d",
    },
    {
        "path": "implementation/p05/qualification/p05-07-dense-attempt02-qualification.json",
        "bytes": 4081,
        "sha256": "a11a32991998b928a6a3faea1d12d76b57f750ab190b1c525e4c040b6b756293",
    },
    {
        "path": "implementation/p05/render-expectations/p05-07-dense-column-flow.json",
        "bytes": 1580,
        "sha256": "6ca7926efb1b9e6f9c1c8b0b5cce97cb8ae69ae91640b1bcc3cdbc62f67d0ad3",
    },
    {
        "path": "implementation/p05/tools/verify_p05_hancom_pdf.py",
        "bytes": 29680,
        "sha256": "5e35f27b5d58cc5c11119725a3506cdd6afa19d45cdd5228f572f55dd3d075f2",
    },
    {
        "path": "implementation/p05/tests/test_verify_p05_hancom_pdf.py",
        "bytes": 12310,
        "sha256": "d3cd7f9d253113ed74085060a3f3506d76383d37fbb4fd4a1ca63798b84231b7",
    },
    {
        "path": "crates/hwpx-package/examples/p05_09_vs1_layout_target_fixture.rs",
        "bytes": 5348,
        "sha256": "e47f7f3502203dcc77853a46bff8d8591436348a78744b2691c4b70d74fa8876",
    },
    {
        "path": "implementation/p05/P05-08_ATTEMPT01_02_DIAGNOSTIC.md",
        "bytes": 3587,
        "sha256": "fad2f3036afd47af21ce12af448fdd92369e2f3bcdaa2750f0d11e8b873067ac",
    },
    {
        "path": "implementation/p05/P05-09_VS1_LAYOUT_POLICY.md",
        "bytes": 2644,
        "sha256": "82a9ac8ae87cb1f73e10eaf147fd1af3d8cf97b23ee2bf3712afbe855e5a7a52",
    },
    {
        "path": "implementation/p05/render-expectations/p05-09-vs1-layout.json",
        "bytes": 928,
        "sha256": "eec108ed9bcc0cb15c6634db9a340d944cc305cdcfe5b428a0ccf076d8f845a8",
    },
    {
        "path": "crates/hwpx-package/src/header_footer.rs",
        "bytes": 67813,
        "sha256": "a5e8fb915d1334aaa802ad09b2c1bbad66a4a3e3fd718ea1c373f5933ace732f",
    },
    {
        "path": "crates/hwpx-package/tests/header_footer.rs",
        "bytes": 23371,
        "sha256": "6ec0a7c23d0846612b3dc56bcd91ed970abc65adcf6f5b06beedfd20a0519ad9",
    },
    {
        "path": "crates/hwpx-package/examples/p05_08_header_footer_target_fixture.rs",
        "bytes": 20367,
        "sha256": "a14151e6d7ed923ddd38c841167d7d5e6c92866c0dbabfb37aff53a9fdb8b31d",
    },
    {
        "path": "implementation/p05/P05-08_HEADER_FOOTER_POLICY.md",
        "bytes": 5007,
        "sha256": "f4ce9064b30de8e939b9153b80da314e0492693eee8564704dffb6b60bc9dc8c",
    },
    {
        "path": "implementation/p05/P05-08_NUMERIC_PARAGRAPH_ID_REPAIR.md",
        "bytes": 3656,
        "sha256": "2b1783165951ce54ab7994ae83be2632d2372268703792e2e1b0bb218d4b8bf3",
    },
    {
        "path": "crates/local-sync/src/lib.rs",
        "bytes": 39692,
        "sha256": "72972e8c12d2203e49fdc7de3987e1c1e45d59911924af0353959dbb35b09ea0",
    },
    {
        "path": "crates/local-sync/src/main.rs",
        "bytes": 16273,
        "sha256": "0ef7421689d888c565fc3619b931c708907b3314d303e725f66dd887b70695fb",
    },
    {
        "path": "crates/local-sync/tests/state_machine.rs",
        "bytes": 20704,
        "sha256": "07821c15027d77b138ea4f8f37c74b9162b5255059db1f280d41b036a989f65e",
    },
    {
        "path": "crates/local-sync/tests/durable_remote.rs",
        "bytes": 16032,
        "sha256": "23bcddc58583ebb390ac0776dd54684ce58e52a93f7fb7bfb7f53480935bc0d5",
    },
    {
        "path": "crates/local-sync/tests/cli.rs",
        "bytes": 12528,
        "sha256": "5ae19c12b2abbceb3f34d8d5ee6ac5e5a9cf35e5e7d10935b0f3fd16c9a976e4",
    },
    {
        "path": "protocol/private/p17-local-conflict-resolver-v1.json",
        "bytes": 2511,
        "sha256": "c932ff45888865adfc25ad7500d6a51f9e87d2f9f4b37d54d42ec41a0dcb9199",
    },
    {
        "path": "implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V1.md",
        "bytes": 2377,
        "sha256": "61980228a0bb48d15be28a4ab1d0fc28259eadfee45f3b99bbc871bd98c277c8",
    },
    {
        "path": "web/plugin-widget/scripts/build-continuity-widget.mjs",
        "bytes": 3651,
        "sha256": "6fbd5601929e84c45a7de8c0ad1122d7ab1917b6b9c2c0e500e50d2dbe2c6d5c",
    },
    {
        "path": "web/plugin-widget/src/continuity-component.tsx",
        "bytes": 2930,
        "sha256": "eb2fc1b4e352c76f3d4854824425281c55067f7339d7ce0a7ec9b69d037fe064",
    },
    {
        "path": "web/plugin-widget/src/continuity-controller.test.ts",
        "bytes": 16489,
        "sha256": "4290b6fc4bbb13642eb1b497da196df526b956f9c025ee996b31b5a164d8781a",
    },
    {
        "path": "web/plugin-widget/src/continuity-controller.ts",
        "bytes": 21528,
        "sha256": "467e66139f48d2287b768718938627f800f7316029934b9640666306168fe72b",
    },
    {
        "path": "web/plugin-widget/src/continuity-model.test.ts",
        "bytes": 8200,
        "sha256": "c76a29a76294831725005bd3c4c7a4df3e2895499adb839bc24fa3accad5f094",
    },
    {
        "path": "web/plugin-widget/src/continuity-model.ts",
        "bytes": 24463,
        "sha256": "b3f480324909f3c4ba009e09b1457025410a9d27912a5c93b6f6387b8806e12b",
    },
    {
        "path": "web/plugin-widget/src/continuity-preview.tsx",
        "bytes": 3012,
        "sha256": "f19afeed48e9d5fccfd76c0a3d3f88f679495635a072d8ae6f3a12a432b8c8cb",
    },
    {
        "path": "web/plugin-widget/src/continuity-resource.test.ts",
        "bytes": 4672,
        "sha256": "becc4cd32f74b0a711a9564ab0bb5d2eba7d242163b314b3f5518726c3a400f6",
    },
    {
        "path": "web/plugin-widget/src/continuity-resource.ts",
        "bytes": 10606,
        "sha256": "4a57767e6a6e1b392f72a42e935ffc5c53ca9ecf8eb715eed50b08c2e9a3b305",
    },
    {
        "path": "web/plugin-widget/src/continuity-styles.css",
        "bytes": 10432,
        "sha256": "326a966f08020a6492b91a8d9803e01c8b165e16d1bfe5c32d710a4e36781b6c",
    },
    {
        "path": "web/plugin-widget/src/continuity-ui.test.tsx",
        "bytes": 5674,
        "sha256": "5846d9c9cbbeae4a519d850b050a8fb633e95bef592e4b2d9ccbe55efd346fb4",
    },
    {
        "path": "web/plugin-widget/src/continuity-ui.tsx",
        "bytes": 27068,
        "sha256": "c6f6dcffb0349ff548bc6813ad7982994de5a9491372075d7bdf235beb628f92",
    },
    {
        "path": "web/plugin-widget/src/continuity-v2-e2e-host.ts",
        "bytes": 8181,
        "sha256": "09683e8e3f05b2ca27c6a6b3fcb86f71abb1c8780734ab69fe5ef89ad1dc027b",
    },
    {
        "path": "tools/p17/run_stale_head_widget_e2e.py",
        "bytes": 5738,
        "sha256": "36be58eddae2f657c51c3189de4b13ee27981ce93f07ec22eb18c6d001977ce1",
    },
    {
        "path": "tools/p17/stale_head_widget.py",
        "bytes": 10806,
        "sha256": "16b474b5082517c4697d2d9c24b30fd82f853d52e9cfb23a7ca1b291e901d0c2",
    },
    {
        "path": "tools/p17/tests/test_stale_head_widget.py",
        "bytes": 2176,
        "sha256": "8c36fbb43874d6540a7fead64607132ec1ad40d9829dea89a0632a9152b8b58e",
    },
    {
        "path": "protocol/migrations/p17-continuity-v1-to-v2.md",
        "bytes": 1708,
        "sha256": "0f49483bfbd64d1a7192978c75f129bf22f92a7c3e9234640f244c8e468b9ba8",
    },
    {
        "path": "protocol/private/p17-stale-head-widget-v1.json",
        "bytes": 2605,
        "sha256": "f4c5765927ca110b2907b26015698a0039327980c1c9958c99f2a92cfcdf607c",
    },
    {
        "path": "implementation/p17/P17-07_STALE_HEAD_WIDGET_V2.md",
        "bytes": 2761,
        "sha256": "e5d5dac479061a1f2b66748ad101946217ef7a25e8cc712aa5917f4cefe19364",
    },
    {
        "path": "implementation/p17/p17-stale-head-widget-contract-v1.json",
        "bytes": 5484,
        "sha256": "10b6b4ee473bd7712c626fdfbed6c93f01208e368831e42376ea5152285edc43",
    },
    {
        "path": "crates/local-sync/src/adapter.rs",
        "bytes": 11682,
        "sha256": "af3b2a4cb9ca73744e9dbbe13ad77953126ff2c725744162bb3d0dbd1d6e03fe",
    },
    {
        "path": "crates/local-sync/tests/remote_adapter.rs",
        "bytes": 9998,
        "sha256": "984e5ecd44ece7a8a7c4161a45c76838f82552ce1afafc4c3bb4f645059cf36b",
    },
    {
        "path": "protocol/private/p17-remote-sync-adapter-v2.json",
        "bytes": 2141,
        "sha256": "05c7d2c7dc7f35a4cf10ca39d221bc588d583cdbb1cc3c303438c2123298ec11",
    },
    {
        "path": "protocol/migrations/p17-remote-sync-request-v1-to-v2.md",
        "bytes": 925,
        "sha256": "94f20b57fb0430a4a9589cead802680cf93fa1b164e842ea1bb066c8192ed28f",
    },
    {
        "path": "implementation/p17/P17-06_MIRROR_BINDING_V4.md",
        "bytes": 1481,
        "sha256": "51ca4df4fd651837e3850984ac106e67dd9f27b7351e2109f36026fb52a5f5c1",
    },
)
SUCCESSORS: tuple[dict[str, Any], ...] = (
    {
        "accepted_predecessor_sha256s": [
            "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
            "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
        ],
        "composition_predecessor_sha256": "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
        "current_sha256": "49e39ae27dd47faaf20c79ad154c930cf515721d84a5fd3659bf14d41366e6a3",
        "path": "Cargo.lock",
    },
    {
        "accepted_predecessor_sha256s": [
            "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03"
        ],
        "composition_predecessor_sha256": "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03",
        "current_sha256": "8d48d90ef0f432236cc89a288bc0803ec9cd228d5b7183a4360f6609f53d7a9e",
        "path": "Cargo.toml",
    },
    {
        "accepted_predecessor_sha256s": [
            "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
        ],
        "composition_predecessor_sha256": "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa",
        "current_sha256": "7f44605e82a9b8a290961553fc2993b8d7209003d2c55157258d80f7e36e5cb6",
        "path": "crates/artifact-service/src/store/postgres_repository.rs",
    },
    {
        "accepted_predecessor_sha256s": [
            "2c510c70ceca388d0858f0a0e887b84fcbde64d7b2b24cc266d377ec9fc04f63"
        ],
        "composition_predecessor_sha256": "2c510c70ceca388d0858f0a0e887b84fcbde64d7b2b24cc266d377ec9fc04f63",
        "current_sha256": "bed1fcd842f320c3f8df11a80458df94007e9dd86125421fbcb6e48cdc09ca42",
        "path": "crates/mcp-control-plane/Cargo.toml",
    },
    {
        "accepted_predecessor_sha256s": [
            "92a8fe6aad98619ad106f4d037d4002d1049078a07fc2e3d85fa5e0c4fc661dc"
        ],
        "composition_predecessor_sha256": "92a8fe6aad98619ad106f4d037d4002d1049078a07fc2e3d85fa5e0c4fc661dc",
        "current_sha256": "3d066f53a353552e5c1d66c891c7ca2167b92fd07bcdb84f29737513c14e1864",
        "path": "crates/mcp-control-plane/src/lib.rs",
    },
    {
        "accepted_predecessor_sha256s": [
            "ba4d49cc2326c4fc7f43c71396eccbeaf48fcb2f8cf586b6f5e0f2507fd8c3f9"
        ],
        "composition_predecessor_sha256": "ba4d49cc2326c4fc7f43c71396eccbeaf48fcb2f8cf586b6f5e0f2507fd8c3f9",
        "current_sha256": "034eecd9cb64d7b072a4096d320d7f53ff8cfb86c797a44edabeceb5e745d5f9",
        "path": "pnpm-lock.yaml",
    },
    {
        "accepted_predecessor_sha256s": [
            "43fc5f526597d08eecac720674ed0c3cb039d146dd28c48c62ecf62c16b1f775"
        ],
        "composition_predecessor_sha256": "43fc5f526597d08eecac720674ed0c3cb039d146dd28c48c62ecf62c16b1f775",
        "current_sha256": "e8e122e48d97694af7bc59738e96c886795e16d3c50f90b51af6a682c1836400",
        "path": "tools/p16/integrated_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "6e3ba421f4c0d5f34b8123e918892bf52fca1f11e0263349e8bb59462863bd21",
            "e4c424920bcc040f1f1ea9aaac3e624eb1478866e9d9458dbe75b778bb2cbd5f",
        ],
        "composition_predecessor_sha256": "e4c424920bcc040f1f1ea9aaac3e624eb1478866e9d9458dbe75b778bb2cbd5f",
        "current_sha256": "70b04f9edd7c0d7ef88b09f82ca399663dc7d0aa74d1536ca6876114720a89bc",
        "path": "tools/p16/p15_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "8fa11f1137591c18d8160985687ab1e6f9e27d83495424cb7158fd68cb4a5f3a"
        ],
        "composition_predecessor_sha256": "8fa11f1137591c18d8160985687ab1e6f9e27d83495424cb7158fd68cb4a5f3a",
        "current_sha256": "7ecaa4939b0bacc92d3eb0c6c69e9610069193604d7a9f942314d8f80f3ea332",
        "path": "tools/p16/run_postgres_artifact_checks.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "9ad0c151c7d63bb5067395463522946d86bf656da8d3805623155c4df054a397"
        ],
        "composition_predecessor_sha256": "9ad0c151c7d63bb5067395463522946d86bf656da8d3805623155c4df054a397",
        "current_sha256": "c4e12a506a5bbf6cab74bb27a7eea6737147b8fe878118c7570c270e1ce7bd8e",
        "path": "tools/p16/tests/test_integrated_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "483c22b852742df6a9c55b3f80bb26425b58e70cf9fe16195a01f3479886160b",
            "76ac1f16b8d0ce831eaaccd0d91f74d6dc601f3d58fc2868a8674761922a1fdd",
        ],
        "composition_predecessor_sha256": "76ac1f16b8d0ce831eaaccd0d91f74d6dc601f3d58fc2868a8674761922a1fdd",
        "current_sha256": "ff77693dc9c309f4f44f2ad9c885fb73862eeb87b1f87d3e284cbf5045fcfc2f",
        "path": "tools/p16/tests/test_p15_source_qualification.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "b3067b75185437f712b9a3b8c0d4ea22fe467d6d4936c1a99834c0a63d03d56a"
        ],
        "composition_predecessor_sha256": "b3067b75185437f712b9a3b8c0d4ea22fe467d6d4936c1a99834c0a63d03d56a",
        "current_sha256": "a1cf888bf867637d087abc8dd37640a167949bf2c98f81fb02b68b8a733fbe5c",
        "path": "tools/p16/tests/test_postgres_artifact_checks.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "599197fa02f6f2c9d3ff08efd72db417fcd70becab5544abdf013d4b859d9ded"
        ],
        "composition_predecessor_sha256": "599197fa02f6f2c9d3ff08efd72db417fcd70becab5544abdf013d4b859d9ded",
        "current_sha256": "f0fde73e5e506e5ea46daef3acd1fa265df4719c3d08fdeeb0071c2e44bd25d6",
        "path": "tools/p16/validate_widget_shell_successor.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "d87b6ea4737a76bec765d492a34b21839f791af6d3df12aa62e18ca29197f343"
        ],
        "composition_predecessor_sha256": "d87b6ea4737a76bec765d492a34b21839f791af6d3df12aa62e18ca29197f343",
        "current_sha256": "abcd83a904cf0501e0c466d218a498025e4541ef93a21136fccda8536b754f0e",
        "path": "web/plugin-widget/scripts/build-widget.mjs",
    },
)
CLAIMS = {
    "source_qualification_only": True,
    "p05_diagnostic_dependencies_bound": True,
    "p05_identity_rebinding_sources_bound": True,
    "p05_dense_flow_sources_bound": True,
    "p05_dense_actual_receipt_bound": True,
    "p05_header_footer_failed_attempts_bound": True,
    "p05_header_footer_numeric_paragraph_id_repair_bound": True,
    "p05_vs1_coordinate_gate_sources_bound": True,
    "p17_local_conflict_resolver_bound": True,
    "p17_stale_head_widget_v2_bound": True,
    "p17_remote_sync_mirror_binding_v2_bound": True,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "phase_complete": False,
}
GUARD_SOURCES = (
    "tools/p17/run_current_workspace_source_checks.py",
    "tools/p17/current_workspace_source_qualification.py",
    "tools/p17/tests/test_current_workspace_source_qualification.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V9.md",
)
HEX = re.compile(r"[0-9a-f]{64}\Z")


class QualificationError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 512_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(value, dict), f"{code}.object")
    require(raw == canonical(value), f"{code}.canonical")
    return value


def git_digest(root: Path, revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        timeout=30,
    )
    require(completed.returncode == 0 and 0 < len(completed.stdout) <= 4_000_000, "history.source")
    return hashlib.sha256(completed.stdout).hexdigest()


def source_lock(root: Path, relative: str) -> dict[str, Any]:
    path = acceptance.bounded_file(root, relative)
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def expected_receipt() -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-check/v1",
        "run_id": RUN_ID,
        "scope": "current_pc_source_binding_successor_only",
        "source_commit": BASE_COMMIT,
        "checks": list(acceptance.CHECKS),
        "check_count": len(acceptance.CHECKS),
        "passed": True,
        "decision": "PASS",
        "predecessor_contract_sha256": acceptance.PINNED_CONTRACTS,
        "successors": list(SUCCESSORS),
        "successor_count": len(SUCCESSORS),
        "cargo_metadata_projection_sha256": CARGO_METADATA_PROJECTION_SHA256,
        "cargo_workspace_member_count": WORKSPACE_MEMBER_COUNT,
        "actual_hangul": False,
        "registered_host": False,
        "production": False,
        "other_pc_or_version": False,
        "phase_complete": False,
    }


def validate_receipt(value: dict[str, Any]) -> None:
    expected = expected_receipt()
    require(set(value) == set(expected), "receipt.fields")
    require(value == expected, "receipt.exact")


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/current-workspace-source-runs" / RUN_ID / "receipt.json"


def expected_current(root: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v9",
        "scope": "current_pc_source_binding_successor_only",
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "predecessor_contract_sha256": acceptance.PINNED_CONTRACTS,
        "successors": list(SUCCESSORS),
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "cargo_metadata_projection_sha256": CARGO_METADATA_PROJECTION_SHA256,
        "cargo_workspace_member_count": WORKSPACE_MEMBER_COUNT,
        "claims": CLAIMS,
        "receipt": {
            "path": f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v9",
        "qualification_id": "p17.current-workspace-source.v9.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_source_binding_successor_only",
        "claims": CLAIMS,
        "predecessors": [
            {"path": relative, "sha256": expected}
            for relative, expected in acceptance.PINNED_CONTRACTS.items()
        ]
        + [{"path": PREVIOUS_QUALIFICATION[0], "sha256": PREVIOUS_QUALIFICATION[1]}],
        "implementation_sources": list(IMPLEMENTATION_SOURCES),
        "evidence": {
            "path": f"{BASE}/current-host.json",
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / BASE
    current_path = directory / "current-host.json"
    current = load_document(current_path, "current")
    contract = load_document(directory / "contract.json", "contract")
    require(current == expected_current(root), "current.exact")
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verified_successors(
    root: Path = ROOT,
    history_digest: Callable[[str, str], str] | None = None,
) -> dict[str, dict[str, Any]]:
    verify(root)
    result: dict[str, dict[str, Any]] = {}
    for entry in SUCCESSORS:
        relative = entry.get("path")
        current = entry.get("current_sha256")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(current, str)
            and HEX.fullmatch(current) is not None
            and isinstance(accepted, list)
            and accepted == sorted(set(accepted))
            and all(isinstance(value, str) and HEX.fullmatch(value) is not None for value in accepted)
            and isinstance(composition, str)
            and composition in accepted,
            "successor.shape",
        )
        path = acceptance.bounded_file(root, relative)
        require(digest(path) == current, "successor.current")
        historical = (
            git_digest(root, BASE_COMMIT, relative)
            if history_digest is None
            else history_digest(BASE_COMMIT, relative)
        )
        require(historical == current, "successor.history")
        result[relative] = dict(entry)
    require(result, "successor.empty")
    return result


def validate_implementation_sources(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in IMPLEMENTATION_SOURCES:
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in result
            and isinstance(expected_bytes, int)
            and expected_bytes > 0
            and isinstance(expected_sha256, str)
            and HEX.fullmatch(expected_sha256) is not None,
            "implementation.shape",
        )
        path = acceptance.bounded_file(root, relative)
        require(
            path.stat().st_size == expected_bytes
            and digest(path) == expected_sha256
            and git_digest(root, BASE_COMMIT, relative) == expected_sha256,
            "implementation.identity",
        )
        result[relative] = dict(entry)
    require(result, "implementation.empty")
    return result


def verified_implementation_sources(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    verify(root)
    return validate_implementation_sources(root)


def verification_paths(root: Path = ROOT) -> set[str]:
    del root
    return {
        f"{BASE}/current-host.json",
        f"{BASE}/contract.json",
        *acceptance.PINNED_CONTRACTS,
        *(entry["path"] for entry in SUCCESSORS),
        *(entry["path"] for entry in IMPLEMENTATION_SOURCES),
        *GUARD_SOURCES,
    }


def qualify() -> tuple[Path, Path]:
    receipt = load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    require(digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")
    validate_implementation_sources(ROOT)
    verified_successors_from_receipt = {entry["path"]: entry for entry in receipt["successors"]}
    require(len(verified_successors_from_receipt) == len(SUCCESSORS), "receipt.successors")
    for entry in SUCCESSORS:
        require(verified_successors_from_receipt.get(entry["path"]) == entry, "receipt.successor")
        require(git_digest(ROOT, BASE_COMMIT, entry["path"]) == entry["current_sha256"], "history.source")
    for entry in IMPLEMENTATION_SOURCES:
        require(
            git_digest(ROOT, BASE_COMMIT, entry["path"]) == entry["sha256"],
            "history.implementation",
        )
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: current_workspace_source_qualification.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: current_workspace_source_qualification.py RUN_ID|verify")
