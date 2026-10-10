#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""HyperSkills 测试 VM 管理：构建镜像、自检、在一次性 microVM 里用 pi 跑提示词。

    uv run tools/vm.py build                      # docker 构建并导入 msb
    uv run tools/vm.py verify --services          # VM 内工具与服务自检
    uv run tools/vm.py run --skill office "..."   # 一次性 VM，只挂载 office skill
    uv run tools/vm.py run "..."                  # 不挂载任何 skill（基线）
    uv run tools/vm.py shell                      # 常驻开发 VM，交互式 pi
    uv run tools/vm.py clean                      # 删除本工具创建的全部 sandbox

VM 里没有宿主的 agent 配置、AGENTS.md、skill 目录或凭据：模型密钥经 msb `--secret`
以占位符注入，只在发往模型 API 主机的请求里被替换成真实值。详见 vm/README.md。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import SkillLoadError, repo_root, resolve_targets  # noqa: E402

IMAGE = "hyperskills-vm:latest"
# 宿主侧可选配置文件（已 gitignore）；环境变量优先于文件。
LOCAL_ENV = "vm/local.env"
KEY_ENV = "ANTHROPIC_API_KEY"
BASE_URL_ENV = "HS_VM_ANTHROPIC_BASE_URL"
DEFAULT_API_URL = "https://api.anthropic.com"
# 与 tools/run_evals.py 一致：同一模型与思考档，VM 内外结果才可比。
DEFAULT_MODEL = "anthropic/claude-opus-5"
DEFAULT_THINKING = "medium"
THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")
DEFAULT_OUT_ROOT = Path("/tmp/hs-vm-runs")
DEFAULT_TIMEOUT_S = 900
DEFAULT_CPUS = 4
DEFAULT_MEMORY = "8G"
DEFAULT_ROOT_DISK = "32G"
DEV_SANDBOX = "hs-dev"
# 所有由本工具创建的 sandbox 都带这个标签，clean 按它清理。
LABEL = "project=hyperskills"
GUEST_HOME = "/home/agent"
GUEST_PI_DIR = f"{GUEST_HOME}/.pi/agent"
GUEST_SKILLS = "/opt/hyperskills/skills"
GUEST_WORKSPACE = "/workspace"
# msb 做 TLS 拦截（secret 替换靠它）时把自己的 CA 写进系统证书包，同时设置
# NODE_EXTRA_CA_CERTS=/.msb/tls/ca.pem；但该路径只有 root 可读，以 agent 身份运行的
# Node（pi 本身、npm、playwright）会忽略它并以 SELF_SIGNED_CERT_IN_CHAIN 失败。
# 改指向对所有用户可读、且已含 msb CA 的系统证书包。
GUEST_ENV = ["--env", "NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt"]


def die(message: str, code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code


def require(*commands: str) -> None:
    missing = [c for c in commands if shutil.which(c) is None]
    if missing:
        raise SystemExit(f"error: not on PATH: {', '.join(missing)}")


def load_local_env(root: Path) -> None:
    """读取 vm/local.env 的 KEY=VALUE 行；已存在的环境变量不被覆盖。"""
    path = root / LOCAL_ENV
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def model_access(root: Path, workdir: Path) -> list[str]:
    """生成 pi 的 models.json 并返回对应的 msb 参数（secret 绑定 + 文件挂载）。

    真实密钥只存在于宿主进程环境里；msb 在 VM 中放置占位符，并且只在发往
    API 主机的连接上替换。VM 里的任何进程都读不到真实值。
    """
    load_local_env(root)
    if not os.environ.get(KEY_ENV):
        raise SystemExit(
            f"error: {KEY_ENV} is not set. Export it or put it in {LOCAL_ENV} "
            f"(see vm/local.env.example)."
        )
    base_url = os.environ.get(BASE_URL_ENV, "").strip()
    host = urlparse(base_url or DEFAULT_API_URL).hostname
    if not host:
        raise SystemExit(f"error: {BASE_URL_ENV} is not a URL: {base_url!r}")
    providers = {"anthropic": {"baseUrl": base_url}} if base_url else {}
    models = workdir / "models.json"
    models.write_text(json.dumps({"providers": providers}, indent=2) + "\n", "utf-8")
    # 用 uid 映射的只读文件挂载而不是 --copy-file：后者注入的文件是 root:root 0600，
    # pi 以 agent 身份读不到，会静默退回官方端点，请求随即被 secret 策略拦下。
    return [
        "--secret",
        f"{KEY_ENV}@{host}",
        "--mount-file",
        f"{models}:{GUEST_PI_DIR}/models.json:ro,uid=1000,gid=1000",
    ]


def sandbox_exists(name: str) -> bool:
    proc = subprocess.run(
        ["msb", "inspect", name], capture_output=True, text=True, check=False
    )
    return proc.returncode == 0


def cmd_build(args: argparse.Namespace) -> int:
    require("docker", "msb")
    context = repo_root() / "vm" / "image"
    build = ["docker", "build", "-t", IMAGE, str(context)]
    if args.no_cache:
        build.insert(2, "--no-cache")
    for item in args.build_arg:
        build[2:2] = ["--build-arg", item]
    if subprocess.run(build, check=False).returncode:
        return die("docker build failed")
    # docker save 直接管道给 msb，避免在磁盘上落一个十几 GB 的中间 tar。
    print(f"loading {IMAGE} into microsandbox ...", flush=True)
    save = subprocess.Popen(["docker", "save", IMAGE], stdout=subprocess.PIPE)
    load = subprocess.run(
        ["msb", "image", "load", "-t", IMAGE], stdin=save.stdout, check=False
    )
    save.stdout.close()
    if save.wait() or load.returncode:
        return die("docker save | msb image load failed")
    return 0


def base_run(args: argparse.Namespace) -> list[str]:
    return [
        "msb",
        "run",
        "--pull",
        "never",
        "--quiet",
        "--no-stdin",
        "--label",
        LABEL,
        "--cpus",
        str(args.cpus),
        "--memory",
        args.memory,
        "--root-disk",
        args.root_disk,
        *GUEST_ENV,
    ]


def provider_error(events_path: Path) -> str | None:
    """最后一条 assistant 消息以 error 结束时返回错误文本。

    pi 在模型请求全部失败（连接错误、鉴权失败）时仍以 0 退出，事件流里只有
    stopReason=error 的空回答；不在这里拦下，评测会把它当成一次正常作答。
    """
    last: dict | None = None
    for line in events_path.read_text("utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message") if event.get("type") == "message_end" else None
        if isinstance(message, dict) and message.get("role") == "assistant":
            last = message
    if last and last.get("stopReason") == "error":
        return str(last.get("errorMessage") or "unknown provider error")
    return None


def cmd_verify(args: argparse.Namespace) -> int:
    require("msb")
    cmd = base_run(args) + [IMAGE, "--", "hs-verify-tools"]
    if args.services:
        cmd.append("--services")
    return subprocess.run(cmd, check=False).returncode


def cmd_run(args: argparse.Namespace) -> int:
    require("msb")
    root = repo_root()
    try:
        skill_dirs = resolve_targets(args.skill, root) if args.skill else []
    except SkillLoadError as exc:
        return die(str(exc))

    out = (args.out or DEFAULT_OUT_ROOT / time.strftime("%Y%m%d-%H%M%S")).resolve()
    if out.exists():
        shutil.rmtree(out)
    workspace = out / "workspace"
    if args.workspace:
        shutil.copytree(args.workspace, workspace)
    else:
        workspace.mkdir(parents=True)

    cmd = base_run(args) + model_access(root, out)
    cmd += ["--label", "kind=run", "--timeout", f"{args.timeout}s"]
    # 工作区是宿主上的一次性目录；uid/gid 映射让 VM 里的 agent 用户能写。
    cmd += ["--volume", f"{workspace}:{GUEST_WORKSPACE}:uid=1000,gid=1000"]
    # 只挂载被测 skill，且只读：基线运行在文件系统里根本找不到任何 skill。
    for path in skill_dirs:
        cmd += ["--volume", f"{path}:{GUEST_SKILLS}/{path.name}:ro"]
    cmd += ["--workdir", GUEST_WORKSPACE, IMAGE, "--"]

    pi = ["pi", "-p", args.prompt, "--mode", "json", "--no-session", "--offline"]
    pi += ["--model", args.model, "--thinking", args.thinking, "--no-skills"]
    for path in skill_dirs:
        pi += ["--skill", f"{GUEST_SKILLS}/{path.name}"]
    cmd += pi

    events_path = out / "events.jsonl"
    stderr_path = out / "stderr.log"
    started = time.monotonic()
    with events_path.open("wb") as sink, stderr_path.open("wb") as err_sink:
        try:
            rc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=err_sink,
                # msb 自己的 --timeout 先生效；这里只兜底 VM 启停卡死。
                timeout=args.timeout + 120,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            rc = 124
    error = provider_error(events_path) if rc == 0 else None
    if error:
        rc = 3
    meta = {
        "returncode": rc,
        "provider_error": error,
        "duration_s": round(time.monotonic() - started, 1),
        "model": args.model,
        "thinking": args.thinking,
        "skills": [p.name for p in skill_dirs],
        "prompt": args.prompt,
        "image": IMAGE,
        "pi_argv": pi,
    }
    (out / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", "utf-8"
    )
    print(json.dumps({"out": str(out), **meta}, ensure_ascii=False, indent=2))
    if error:
        print(f"error: model request failed inside the VM: {error}", file=sys.stderr)
    elif rc:
        tail = stderr_path.read_text("utf-8", errors="replace").strip()[-800:]
        print(f"error: run exited {rc}; stderr tail:\n{tail}", file=sys.stderr)
    return rc


def cmd_shell(args: argparse.Namespace) -> int:
    require("msb")
    root = repo_root()
    name = args.name
    if args.recreate and sandbox_exists(name):
        subprocess.run(["msb", "remove", "--force", name], check=False)
    # models.json 放宿主 /tmp（不进仓库），以文件挂载进 VM；每次进入前都重写，
    # 宿主重启清空 /tmp 后常驻 VM 仍能启动。
    state = Path("/tmp") / f"hs-vm-{name}"
    state.mkdir(parents=True, exist_ok=True)
    # 每次都校验并加载密钥：msb 在每次 start 时从宿主环境重新读取 secret 的值。
    access = model_access(root, state)
    if not sandbox_exists(name):
        cmd = [
            "msb",
            "create",
            IMAGE,
            "--name",
            name,
            "--pull",
            "never",
            "--label",
            LABEL,
            "--label",
            "kind=dev",
            "--cpus",
            str(args.cpus),
            "--memory",
            args.memory,
            "--root-disk",
            args.root_disk,
            # 开发 VM 挂载全部 skill（只读）到 pi 的用户级发现目录，交互时直接可用。
            "--volume",
            f"{root / 'skills'}:{GUEST_HOME}/.agents/skills:ro",
            *access,
            *GUEST_ENV,
        ]
        if subprocess.run(cmd, check=False).returncode:
            return die(f"msb create {name} failed")
    else:
        subprocess.run(["msb", "start", name], capture_output=True, check=False)
    return subprocess.run(
        ["msb", "exec", "--tty", name, "--", "bash", "-l"], check=False
    ).returncode


def cmd_clean(args: argparse.Namespace) -> int:
    require("msb")
    rc = subprocess.run(
        ["msb", "remove", "--force", "--label", LABEL], check=False
    ).returncode
    if args.image:
        rc |= subprocess.run(["msb", "image", "remove", IMAGE], check=False).returncode
        if shutil.which("docker"):
            rc |= subprocess.run(
                ["docker", "image", "rm", IMAGE], check=False
            ).returncode
    return rc


def add_resources(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cpus", type=int, default=DEFAULT_CPUS)
    parser.add_argument("--memory", default=DEFAULT_MEMORY)
    parser.add_argument(
        "--root-disk", default=DEFAULT_ROOT_DISK, help="writable root disk size"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="docker build the image and load it into msb")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument(
        "--build-arg",
        action="append",
        default=[],
        help="KEY=VALUE, e.g. PI_VERSION=1.2.0",
    )
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("verify", help="run hs-verify-tools in a throwaway VM")
    p.add_argument(
        "--services", action="store_true", help="also start postgres/redis/dockerd"
    )
    add_resources(p)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("run", help="run one pi prompt in a throwaway VM")
    p.add_argument("prompt")
    p.add_argument(
        "--skill", action="append", default=[], help="skill name or path; repeatable"
    )
    p.add_argument("--workspace", type=Path, help="host dir copied in as /workspace")
    p.add_argument(
        "--out", type=Path, help=f"output dir (default {DEFAULT_OUT_ROOT}/<ts>)"
    )
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--thinking", default=DEFAULT_THINKING, choices=THINKING_LEVELS)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S, help="seconds")
    add_resources(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("shell", help="open a shell in the persistent dev VM")
    p.add_argument("--name", default=DEV_SANDBOX)
    p.add_argument("--recreate", action="store_true", help="remove and recreate first")
    add_resources(p)
    p.set_defaults(func=cmd_shell)

    p = sub.add_parser("clean", help="remove every sandbox created by this tool")
    p.add_argument("--image", action="store_true", help="also remove the image")
    p.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
