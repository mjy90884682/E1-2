# 터미널 증거 생성

GUI가 필요하지 않은 제출 증거는 다음 명령으로 다시 생성할 수 있습니다.

```bash
.venv/bin/python scripts/capture_terminal_evidence.py
```

생성 결과:

- `snapshots/environment.txt`: Python, Git과 운영체제 정보
- `snapshots/git-graph.txt`: 브랜치와 병합 그래프
- `snapshots/quiz-session.cast`: 퀴즈 추가, 목록, 전체 플레이, 점수 확인과 종료를 기록한 asciinema v2 형식의 PTY 세션
- `snapshots/manifest.json`: 생성 기준 Git revision과 각 파일의 SHA-256

`.cast`는 JSON Lines 텍스트이므로 별도 도구 없이 출력과 입력을 검토할 수 있습니다. asciinema가 설치된 환경에서는 다음처럼 실제 터미널 흐름으로 재생할 수도 있습니다.

```bash
asciinema play docs/evidence/snapshots/quiz-session.cast
```
