"""SQL host freshness and checked watcher shutdown; never changes DB/security policy."""
from build_current_issuer_probe import CurrentCompilerResources as SQLRuntimeResources
import os
from owned_sql_job import OwnedSQLJobFactory, factory_require

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-sql-runtime-watch-cleanup/source-preimages.v1.json"
SOURCES = ["tools/p09/sql_runtime_supervision.py", "tools/p09/tests/test_sql_runtime_supervision.py",
    "tools/p09/tests/sql_runtime_driver_delta.py", ARCHIVE,
    "implementation/p09/source-archive/p09-149-pre-explicit-local-sql-endpoint/source-preimages.v1.json"]
LOCAL_DOCKER_HOST = "npipe:////./pipe/dockerDesktopLinuxEngine"
ENDPOINT_ENV = ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")


def local_docker_arguments(args, docker):
    factory_require(isinstance(args, (list, tuple)) and args and all(isinstance(arg, str) for arg in args),
        "OWNED_SQL_LOCAL_ARGUMENT_SCOPE")
    if args[0] != docker:
        return args
    factory_require(len(args) >= 2 and args[1] in {"version", "info", "inspect", "image", "exec", "run", "rm"},
        "OWNED_SQL_LOCAL_COMMAND_SCOPE")
    factory_require(not any(arg in {"--host", "-H", "--context", "--config"}
        or arg.startswith(("--host=", "--context=", "--config=")) or arg.startswith("-H") for arg in args[1:]),
        "OWNED_SQL_LOCAL_ENDPOINT_OVERRIDE")
    return [docker, "--host", LOCAL_DOCKER_HOST, *args[1:]]


def local_docker_environment(env=None):
    scoped = dict(os.environ if env is None else env)
    for name in ENDPOINT_ENV:
        scoped.pop(name, None)
    return scoped


class LocalDockerJobFactory(OwnedSQLJobFactory):
    """Keep primary7%/observer1%; bind only Docker to explicit local npipe."""
    def __init__(self, **kwargs):
        allowed = kwargs.get("allowed_executables")
        factory_require(isinstance(allowed, (list, tuple)) and len(allowed) == 3,
            "OWNED_SQL_LOCAL_EXECUTABLE_SCOPE")
        self.docker = allowed[0]
        super().__init__(**kwargs)

    def __call__(self, args, **kwargs):
        actual = local_docker_arguments(args, self.docker)
        if args[0] == self.docker:
            kwargs["env"] = local_docker_environment(kwargs.get("env"))
        return super().__call__(actual, **kwargs)


def finish_watcher(resources, receipt):
    # Container cleanup must still run on a watcher failure. Never raise here or
    # turn an alive/failed watcher into a successful product receipt.
    resources.done.set()
    complete = False
    try:
        if resources.thread.ident is not None:
            resources.thread.join(timeout=3)
        complete = not resources.thread.is_alive()
    except (OSError, RuntimeError):
        complete = False
    receipt["resource_watcher_cleanup_confirmed"] = complete
    if not complete:
        resources._failed("STOP_RESOURCE_WATCHER_CLEANUP_FAILED")
        receipt["state"] = "FAIL_CLOSED"
    return complete
