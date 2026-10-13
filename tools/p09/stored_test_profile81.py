"""Exact retained test-only81 config entries, with no historical runner imports.

실제 실패 build002의 선언 recipe/config에 byte-exact 대응을 별도로 확인한다.
이 데이터만으로 compiler catalog나 runtime/Gate PASS를 주장하지 않는다.
"""
PACKAGES=("hwpx-package","hwpx-agent-cli","serde_json","sha2","quick-xml","zip","flate2","zlib-rs",
          "aead","aes","aes-gcm","cipher","ctr","ghash","polyval","universal-hash")
SETTINGS=(("opt-level","1"),("debug-assertions","true"),("overflow-checks","true"),
          ("codegen-units","16"),("debug",'"line-tables-only"'))


def expected():
    entries=tuple(f"profile.test.package.{package}.{key}={value}" for package in PACKAGES for key,value in SETTINGS)
    return (*entries[:10],'profile.test.lto="off"',*entries[10:])


CONFIG=expected()


def config_contract(entries):
    if not (type(entries) is tuple and entries==expected() and len(entries)==81
            and len({entry.split("=",1)[0] for entry in entries})==81):
        raise ValueError("CURRENT_STORED_EXACT_OPTIMIZED_PROFILE_REQUIRED")
