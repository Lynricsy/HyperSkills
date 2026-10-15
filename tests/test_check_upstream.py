"""上游检查对异常仓库状态的归类：用本地夹具服务模拟 GitHub API，不访问网络。"""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import check_upstream  # noqa: E402

PIN = "a" * 40

# 路径 -> (状态码, 响应体)；与 GitHub 对这些情况的真实响应一致。
ROUTES = {
    "/repos/o/emptied/commits": (409, {"message": "Git Repository is empty."}),
    "/repos/o/gone/commits": (404, {"message": "Not Found"}),
    "/repos/o/live/commits": (200, [{"sha": PIN}]),
    # HEAD 已前进，但 compare 接口报 409：区间无法确认。
    "/repos/o/flaky/commits": (200, [{"sha": "b" * 40}]),
    f"/repos/o/flaky/compare/{PIN}...main": (409, {"message": "Git Repository is empty."}),
}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server 约定的方法名
        code, body = ROUTES.get(self.path.split("?", 1)[0], (500, {}))
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args: object) -> None:
        pass


class RepositoryStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.original_root = check_upstream.API_ROOT
        # 非 api.github.com 的根地址会跳过 gh，直接走 HTTP 传输。
        check_upstream.API_ROOT = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        check_upstream.API_ROOT = cls.original_root
        cls.server.shutdown()
        cls.server.server_close()

    def status_of(self, repo: str, git_head: str | None = None) -> str:
        upstream = {"id": repo, "kind": "repo", "repo": f"o/{repo}", "ref": "main", "commit": PIN}
        # git ls-remote 是回退传输；替换掉它，测试不访问网络。
        with mock.patch.object(check_upstream, "ls_remote_head", return_value=git_head):
            return check_upstream.check_upstream(upstream)["status"]

    def test_emptied_repository_is_reported_not_raised(self) -> None:
        # API 返回 409 且 git 也取不到分支：以前这里抛出 HTTPError，整次检查中断。
        self.assertEqual(self.status_of("emptied"), "empty")

    def test_api_409_defers_to_git_refs(self) -> None:
        # GitHub API 可能对仍有分支的仓库返回 409；git 取到的 HEAD 等于 pin 时不得报成空仓库。
        self.assertEqual(self.status_of("emptied", git_head=PIN), "up_to_date")

    def test_deleted_repository_stays_missing(self) -> None:
        self.assertEqual(self.status_of("gone"), "missing")

    def test_compare_409_reports_behind_instead_of_aborting(self) -> None:
        upstream = {"id": "flaky", "kind": "repo", "repo": "o/flaky", "ref": "main", "commit": PIN, "paths": ["x"]}
        result = check_upstream.check_upstream(upstream)
        self.assertEqual(result["status"], "behind")
        self.assertIn("range not resolved", result["reason"])


if __name__ == "__main__":
    unittest.main()
