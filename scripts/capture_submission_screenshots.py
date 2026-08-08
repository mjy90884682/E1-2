#!/usr/bin/env python3
import argparse
import hashlib
import html
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "submission" / "screenshots"
BROWSER_IMAGE = (
    "selenium/standalone-chromium@"
    "sha256:ddcd01e43742e92eaeb3bc114a01f3e8d6b5afa326ac75aefd57a198d0d20a42"
)


def command_output(*command: str, cwd: Path = PROJECT_ROOT) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout


def extract_revision(revision: str, destination: Path) -> None:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", revision],
        cwd=PROJECT_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination, filter="data")


def run_quiz(source: Path, state_directory: Path, answers: list[str]) -> str:
    environment = {
        **os.environ,
        "PYTHONPATH": str(source / "quiz_game" / "src"),
        "PYTHONUNBUFFERED": "1",
    }
    return subprocess.run(
        [sys.executable, "-m", "quiz_game"],
        cwd=state_directory,
        env=environment,
        input="\n".join([*answers, ""]),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout


def lines_containing(output: str, prefixes: tuple[str, ...]) -> str:
    return "\n".join(
        line for line in output.splitlines() if line.strip().startswith(prefixes)
    )


def lines_with_text(output: str, fragments: tuple[str, ...]) -> str:
    """파이프로 입력해 프롬프트와 결과가 한 줄에 붙어도 필요한 결과를 남긴다."""
    return "\n".join(
        line for line in output.splitlines() if any(text in line for text in fragments)
    )


def render_page(title: str, subtitle: str, command: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #0b1020; color: #e5e7eb; font-family: system-ui, sans-serif; }}
  main {{ width: 1180px; margin: 34px auto; }}
  h1 {{ margin: 0 0 8px; font-size: 30px; color: #f8fafc; }}
  .subtitle {{ color: #93c5fd; margin-bottom: 22px; }}
  .terminal {{ border: 1px solid #334155; border-radius: 12px; overflow: hidden; box-shadow: 0 18px 50px #0008; }}
  .bar {{ background: #1e293b; padding: 11px 16px; color: #cbd5e1; font: 14px monospace; }}
  pre {{ margin: 0; padding: 20px; min-height: 520px; background: #020617; color: #d1fae5;
         white-space: pre-wrap; font: 16px/1.45 'DejaVu Sans Mono', monospace; }}
  footer {{ margin-top: 14px; color: #94a3b8; font: 13px monospace; }}
</style>
<main>
  <h1>{html.escape(title)}</h1>
  <div class="subtitle">{html.escape(subtitle)}</div>
  <section class="terminal">
    <div class="bar">$ {html.escape(command)}</div>
    <pre>{html.escape(content)}</pre>
  </section>
  <footer>실제 명령 출력에서 생성 · revision과 SHA-256은 manifest.json에 기록</footer>
</main>
</html>"""


def capture_png(work_directory: Path, name: str, page: str) -> Path:
    html_path = work_directory / f"{name}.html"
    png_path = work_directory / f"{name}.png"
    html_path.write_text(page, encoding="utf-8")
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            "root",
            "--mount",
            f"type=bind,src={work_directory},dst=/work",
            "--entrypoint",
            "chromium",
            BROWSER_IMAGE,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--user-data-dir=/tmp/submission-chromium-profile",
            "--force-device-scale-factor=1",
            "--window-size=1280,720",
            f"--screenshot=/work/{name}.png",
            f"file:///work/{name}.html",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(f"Chromium 캡처 실패 ({name}):\n{result.stderr}")
    if not png_path.is_file():
        raise RuntimeError(f"스크린샷이 생성되지 않았습니다: {name}")
    return png_path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True, help="스크린샷을 생성할 Git tag 또는 commit")
    args = parser.parse_args()
    revision = command_output("git", "rev-parse", f"{args.revision}^{{commit}}").strip()
    remote = command_output("git", "remote", "get-url", "origin").strip()

    with tempfile.TemporaryDirectory(prefix="quiz-submission-") as directory:
        work = Path(directory)
        source = work / "source"
        state = work / "state"
        source.mkdir()
        state.mkdir()
        extract_revision(args.revision, source)

        add_output = run_quiz(
            source,
            state,
            [
                "2",
                "검증 가능한 증거의 조건은?",
                "입력과 revision을 기록한다",
                "화면만 꾸민다",
                "결과를 수정한다",
                "기록하지 않는다",
                "1",
                "5",
            ],
        )
        list_output = run_quiz(source, state, ["3", "5"])
        play_output = run_quiz(source, state, ["1", "2", "3", "4", "3", "1", "1", "5"])
        score_output = run_quiz(source, state, ["4", "5"])

        evidence = {
            "environment": (
                "개발 환경",
                "Python과 Git 버전 및 검증 대상",
                "python --version && git --version",
                f"revision={revision}\nremote={remote}\n"
                + command_output(sys.executable, "--version")
                + command_output("git", "--version"),
            ),
            "add-quiz": (
                "퀴즈 추가",
                "실제 콘솔 입력 흐름으로 문제를 추가하고 state.json에 저장",
                "python -m quiz_game  # 메뉴 2",
                "입력 문제: 검증 가능한 증거의 조건은?\n"
                "입력 선택지 1: 입력과 revision을 기록한다\n"
                "입력 선택지 2: 화면만 꾸민다\n"
                "입력 선택지 3: 결과를 수정한다\n"
                "입력 선택지 4: 기록하지 않는다\n"
                "입력 정답 번호: 1\n\n"
                + lines_with_text(add_output, ("새 퀴즈", "퀴즈가 저장")),
            ),
            "quiz-list": (
                "퀴즈 목록",
                "기본 5문제와 방금 추가한 문제를 재실행 후 확인",
                "python -m quiz_game  # 메뉴 3",
                lines_containing(list_output, tuple(f"{number}." for number in range(1, 7))),
            ),
            "play-progress-score": (
                "퀴즈 플레이",
                "문제별 진행률과 현재 점수, 최종 결과",
                "python -m quiz_game  # 메뉴 1",
                lines_containing(
                    play_output,
                    ("진행:", "문제:", "정답입니다", "오답입니다", "현재 점수:", "결과:", "새로운"),
                ),
            ),
            "best-score": (
                "최고 점수",
                "프로그램 재실행 후 state.json에서 최고 점수 복원",
                "python -m quiz_game  # 메뉴 4",
                lines_with_text(score_output, ("최고 점수:", "기록된 점수")),
            ),
            "git-graph": (
                "Git 브랜치와 병합 이력",
                f"검증 대상 {args.revision}",
                f"git log --graph {args.revision}",
                command_output(
                    "git",
                    "log",
                    "--oneline",
                    "--graph",
                    "--decorate",
                    "--max-count=26",
                    args.revision,
                ),
            ),
        }

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        generated: dict[str, dict[str, str]] = {}
        for name, (title, subtitle, command, content) in evidence.items():
            png = capture_png(work, name, render_page(title, subtitle, command, content))
            destination = SCREENSHOT_DIR / png.name
            shutil.copy2(png, destination)
            generated[str(destination.relative_to(PROJECT_ROOT))] = {"sha256": sha256(destination)}

    manifest = {
        "revision": revision,
        "revision_input": args.revision,
        "remote": remote,
        "browser_image": BROWSER_IMAGE,
        "generator": str(Path(__file__).relative_to(PROJECT_ROOT)),
        "screenshots": generated,
        "manual_screenshot": "docs/submission/screenshots/vscode-environment.png",
    }
    (SCREENSHOT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: {args.revision} 기준 제출 스크린샷 {len(generated)}개를 생성했습니다.")


if __name__ == "__main__":
    main()
