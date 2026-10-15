#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""HyperSkills 测试 VM 管理：构建镜像、自检、在一次性 microVM 里用 omp 跑提示词。

    uv run tools/vm.py build                      # docker 构建并导入 msb
    uv run tools/vm.py verify --services          # VM 内工具与服务自检
    uv run tools/vm.py run --skill office "..."   # 一次性 VM，只挂载 office skill
    uv run tools/vm.py run "..."                  # 不挂载任何 skill（基线）
    uv run tools/vm.py shell                      # 常驻开发 VM，交互式 omp
    uv run tools/vm.py clean                      # 删除本工具创建的全部 sandbox

VM 里没有宿主的 agent 配置、AGENTS.md、skill 目录或凭据，advisor 关闭：模型密钥经
msb `--secret` 以占位符注入，只在发往模型 API 主机的请求里被替换成真实值。
详见 vm/README.md。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import SkillLoadError, repo_root, resolve_targets  # noqa: E402

IMAGE = "hyperskills-vm:latest"
# 宿主侧可选配置文件（已 gitignore）；环境变量优先于文件。
LOCAL_ENV = "vm/local.env"


@dataclass(frozen=True, slots=True)
class Provider:
    """VM 能转发凭据的模型 provider：密钥变量名、可选代理地址变量名、官方端点。"""

    key_env: str
    base_url_env: str
    default_url: str


# 模型选择器的 `<provider>/` 前缀 → 凭据来源。只有这里列出的 provider 能在 VM 里拿到密钥。
PROVIDERS = {
    "openai": Provider(
        "OPENAI_API_KEY", "HS_VM_OPENAI_BASE_URL", "https://api.openai.com/v1"
    ),
    "anthropic": Provider(
        "ANTHROPIC_API_KEY", "HS_VM_ANTHROPIC_BASE_URL", "https://api.anthropic.com"
    ),
}
# VM 内 omp 的 smol 角色（镜像 config.yml 的 `modelRoles.smol: workbuddy/deepseek-v4.1-flash`）。
# omp 每次挂载 skill 都会用 smol 把描述压成路由提示；smol 解析不到时按内置优先级表回落到
# 已下线的 gpt-5.3-codex-spark，每个场景一次必失败的请求，累积触发网关熔断（日志 0089）。
# 所以它的凭据是每次运行的必需项，而不是可选 provider。
SMOL_PROVIDER = "workbuddy"
SMOL_KEY_ENV = "WORKBUDDY_API_KEY"
SMOL_BASE_URL_ENV = "HS_VM_WORKBUDDY_BASE_URL"
SMOL_MODEL = {
    "id": "deepseek-v4.1-flash",
    "name": "DeepSeek V4.1 Flash",
    "reasoning": True,
    "input": ["text"],
    "supportsTools": True,
    "contextWindow": 1000000,
    "maxTokens": 32000,
    "thinking": {"mode": "effort", "efforts": ["low", "high", "max"], "defaultLevel": "high"},
    "compat": {"supportsReasoningEffort": True, "maxTokensField": "max_tokens"},
}
# 评测模型由维护者指定为 GPT-6.1 Sol、medium 思考；基线与有 skill 同一配置才可比。
DEFAULT_MODEL = "openai/gpt-6.1-sol"
DEFAULT_THINKING = "medium"
THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max", "auto")
DEFAULT_OUT_ROOT = Path("/tmp/hs-vm-runs")
# 每次运行输出目录里的文件名；run_evals.py 复用同一套布局。
EVENTS_FILE = "events.jsonl"
STDERR_FILE = "stderr.log"
META_FILE = "meta.json"
# claim_out_dir 写入的运行标记：只有带它的目录才是本工具产物，上层工具才可替换。
RUN_MARKER = ".hyperskills-vm-run"
# msb --timeout 杀掉命令时打印的诊断（退出码只是 1）。
MSB_TIMEOUT_TEXT = "exec timed out"
DEFAULT_TIMEOUT_S = 900
DEFAULT_CPUS = 4
DEFAULT_MEMORY = "8G"
DEFAULT_ROOT_DISK = "32G"
DEV_SANDBOX = "hs-dev"
# 所有由本工具创建的 sandbox 都带这个标签，clean 按它清理。
LABEL = "project=hyperskills"
GUEST_HOME = "/home/agent"
GUEST_OMP_DIR = f"{GUEST_HOME}/.omp/agent"
# 镜像里的 omp config.yml 把它设为 skills.customDirectories。
GUEST_SKILLS = "/opt/hyperskills/skills"
GUEST_WORKSPACE = "/workspace"
# msb 做 TLS 拦截（secret 替换靠它）时把自己的 CA 写进系统证书包，同时设置
# NODE_EXTRA_CA_CERTS=/.msb/tls/ca.pem；但该路径只有 root 可读，以 agent 身份运行的
# Node/Bun 进程（omp、npm、playwright）会忽略它并以 SELF_SIGNED_CERT_IN_CHAIN 失败。
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


def model_access(root: Path, workdir: Path, providers: Sequence[str]) -> list[str]:
    """生成 omp 的 models.yml 并返回对应的 msb 参数（secret 绑定 + 文件挂载）。

    真实密钥只存在于宿主进程环境里；msb 在 VM 中放置占位符，并且只在发往
    该 provider API 主机的连接上替换。VM 里的任何进程都读不到真实值。
    """
    load_local_env(root)
    args: list[str] = []
    overrides: dict[str, dict[str, Any]] = {}
    for name in providers:
        provider = PROVIDERS[name]
        if not os.environ.get(provider.key_env):
            raise SystemExit(
                f"error: {provider.key_env} is not set. Export it or put it in "
                f"{LOCAL_ENV} (see vm/local.env.example)."
            )
        base_url = os.environ.get(provider.base_url_env, "").strip()
        host = urlparse(base_url or provider.default_url).hostname
        if not host:
            raise SystemExit(
                f"error: {provider.base_url_env} is not a URL: {base_url!r}"
            )
        if base_url:
            overrides[name] = {"baseUrl": base_url}
        args += ["--secret", f"{provider.key_env}@{host}"]
    # smol 角色的自定义 provider 每次都挂：apiKey 写环境变量名，omp 先按变量名解析，
    # VM 里该变量是 msb 的占位符，只在发往该主机的连接上被替换成真实值。
    smol_key = os.environ.get(SMOL_KEY_ENV, "").strip()
    smol_url = os.environ.get(SMOL_BASE_URL_ENV, "").strip()
    smol_host = urlparse(smol_url).hostname
    if not smol_key or not smol_host:
        raise SystemExit(
            f"error: {SMOL_KEY_ENV} and {SMOL_BASE_URL_ENV} must both be set for the "
            f"VM's smol role (see vm/local.env.example); without them omp falls back "
            f"to a retired model on every skill run."
        )
    overrides[SMOL_PROVIDER] = {
        "baseUrl": smol_url,
        "apiKey": SMOL_KEY_ENV,
        "api": "openai-completions",
        "authHeader": True,
        "auth": "apiKey",
        "models": [SMOL_MODEL],
    }
    args += ["--secret", f"{SMOL_KEY_ENV}@{smol_host}"]
    # JSON 是合法 YAML，省掉对宿主 YAML 序列化的依赖。
    models = workdir / "models.yml"
    models.write_text(json.dumps({"providers": overrides}, indent=2) + "\n", "utf-8")
    # 用 uid 映射的只读文件挂载而不是 --copy-file：后者注入的文件是 root:root 0600，
    # omp 以 agent 身份读不到，会静默退回官方端点，请求随即被 secret 策略拦下。
    args += [
        "--mount-file",
        f"{models}:{GUEST_OMP_DIR}/models.yml:ro,uid=1000,gid=1000",
    ]
    return args


def configured_providers() -> list[str]:
    """宿主上已提供密钥的 provider（常驻开发 VM 全部挂上）。"""
    return [n for n, p in PROVIDERS.items() if os.environ.get(p.key_env)]


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


@dataclass(frozen=True, slots=True)
class VmSpec:
    """一次性 VM 的规格。"""

    cpus: int = DEFAULT_CPUS
    memory: str = DEFAULT_MEMORY
    root_disk: str = DEFAULT_ROOT_DISK

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> VmSpec:
        return cls(cpus=args.cpus, memory=args.memory, root_disk=args.root_disk)


def base_run(spec: VmSpec) -> list[str]:
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
        str(spec.cpus),
        "--memory",
        spec.memory,
        "--root-disk",
        spec.root_disk,
        *GUEST_ENV,
    ]


def parse_events(raw: str) -> list[dict[str, Any]]:
    """按 LF 切分的 JSONL 事件；超时截断的残行被跳过。

    只能按 `\\n` 分帧：`str.splitlines()` 还会在 U+2028/U+2029 等字符处断行，而它们
    在 JSON 字符串里是合法的原样字符（输出未转义非 ASCII 时就会出现），整条事件会被
    拆坏并静默丢掉——恰好可能是最终回答或错误事件。
    """
    events: list[dict[str, Any]] = []
    for line in raw.split("\n"):
        line = line.removesuffix("\r")
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def provider_error(events_path: Path) -> str | None:
    """最后一条 assistant 消息以 error 结束时返回错误文本。

    pi 系 agent 在模型请求全部失败（连接错误、鉴权失败）时可能仍以 0 退出，事件流里
    只有 stopReason=error 的空回答；不在这里拦下，评测会把它当成一次正常作答。
    """
    last: dict[str, Any] | None = None
    for event in parse_events(events_path.read_text("utf-8", errors="replace")):
        message = event.get("message") if event.get("type") == "message_end" else None
        if isinstance(message, dict) and message.get("role") == "assistant":
            last = message
    if last and last.get("stopReason") == "error":
        return str(last.get("errorMessage") or "unknown provider error")
    return None


def cmd_verify(args: argparse.Namespace) -> int:
    require("msb")
    cmd = base_run(VmSpec.from_args(args)) + [IMAGE, "--", "hs-verify-tools"]
    if args.services:
        cmd.append("--services")
    return subprocess.run(cmd, check=False).returncode


class VmRunError(Exception):
    """运行无法开始：输出目录不可用或模型不受支持。不会删除或覆盖宿主上已有的内容。"""


def check_model(model: str) -> str:
    """返回模型所属 provider；VM 只能为 PROVIDERS 里的 provider 转发凭据。"""
    provider = model.lstrip("@").split("/", 1)[0]
    if "/" not in model or provider not in PROVIDERS:
        supported = ", ".join(f"{p}/*" for p in PROVIDERS)
        raise VmRunError(f"model must be one of {supported}; got {model}")
    return provider


def claim_out_dir(out: Path) -> None:
    """创建（或接管一个空的）输出目录，并以独占方式写入运行标记。

    非空目录一律拒绝：输出目录由调用方指定，可能是任何路径（`--out .` 就是仓库根），
    唯一安全的做法是只写入自己刚创建的空目录。标记用 O_EXCL 创建，两个进程同时认领
    同一个空目录时只有一个成功。标记只证明「目录由本工具创建」，不代表运行已结束；
    并发互斥由调用方负责（run_evals 用场景锁）。
    """
    if out.is_symlink():
        raise VmRunError(f"{out} is a symlink")
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise VmRunError(f"{out} is not empty")
    try:
        (out / RUN_MARKER).open("x", encoding="utf-8").close()
    except FileExistsError:
        raise VmRunError(f"{out} was claimed by another run") from None


def new_out_dir() -> Path:
    """默认输出目录：时间戳前缀 + 随机后缀，并发运行互不相撞。"""
    DEFAULT_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    prefix = time.strftime("%Y%m%d-%H%M%S-")
    return Path(tempfile.mkdtemp(prefix=prefix, dir=DEFAULT_OUT_ROOT))


@dataclass(slots=True)
class AgentRun:
    """一次 `run_agent` 的结果；产物都在 `out` 下。"""

    out: Path
    returncode: int
    timed_out: bool
    provider_error: str | None
    duration_s: float
    agent_argv: list[str]

    @property
    def events_path(self) -> Path:
        return self.out / EVENTS_FILE

    @property
    def stderr_path(self) -> Path:
        return self.out / STDERR_FILE

    @property
    def workspace(self) -> Path:
        return self.out / "workspace"


def run_agent(
    *,
    prompt: str,
    out: Path,
    skill_dirs: Sequence[Path] = (),
    files: Sequence[Path] = (),
    model: str = DEFAULT_MODEL,
    thinking: str = DEFAULT_THINKING,
    timeout: int = DEFAULT_TIMEOUT_S,
    spec: VmSpec | None = None,
) -> AgentRun:
    """在一次性 microVM 里跑一条 omp 提示词。`vm.py run` 与 `run_evals.py` 共用。

    `out` 必须不存在或为空目录（见 `claim_out_dir`）；`files` 按文件名复制进
    `/workspace`；`skill_dirs` 只读挂载并且是 omp 唯一能加载的 skill，空则为基线。
    """
    provider = check_model(model)
    claim_out_dir(out)
    workspace = out / "workspace"
    workspace.mkdir()
    for src in files:
        dest = workspace / src.name
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    cmd = base_run(spec or VmSpec()) + model_access(repo_root(), out, [provider])
    cmd += ["--label", "kind=run", "--timeout", f"{timeout}s"]
    # 工作区是宿主上的一次性目录；uid/gid 映射让 VM 里的 agent 用户能写。
    # 只有它被挂进 VM，输出目录里的事件流等产物对 agent 不可见。
    cmd += ["--volume", f"{workspace}:{GUEST_WORKSPACE}:uid=1000,gid=1000"]
    # 只挂载被测 skill，且只读：基线运行在文件系统里根本找不到任何 skill。
    for path in skill_dirs:
        cmd += ["--volume", f"{path}:{GUEST_SKILLS}/{path.name}:ro"]
    cmd += ["--workdir", GUEST_WORKSPACE, IMAGE, "--"]

    agent = ["omp", "-p", prompt, "--mode", "json", "--no-session"]
    agent += ["--model", model, "--thinking", thinking]
    if skill_dirs:
        agent += ["--skills", ",".join(p.name for p in skill_dirs)]
    else:
        agent.append("--no-skills")
    cmd += agent

    events_path = out / EVENTS_FILE
    stderr_path = out / STDERR_FILE
    started = time.monotonic()
    timed_out = False
    with events_path.open("wb") as sink, stderr_path.open("wb") as err_sink:
        try:
            rc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=err_sink,
                # msb 自己的 --timeout 先生效；这里只兜底 VM 启停卡死。
                timeout=timeout + 120,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            rc, timed_out = 124, True
    if rc and not timed_out:
        # msb 的 --timeout 杀掉命令后以 1 退出，只能从它的诊断输出区分超时。
        timed_out = MSB_TIMEOUT_TEXT in stderr_path.read_text("utf-8", errors="replace")
    error = provider_error(events_path) if rc == 0 else None
    if error:
        rc = 3
    run = AgentRun(
        out=out,
        returncode=rc,
        timed_out=timed_out,
        provider_error=error,
        duration_s=round(time.monotonic() - started, 1),
        agent_argv=agent,
    )
    meta = {
        "returncode": rc,
        "timed_out": timed_out,
        "provider_error": error,
        "duration_s": run.duration_s,
        "model": model,
        "thinking": thinking,
        "skills": [p.name for p in skill_dirs],
        "prompt": prompt,
        "image": IMAGE,
        "agent_argv": agent,
    }
    (out / META_FILE).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", "utf-8"
    )
    return run


def cmd_run(args: argparse.Namespace) -> int:
    root = repo_root()
    try:
        skill_dirs = resolve_targets(args.skill, root) if args.skill else []
    except SkillLoadError as exc:
        return die(str(exc))
    # 显式目录已存在（哪怕是空的）就拒绝：用户给的路径可能是任何东西。
    if args.out is not None and (args.out.exists() or args.out.is_symlink()):
        return die(f"--out {args.out} already exists; pick a new path")
    if args.workspace is not None and not args.workspace.is_dir():
        return die(f"--workspace {args.workspace} is not a directory")
    try:
        check_model(args.model)
    except VmRunError as exc:
        return die(str(exc))
    require("msb")
    out = args.out.resolve() if args.out is not None else new_out_dir()
    files = sorted(args.workspace.iterdir()) if args.workspace else []
    try:
        run = run_agent(
            prompt=args.prompt,
            out=out,
            skill_dirs=skill_dirs,
            files=files,
            model=args.model,
            thinking=args.thinking,
            timeout=args.timeout,
            spec=VmSpec.from_args(args),
        )
    except VmRunError as exc:
        return die(str(exc))
    meta = json.loads((out / META_FILE).read_text(encoding="utf-8"))
    print(json.dumps({"out": str(out), **meta}, ensure_ascii=False, indent=2))
    if run.provider_error:
        print(
            f"error: model request failed inside the VM: {run.provider_error}",
            file=sys.stderr,
        )
    elif run.returncode:
        tail = run.stderr_path.read_text("utf-8", errors="replace").strip()[-800:]
        print(
            f"error: run exited {run.returncode}; stderr tail:\n{tail}", file=sys.stderr
        )
    return run.returncode


def cmd_shell(args: argparse.Namespace) -> int:
    require("msb")
    root = repo_root()
    name = args.name
    if args.recreate and sandbox_exists(name):
        subprocess.run(["msb", "remove", "--force", name], check=False)
    # models.yml 放宿主 /tmp（不进仓库），以文件挂载进 VM；每次进入前都重写，
    # 宿主重启清空 /tmp 后常驻 VM 仍能启动。
    state = Path("/tmp") / f"hs-vm-{name}"
    state.mkdir(parents=True, exist_ok=True)
    # 每次都校验并加载密钥：msb 在每次 start 时从宿主环境重新读取 secret 的值。
    load_local_env(root)
    providers = configured_providers()
    if not providers:
        keys = ", ".join(p.key_env for p in PROVIDERS.values())
        return die(
            f"no model credentials: set one of {keys} (see vm/local.env.example)"
        )
    access = model_access(root, state, providers)
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
            # 开发 VM 挂载全部 skill（只读）到 omp 配置的 skill 目录，交互时直接可用。
            "--volume",
            f"{root / 'skills'}:{GUEST_SKILLS}:ro",
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

    p = sub.add_parser("run", help="run one omp prompt in a throwaway VM")
    p.add_argument("prompt")
    p.add_argument(
        "--skill", action="append", default=[], help="skill name or path; repeatable"
    )
    p.add_argument("--workspace", type=Path, help="host dir copied in as /workspace")
    p.add_argument(
        "--out",
        type=Path,
        help=f"new output dir, must not exist (default: unique dir in {DEFAULT_OUT_ROOT})",
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
