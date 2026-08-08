# Scripts

| 스크립트 | 목적 | 요구 환경 |
|---|---|---|
| `setup_venv.sh` | `.venv` 생성 및 로컬 `src` 패키지 연결 | Python 3.10+, POSIX 셸 |
| `capture_terminal_evidence.py` | 퀴즈 전체 흐름 PTY 기록과 해시 생성 | 준비된 `.venv` |
| `github_clone_pull_practice.sh` | 실제 GitHub origin에서 clone·push·pull 실습 | GitHub 쓰기 권한, Git, POSIX 셸 |
| `verify_public_origin.sh` | 깨끗한 컨테이너에서 origin 공개 접근 확인 | Docker, POSIX 셸 |

`setup_venv.sh`는 외부 의존성이 없는 프로젝트 특성에 맞춰 `venv --without-pip`를 사용하고, 가상환경의 `.pth`에 `quiz_game/src`를 연결합니다. 시스템 패키지를 설치하거나 네트워크에 접근하지 않습니다.

GitHub 실습은 실제 `origin/main`에 증거 커밋을 추가하므로 기본 실행을 거부하고 `--execute` 확인 인자를 요구합니다. 공개 접근 검증만 Docker의 깨끗한 컨테이너를 사용합니다. 자세한 절차는 [Git 실습 문서](../docs/git-practice.md)와 [증거 문서](../docs/evidence/README.md)를 참고하세요.
