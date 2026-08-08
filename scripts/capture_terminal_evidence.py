#!/usr/bin/env python3

import codecs
import errno
import fcntl
import hashlib
import json
import os
import pty
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from termios import TIOCSWINSZ


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "evidence" / "snapshots"
SCRIPTED_DIALOGUE = (
    ("선택: ", "2"),
    ("문제: ", "증거용으로 추가한 문제는?"),
    ("선택지 1: ", "첫 번째 선택지"),
    ("선택지 2: ", "두 번째 선택지"),
    ("선택지 3: ", "세 번째 선택지"),
    ("선택지 4: ", "네 번째 선택지"),
    ("정답 번호: ", "1"),
    ("선택: ", "3"),
    ("선택: ", "1"),
    ("정답: ", "2"),
    ("정답: ", "3"),
    ("정답: ", "4"),
    ("정답: ", "3"),
    ("정답: ", "1"),
    ("정답: ", "1"),
    ("선택: ", "4"),
    ("선택: ", "5"),
)


def run_text(*command: str) -> str:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout


def capture_quiz_session(destination: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="quiz-evidence-") as directory:
        working_directory = Path(directory)
        # 실제 state.json을 건드리지 않도록 패키지를 임시 디렉터리에 복사한다.
        shutil.copytree(
            PROJECT_ROOT / "quiz_game" / "src" / "quiz_game",
            working_directory / "quiz_game",
        )

        master_fd, slave_fd = pty.openpty()
        fcntl.ioctl(master_fd, TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
        started_at = time.monotonic()
        process = subprocess.Popen(
            [sys.executable, "-m", "quiz_game"],
            cwd=working_directory,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env={
                **os.environ,
                "TERM": "xterm-256color",
                "PYTHONUNBUFFERED": "1",
                "PYTHONPATH": str(working_directory),
            },
        )
        os.close(slave_fd)
        dialogue = iter(SCRIPTED_DIALOGUE)
        expected_prompt, response = next(dialogue)
        pending_output = ""
        # PTY는 한글 한 글자의 UTF-8 바이트를 여러 번에 나눠 반환할 수 있다.
        decoder = codecs.getincrementaldecoder("utf-8")()

        header = {
            "version": 2,
            "width": 100,
            "height": 30,
            "timestamp": int(time.time()),
            "env": {"SHELL": "/bin/sh", "TERM": "xterm-256color"},
            "command": "python -m quiz_game",
        }
        with destination.open("w", encoding="utf-8") as output:
            output.write(json.dumps(header, ensure_ascii=False) + "\n")
            while True:
                readable, _, _ = select.select([master_fd], [], [], 0.1)
                if readable:
                    try:
                        data = os.read(master_fd, 65536)
                    except OSError as error:
                        if error.errno == errno.EIO:
                            break
                        raise
                    if not data:
                        break
                    decoded = decoder.decode(data)
                    if not decoded:
                        continue
                    pending_output += decoded
                    event = [round(time.monotonic() - started_at, 6), "o", decoded]
                    output.write(json.dumps(event, ensure_ascii=False) + "\n")
                    # 프롬프트를 확인한 뒤 답해 실제 사용자 입력 순서를 재현한다.
                    if expected_prompt and expected_prompt in pending_output:
                        os.write(master_fd, f"{response}\n".encode("utf-8"))
                        pending_output = ""
                        try:
                            expected_prompt, response = next(dialogue)
                        except StopIteration:
                            expected_prompt, response = "", ""
                elif process.poll() is not None:
                    break
        os.close(master_fd)
        if process.wait() != 0:
            raise RuntimeError("퀴즈 증거 세션 실행에 실패했습니다.")
        if expected_prompt:
            raise RuntimeError(f"예상한 프롬프트를 찾지 못했습니다: {expected_prompt}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    environment_path = OUTPUT_DIR / "environment.txt"
    graph_path = OUTPUT_DIR / "git-graph.txt"
    session_path = OUTPUT_DIR / "quiz-session.cast"

    environment_path.write_text(
        "$ python --version\n"
        + run_text(sys.executable, "--version")
        + "\n$ git --version\n"
        + run_text("git", "--version")
        + "\n$ uname -a\n"
        + run_text("uname", "-a"),
        encoding="utf-8",
    )
    graph = run_text("git", "log", "--oneline", "--graph", "--decorate", "--all")
    graph_path.write_text(
        "$ git log --oneline --graph --decorate --all\n"
        + "\n".join(line.rstrip() for line in graph.splitlines())
        + "\n",
        encoding="utf-8",
    )
    capture_quiz_session(session_path)

    revision = run_text("git", "rev-parse", "HEAD").strip()
    files = [environment_path, graph_path, session_path]
    manifest = {
        "revision": revision,
        "generator": str(Path(__file__).relative_to(PROJECT_ROOT)),
        "files": {
            str(path.relative_to(PROJECT_ROOT)): {"sha256": sha256(path)} for path in files
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: 터미널 증거와 해시 매니페스트를 {OUTPUT_DIR}에 생성했습니다.")


if __name__ == "__main__":
    main()
