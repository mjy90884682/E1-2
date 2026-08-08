# Python 퀴즈 게임 프로토타입

콘솔에서 퀴즈를 풀고, 문제와 최고 점수를 `state.json`에 저장하는 간단한 프로그램입니다.

## 실행

Python 3.10 이상에서 다음 명령을 실행합니다.

```bash
python3 main.py
```

테스트는 표준 라이브러리만 사용합니다.

```bash
python3 -m unittest discover -s tests -v
```

## 구조

- `models.py`: 퀴즈, 풀이 세션, 점수와 게임 상태
- `data/default_quizzes.json`: 애플리케이션이 제공하는 읽기 전용 기본 퀴즈
- `game.py`: 기능을 조율하고 상태 변경을 관리하는 `QuizGame`
- `repository.py`: `state.json` 읽기와 쓰기
- `console_ui.py`: 사용자 입력과 화면 출력
- `main.py`: 객체 조립, 메뉴 흐름과 안전한 종료

`percentage`는 저장하지 않고 `correct`와 `total`로부터 계산합니다. 기본 퀴즈는 `data/default_quizzes.json`에서 매번 읽고, `state.json`에는 사용자가 추가한 퀴즈와 최고 점수만 저장합니다.

최고 점수는 정답률을 먼저 비교합니다. 정답률이 같으면 더 많은 문제를 맞힌 기록을 우선합니다. 예를 들어 `1/1`은 `9/10`보다 높고, `2/4`는 `1/2`보다 높은 기록입니다.
