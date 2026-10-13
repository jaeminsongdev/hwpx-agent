#!/usr/bin/env python3
"""Fresh public-SDK five-pair inputs for product preparation, NOT native candidates."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
if not __package__: sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_value_public_export as prior
ROOT=prior.ROOT
OUTPUT="fixtures/target-build/p09-42-product-form-values-01/output"


def prepare():
    destination=ROOT/OUTPUT
    prior.oracle.no_links(ROOT/"fixtures/target-build")
    if not destination.parent.exists(): destination.parent.mkdir(exist_ok=False)
    prior.oracle.no_links(destination.parent)
    if destination.exists(): raise ValueError("product_fixture_output_already_exists")
    with tempfile.TemporaryDirectory(prefix="p09-40-component-",dir=ROOT/"fixtures/target-build") as first, tempfile.TemporaryDirectory(prefix="p09-40-component-",dir=ROOT/"fixtures/target-build") as second:
        a,b=prior.generate(Path(first)),prior.generate(Path(second))
        prior.oracle.require(a==b,"product_fixture_fresh_generations_differ")
        files={p.name:prior.oracle.checked_bytes(p,1024*1024) for p in Path(first).iterdir()}
        prior.oracle.require(len(files)==11 and sum(map(len,files.values()))==167304,"product_fixture_inventory")
        destination.mkdir(parents=True,exist_ok=False)
        for name,raw in sorted(files.items()):
            prior.oracle.require(Path(name).name==name and name.endswith((".hwpx",".json")),"product_fixture_name")
            with (destination/name).open("xb") as stream: stream.write(raw)
        prior.oracle.require(prior.oracle.inspect_bundle(Path(first))==a["independent_oracle"],"product_fixture_original_changed")
        actual={p.name:prior.oracle.checked_bytes(p,1024*1024) for p in destination.iterdir()}
        prior.oracle.require(actual==files,"product_fixture_copy_identity")
    return {"state":"pass","files":11,"bytes":167304,"manifest_sha256":a["independent_oracle"]["manifest_sha256"],"two_fresh_public_generations_exact":True,"scope":"product_preparation_only_not_native_candidate","native_session_started":False}


if __name__=="__main__":
    print(json.dumps(prepare()))
