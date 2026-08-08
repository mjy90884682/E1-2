#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON=${PYTHON:-python3}

cd "$PROJECT_ROOT"
"$PYTHON" -m venv --clear --without-pip .venv
SITE_PACKAGES=$(
    .venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'
)
printf '%s\n' "$PROJECT_ROOT/quiz_game/src" > "$SITE_PACKAGES/codyssey_quiz_game.pth"

printf '\n가상환경 준비가 완료되었습니다.\n'
printf '활성화: . .venv/bin/activate\n'
printf '실행:   python main.py\n'
printf '테스트: python -m unittest discover -s quiz_game/tests -v\n'
