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
BASE = "implementation/p17/qualification/current-workspace-source-v16-20260907"
QUALIFICATION = ROOT / BASE
RUN_ID = "748e74afe46042f5889955c182301a68"
BASE_COMMIT = "64421c631236ce975529851d70e1324640a99ad9"
RECEIPT_SHA256 = "97db71a7446c15e1ea275777636e031f82d8e45b8f8bef213584decf3338df61"
CARGO_METADATA_PROJECTION_SHA256 = (
    "d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856"
)
WORKSPACE_MEMBER_COUNT = 25
PREVIOUS_QUALIFICATION = (
    "implementation/p17/qualification/current-workspace-source-v15-20260907/contract.json",
    "f7b7922b12a2891e33fae1adbefe36565e7918e8535b4037f276058f3d901384",
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
        "bytes": 44568,
        "sha256": "54c256c2d958cfd6aa43b42881d42f487c8d46edfc393da36d233d409fb56f7e",
    },
    {
        "path": "crates/local-sync/src/main.rs",
        "bytes": 16471,
        "sha256": "9f104d841783b9bee242188e72b68c4aa171ac06f697e94c44b567b9f176ce07",
    },
    {
        "path": "crates/local-sync/tests/state_machine.rs",
        "bytes": 24364,
        "sha256": "161d7735f154b3a1f1ba3837b90e533b0d33da7f20a4b11117b6d5af47225caa",
    },
    {
        "path": "crates/local-sync/tests/durable_remote.rs",
        "bytes": 17965,
        "sha256": "9694ab58edbf80f3015533288fccb070b4522305f892078ca315717945947e5c",
    },
    {
        "path": "crates/local-sync/tests/cli.rs",
        "bytes": 13936,
        "sha256": "fdadb4ba651d3c6bec7f2ac524333a91c51a8344ab9c17ee66426b4f0bfe516a",
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
        "bytes": 12700,
        "sha256": "abe7316285d99a44ad6e19d548637782c712710bc803dbfcfd19a7d4e5131b52",
    },
    {
        "path": "crates/local-sync/tests/remote_adapter.rs",
        "bytes": 12029,
        "sha256": "bbc49abc5f15bd92e73342e48fc98797d2752af4180deb46ba0d0b3cd41f5d88",
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
    {
        "path": "crates/local-sync/src/store.rs",
        "bytes": 18376,
        "sha256": "590b2bd6f7579c4705ca786e80ac02f0c5fed249c5bff9bfa767bb9ea718de1f",
    },
    {
        "path": "protocol/private/p17-remote-sync-adapter-v3.json",
        "bytes": 3181,
        "sha256": "7fd7849e1e166ac615288299c0f309efee9233e664b899706d32bbfe3c6d2f70",
    },
    {
        "path": "protocol/migrations/p17-remote-sync-request-v2-to-v3.md",
        "bytes": 1017,
        "sha256": "5cda59d50d52aec5c3b2b7054ae2ce38f0f65bc1dc09170cb48e412ea14fb7d1",
    },
    {
        "path": "protocol/migrations/p17-local-mirror-v4-to-v5.md",
        "bytes": 928,
        "sha256": "ebf7b3d258d0e6e9497b04b136fbfb23bab561b8fa0c535fa09345e2ed19a9d9",
    },
    {
        "path": "protocol/private/p17-local-sync-cli-v4.json",
        "bytes": 3980,
        "sha256": "c9ceb95848c1c814da6d62f013fd284add9f993e437789d5a5b0a2f5f394ba06",
    },
    {
        "path": "protocol/private/p17-local-conflict-resolver-v2.json",
        "bytes": 2498,
        "sha256": "5eef47fec56113b89f89f4b2d002e4076b0ffd2d920e3660ecd29d66e8e7e084",
    },
    {
        "path": "implementation/p17/P17-06_CHECKPOINT_INTENT_BINDING_V5.md",
        "bytes": 1625,
        "sha256": "7ca5cba235f6a1bd954b54167df75e11366fae796a379e7d6d89b5afaa3d53d7",
    },
    {
        "path": "implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V2.md",
        "bytes": 963,
        "sha256": "388d6824c350ae311d1f4e407e16759126c1c9e28eb55aca2c91dc08836d26e0",
    },
    {
        "path": "crates/history-service/src/lib.rs",
        "bytes": 555,
        "sha256": "9abd1a4ac037e2f24b6d0db30feffd280a43c538a582f6afe7f1ce3b4b2d7727",
    },
    {
        "path": "crates/history-service/src/service.rs",
        "bytes": 40591,
        "sha256": "6d8e24785db5fac4c333d189b8115469787fab4374e346fec76d947b20a5eddb",
    },
    {
        "path": "crates/history-service/src/store.rs",
        "bytes": 15976,
        "sha256": "056c66d7c8cb58e20f1591e812ad39ae250fe246c624ef913024bcb16f7fa755",
    },
    {
        "path": "crates/history-service/src/types.rs",
        "bytes": 23665,
        "sha256": "92d44d57e9fbbea26cfcf8a43d3c2a960aa99ba0b18a65a4597e5159092a39d4",
    },
    {
        "path": "crates/local-sync/Cargo.toml",
        "bytes": 490,
        "sha256": "aaf9e02b93d87c8a2c88daf26716a012b8819dee491414d4469284523945fc9d",
    },
    {
        "path": "crates/local-sync/src/service_mapping.rs",
        "bytes": 12668,
        "sha256": "5834b7b4225ace4f61eeecf86048cc28968ef95a7d9b541c2988057f26a3792b",
    },
    {
        "path": "crates/local-sync/src/socket.rs",
        "bytes": 5389,
        "sha256": "6624254419485da3b88ed8457e4237c97d23a2b81f27ec235e8732bba59401d5",
    },
    {
        "path": "crates/local-sync/src/strict_json.rs",
        "bytes": 3097,
        "sha256": "c48079d0382ecf39fd0c5ef0f34649b89536b9a0a9bacb1b9e3d618fdaeb9b15",
    },
    {
        "path": "crates/local-sync/tests/checkpoint_service_mapping.rs",
        "bytes": 9632,
        "sha256": "4f667bb47d61932f7025060d814ce860974af84feed6d880581fac19bafee2e6",
    },
    {
        "path": "crates/remote-sync-host/Cargo.toml",
        "bytes": 936,
        "sha256": "6961157e09817ae082f049404df28e22175a9afd25296781f84ba2f8ba21a161",
    },
    {
        "path": "crates/remote-sync-host/src/lib.rs",
        "bytes": 47583,
        "sha256": "1dcfa7c9a8b132f396a28e4e4083cdc05176e9413d46a6f78e713cd6dc3430f7",
    },
    {
        "path": "crates/remote-sync-host/src/socket.rs",
        "bytes": 6192,
        "sha256": "0bd85d5ca862ba5f639040c89e8e3bdc82aeea6e3bd01ab2f07710795944704e",
    },
    {
        "path": "crates/remote-sync-wire/Cargo.toml",
        "bytes": 235,
        "sha256": "ff2583279dcab3cc71443ca56c227d87da462df26fc2f3acd3a90a62556c53b3",
    },
    {
        "path": "crates/remote-sync-wire/src/lib.rs",
        "bytes": 8850,
        "sha256": "7bc3919998a6087d8eb9eeea138248716dc63ae5978631dd37cc3abdebb9618b",
    },
    {
        "path": "crates/retention-sync-service/src/lib.rs",
        "bytes": 86708,
        "sha256": "a2882bbf6609edfb39414ce9ef42d132f7334ee8d0d84c03c27586f0ad07e51f",
    },
    {
        "path": "implementation/p17/P17-06_AUTHENTICATED_CHECKPOINT_HOST_V8.md",
        "bytes": 2693,
        "sha256": "f147d110156b70819bcb3bc61177788b384cce3b36253ed3a52e891c18ba3967",
    },
    {
        "path": "implementation/p17/P17-06_AUTHORIZED_MIRROR_ADMISSION_V7.md",
        "bytes": 2084,
        "sha256": "6db4d12e29718db3617d3f49ef79bef7ed5324fcb75c1f283097cc3c0867840d",
    },
    {
        "path": "implementation/p17/P17-06_CHECKPOINT_SERVICE_MAPPING_V6.md",
        "bytes": 2296,
        "sha256": "4d80be5c057faefdc0d48a59bc5e87d1d662f8436ed34ed5a3d352e6f7c13e06",
    },
    {
        "path": "implementation/p17/P17-06_HISTORY_CHECKPOINT_DISPATCH_V9.md",
        "bytes": 2404,
        "sha256": "8492b415efa1cb645ef0c951525e47c0bc0f5d75ac361c63bfade62f46c3f0df",
    },
    {
        "path": "implementation/p17/P17-06_LOOPBACK_TCP_TRANSPORT_V10.md",
        "bytes": 2556,
        "sha256": "bc9c29c13b6ca1df4bd1117c26d3e77a2f1a61deb979f7b5b9c7ff0209dbb5a7",
    },
    {
        "path": "protocol/migrations/p17-checkpoint-authenticated-host-v1.md",
        "bytes": 1325,
        "sha256": "9f34df9ab06743b3786d7c499e4de72db266993e40129add476217bad070b5cb",
    },
    {
        "path": "protocol/migrations/p17-checkpoint-host-admission-v1.md",
        "bytes": 988,
        "sha256": "6a5e70945806f587fe2d8cf7025af00d976bbcd776b7ef7c631d9275e2a0d057",
    },
    {
        "path": "protocol/migrations/p17-checkpoint-service-mapping-v1.md",
        "bytes": 923,
        "sha256": "47a6069aaa28ac2c14f6a31581e58a39f91bef8ae66bf70ef756d441b76c1261",
    },
    {
        "path": "protocol/migrations/p17-history-checkpoint-dispatch-v1.md",
        "bytes": 1228,
        "sha256": "19a9348ae2dba37945c9ea18f5f34b8369bb38ea320eab768291b9ba4b0ac253",
    },
    {
        "path": "protocol/private/p17-checkpoint-authenticated-host-v1.json",
        "bytes": 2769,
        "sha256": "063f336592a2df2c1134fe48d59ed39338531a37d3e2d99a316986ec89ddea90",
    },
    {
        "path": "protocol/private/p17-checkpoint-host-admission-v1.json",
        "bytes": 1702,
        "sha256": "a22b536966778ea619e000f12e153fe6036df1ed538ce3098398ea51f0b360bc",
    },
    {
        "path": "protocol/private/p17-checkpoint-service-mapping-v1.json",
        "bytes": 3247,
        "sha256": "e651c1de9f00c5b20138ba1b0c91b57e2567a479f41e663bf7f9ca7cfbdb2d2d",
    },
    {
        "path": "protocol/private/p17-history-checkpoint-dispatch-v1.json",
        "bytes": 1947,
        "sha256": "79cfd99e25586e0eea0e5dc5124544ef31d14db66d5ac6096783037fdce6b2a4",
    },
    {
        "path": "crates/mcp-control-plane/src/postgres_plan_review.rs",
        "bytes": 31077,
        "sha256": "ce983cb07a19d6835091dc2a6f4254c33d530060ec25090b4f21a9f8e2edb383",
    },
    {
        "path": "crates/mcp-control-plane/src/postgres_plan_source.rs",
        "bytes": 23339,
        "sha256": "0453647abe8545302d954034b3554d4a1a2853b7e6711329852d9a70ccbf8050",
    },
    {
        "path": "crates/mcp-control-plane/src/postgres_stored_plan.rs",
        "bytes": 42198,
        "sha256": "beb1185bdd364c0b1d3a8f4a8679fcd03b0e93d2cd5b843fbb5de74e579801fa",
    },
    {
        "path": "crates/remote-sync-host/examples/postgres_checkpoint_client.rs",
        "bytes": 3344,
        "sha256": "d7e8288b78a2aec6386cb06810766c6f270f0feab3e98a20d52529f88c5c1e55",
    },
    {
        "path": "crates/remote-sync-host/examples/postgres_checkpoint_host.rs",
        "bytes": 10278,
        "sha256": "b9b908ecc70cc61f268188c963ed2db241776f1d51b41ba00497ba6ab5736330",
    },
    {
        "path": "crates/remote-sync-host/src/postgres.rs",
        "bytes": 24194,
        "sha256": "7e049991583d739872c3b6822bd807741c1f98586142c6702a03f431875f8fce",
    },
    {
        "path": "deny.toml",
        "bytes": 471,
        "sha256": "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
    },
    {
        "path": "implementation/p17/P17-06_POSTGRES_CHECKPOINT_HOST_V11.md",
        "bytes": 4035,
        "sha256": "e5e301a356afd2d97b98f49d6f0e24e13f70cd04824571ddf0ac0ac459b00832",
    },
    {
        "path": "implementation/p17/qualification/postgres-checkpoint-host-v1-20260907/contract.json",
        "bytes": 6535,
        "sha256": "c8b594781c5b05f4d1487c956661a72a3ea93a5cb109186a8aacf9f8f7d08e55",
    },
    {
        "path": "implementation/p17/qualification/postgres-checkpoint-host-v1-20260907/current-host.json",
        "bytes": 5216,
        "sha256": "75c7bc2dfafffa58098160cdaa6729ca728fa8e59e28e490b191d11ee6d3ad40",
    },
    {
        "path": "migrations/postgres/0014_p17_history_checkpoint_note.down.sql",
        "bytes": 1742,
        "sha256": "533a082ce83e0a77b9cd3b71a951a3adeb4df9356caa802490ad2f582086c4c6",
    },
    {
        "path": "migrations/postgres/0014_p17_history_checkpoint_note.up.sql",
        "bytes": 7542,
        "sha256": "d3e8a2846780f9442ea4b3acf55c072a2ba663590e3b24c9e46736517bb4c129",
    },
    {
        "path": "protocol/migrations/p17-postgres-checkpoint-host-v1.md",
        "bytes": 1498,
        "sha256": "d33d5d35b16f9249f7d3602bcc40f5b267a038f89a5d85fe07331827a3dc43b1",
    },
    {
        "path": "protocol/private/p17-postgres-checkpoint-host-v1.json",
        "bytes": 3298,
        "sha256": "899622f73d39c7fc3af18e0922d03762e013fd19bcbab696f1b0255d6bfd250c",
    },
    {
        "path": "tools/p17/fixtures/p17_postgres_checkpoint_setup.sql",
        "bytes": 2946,
        "sha256": "c59c04ba8aa279b60d7901bcbb3394aad587f94cfade1c5b2062aa3507cf1d4d",
    },
    {
        "path": "tools/p17/postgres_checkpoint_host_qualification.py",
        "bytes": 13200,
        "sha256": "b2a658a3046b0df1036f9622f37cbd56e472ba068983ed6702a675b8cea31cad",
    },
    {
        "path": "tools/p17/run_postgres_checkpoint_host_checks.py",
        "bytes": 24927,
        "sha256": "254c37cb56f6ea26e02f12f9de11d758117810a3a37413402b1920ec13dbbef6",
    },
    {
        "path": "tools/p17/tests/test_postgres_checkpoint_host_checks.py",
        "bytes": 7341,
        "sha256": "c6fe2fbb35237b4f9646fbc8b663bb62d8cd080525722d8960c26f252a736094",
    },
    {
        "path": "tools/p17/tests/test_postgres_checkpoint_host_qualification.py",
        "bytes": 2847,
        "sha256": "7501627a4cbb9fcfe74f745c451541b5afaac57a592bc2b0a1e89e23d186f1f1",
    },
    {
        "path": "tools/p14/validate_history_checkpoints_migration.py",
        "bytes": 21357,
        "sha256": "c952f164238e48cddcc1e46ebbfdd4a3503055fe5a6795d67768876d54f00b12",
    },
    {
        "path": "tools/p14/tests/test_history_checkpoints_migration.py",
        "bytes": 5656,
        "sha256": "4095bb67b039a598b4613a6899c00d98bf4ce9766547dc6043fa2eec92599625",
    },
    {
        "path": "tools/p17/frozen_current_source_v12.py",
        "bytes": 7740,
        "sha256": "6355a6290d420d572be4277db1ce3cbc334e2dde719eac6542b033e5d5483294",
    },
    {
        "path": "tools/p17/tests/test_frozen_current_source_v12.py",
        "bytes": 2221,
        "sha256": "c35de80e21c26f6c4ba7ae116ce742669104cf4e92ac4620f88c1d6aba460b20",
    },
    {
        "path": "tools/p17/tests/test_current_workspace_source_checks.py",
        "bytes": 4190,
        "sha256": "49ada14bac45965874c5981abffb0f3ae4bd4a8feb96602392cc525967aefd8f",
    },
    {
        "path": "tools/p17/tests/test_telemetry_source_successor_bridge.py",
        "bytes": 3119,
        "sha256": "b0c0e723a086986f6f7d31743986e94511caaf44d024a632d38f9cce8f55b3a3",
    },
    {
        "path": "tools/p17/frozen_p15_source_v1.py",
        "bytes": 6061,
        "sha256": "e48ab2b77e57827a88662883daeb4aa502ba4abf7cb4951fe91fa6a404989efc",
    },
    {
        "path": "tools/p17/tests/test_frozen_p15_source_v1.py",
        "bytes": 2475,
        "sha256": "d838ad4750c0598eee21071e5e6042c2904822d9b8ae53b69c181187536f95f5",
    },
)
SUCCESSORS: tuple[dict[str, Any], ...] = (
    {
        "accepted_predecessor_sha256s": [
            "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
            "7cb6ea91c65c226f2769af0d33906b39970efa0c81b286aa32ca282ef8614d69",
        ],
        "composition_predecessor_sha256": "6561e43d46f89ee42773840dd33747cfa23bd55b0927f1da41e357bf3b97c639",
        "current_sha256": "180eb9a48c33c51bf1325b824115f40039a064aa94dc200af0dca0f60f43c1ed",
        "path": "Cargo.lock",
    },
    {
        "accepted_predecessor_sha256s": [
            "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03"
        ],
        "composition_predecessor_sha256": "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03",
        "current_sha256": "fc8343046ab7adb7ea9097da370e8fa2fa03ad61c4c0677522abd47d768ffa71",
        "path": "Cargo.toml",
    },
    {
        "accepted_predecessor_sha256s": [
            "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa"
        ],
        "composition_predecessor_sha256": "52f583c2b18d33a009db93ef59127d9cf2b13000e9e83db5bef523c748bc33aa",
        "current_sha256": "994d2a2578a2b9bcfa9fbbf43a113eb54ab21ef01ec3a2ace311b15a90cba96a",
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
            "b18cef25d92231df643cb4c23f7c06508d310aaa1191c014a559e34a67aac36f"
        ],
        "composition_predecessor_sha256": "b18cef25d92231df643cb4c23f7c06508d310aaa1191c014a559e34a67aac36f",
        "current_sha256": "41f8fe1ab6c35d2d4895ba6b320a8d1bd1418c74ff5ee63fc3bd7945a7fb957a",
        "path": "tools/p15/tests/test_inspector_staging_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "2ccf158b9e33f58721c729370d975afe3f1a494b9a53ee0433c4b8f8d598cb14"
        ],
        "composition_predecessor_sha256": "2ccf158b9e33f58721c729370d975afe3f1a494b9a53ee0433c4b8f8d598cb14",
        "current_sha256": "eccaed0edf4cba139020fcf9f124dbaeab43c6c8a7539d5083b1e3c0e6ac086f",
        "path": "tools/p15/validate_artifact_delivery_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "8d1186ec2fe481f4307ebc26efaaaf3b33d9c6d1ed40349d7bbf74c7172a3077"
        ],
        "composition_predecessor_sha256": "8d1186ec2fe481f4307ebc26efaaaf3b33d9c6d1ed40349d7bbf74c7172a3077",
        "current_sha256": "1a80a1a076b0b0697f03c86cd9e834c4c50d256d76b35fdf418a054aebeb12da",
        "path": "tools/p15/validate_async_job_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "73ae4cddb10eb7bb5a0ccb55cdfe5fc95b26cc2ff28d0384b9dcac12387d67a4"
        ],
        "composition_predecessor_sha256": "73ae4cddb10eb7bb5a0ccb55cdfe5fc95b26cc2ff28d0384b9dcac12387d67a4",
        "current_sha256": "7a1aff1bf1afe240989efcaabb391d359f979521b70cc2a803a96580d4bbcf51",
        "path": "tools/p15/validate_error_mapping_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "266af5bf5c4aefe856fb467c20e187cd23eda35dfb12c975e69b211992a51af4"
        ],
        "composition_predecessor_sha256": "266af5bf5c4aefe856fb467c20e187cd23eda35dfb12c975e69b211992a51af4",
        "current_sha256": "86c044ee38112bca4540ec730a1e902d0156632cb1ef3d4f2fcb8bba3e8f3c6a",
        "path": "tools/p15/validate_handler_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "d4370aabc28cc26ac931caaa5ec7172d7a3455e05732026018bec704e684a937",
            "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3",
        ],
        "composition_predecessor_sha256": "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3",
        "current_sha256": "7284a7e92e3b98c6887564d3e5b5418d545ce5ec73b512d568ecf72f92e3dac6",
        "path": "tools/p15/validate_inspector_staging_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "2c558437483847f863732eaef61b13e862e1a47512869ad882e50140d33dd08d"
        ],
        "composition_predecessor_sha256": "2c558437483847f863732eaef61b13e862e1a47512869ad882e50140d33dd08d",
        "current_sha256": "546c54b65c1618ed82f2d4622f326973a2c0918faad3796132853865d3b6d0e9",
        "path": "tools/p15/validate_quota_contract.py",
    },
    {
        "accepted_predecessor_sha256s": [
            "cb4382094bdb41fafaa192e7ff65cb1d2b82740e609f570442efcf9c784bb39f"
        ],
        "composition_predecessor_sha256": "cb4382094bdb41fafaa192e7ff65cb1d2b82740e609f570442efcf9c784bb39f",
        "current_sha256": "0665f5f6016d98f828a5335de2c0638d0ec95757794f517cc12b0489ef5d258f",
        "path": "tools/p15/validate_telemetry_contract.py",
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
        "current_sha256": "c4ce3b37b08989536a25df9dc69e22b4e351d248b8a46891ddf4c01d07f73016",
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
        "current_sha256": "a0387bf67579273dbff364ace6ac485e2ca4a4c0b5a108ff0f62af758073f8ca",
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
    "p17_remote_sync_checkpoint_intent_v3_bound": True,
    "p17_local_mirror_v5_bound": True,
    "p17_checkpoint_service_mapping_v6_bound": True,
    "p17_authorized_mirror_admission_v7_bound": True,
    "p17_authenticated_checkpoint_host_v8_bound": True,
    "p17_history_checkpoint_dispatch_v9_bound": True,
    "p17_loopback_tcp_transport_v10_bound": True,
    "p17_postgres_checkpoint_host_v11_bound": True,
    "docs_source_successor_bridge_v13_bound": True,
    "ambiguous_source_baseline_guard_v13_bound": True,
    "telemetry_source_successor_bridge_v14_bound": True,
    "frozen_p15_source_contexts_v15_bound": True,
    "docs_source_only_widget_validation_v16_bound": True,
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
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V16.md",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v16",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v16",
        "qualification_id": "p17.current-workspace-source.v16.20260907",
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
