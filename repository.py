from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from models import GameState, Quiz, ScoreRecord, default_state


class StateLoadError(Exception):
    """저장 데이터를 유효한 게임 상태로 변환할 수 없을 때 발생한다."""


class GameStateRepository(Protocol):
    def load(self) -> GameState: ...

    def save(self, state: GameState) -> None: ...


class JsonGameStateRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> GameState:
        if not self._path.exists():
            return default_state()

        try:
            with self._path.open(encoding="utf-8") as file:
                data = json.load(file)
            return self._decode(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise StateLoadError("저장 파일이 손상되었거나 읽을 수 없습니다.") from error

    def save(self, state: GameState) -> None:
        data = self._encode(state)
        temporary_path = self._path.with_suffix(self._path.suffix + ".tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        temporary_path.replace(self._path)

    @staticmethod
    def _decode(data: Any) -> GameState:
        if not isinstance(data, dict) or not isinstance(data.get("quizzes"), list):
            raise ValueError("올바르지 않은 저장 형식입니다.")

        quizzes = [
            Quiz(
                question=item["question"],
                choices=tuple(item["choices"]),
                answer=item["answer"],
            )
            for item in data["quizzes"]
        ]
        score_data = data.get("best_score")
        best_score = (
            None
            if score_data is None
            else ScoreRecord(
                correct=score_data["correct"],
                total=score_data["total"],
            )
        )
        return GameState(quizzes=quizzes, best_score=best_score)

    @staticmethod
    def _encode(state: GameState) -> dict[str, Any]:
        return {
            "quizzes": [
                {
                    "question": quiz.question,
                    "choices": list(quiz.choices),
                    "answer": quiz.answer,
                }
                for quiz in state.quizzes
            ],
            "best_score": (
                None
                if state.best_score is None
                else {
                    "correct": state.best_score.correct,
                    "total": state.best_score.total,
                }
            ),
        }
