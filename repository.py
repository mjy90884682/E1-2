from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from models import GameState, Quiz, ScoreRecord


class InvalidStateError(Exception):
    """저장 데이터의 형식이나 내용이 올바르지 않을 때 발생한다."""


class StateAccessError(Exception):
    """파일 시스템 문제로 저장 데이터에 접근하지 못할 때 발생한다."""


class StateSaveError(Exception):
    """게임 상태를 파일에 저장하지 못할 때 발생한다."""


class GameStateRepository(Protocol):
    def load(self) -> GameState | None: ...

    def save(self, state: GameState) -> None: ...


class JsonGameStateRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> GameState | None:
        if not self._path.exists():
            return None

        try:
            with self._path.open(encoding="utf-8") as file:
                data = json.load(file)
        except OSError as error:
            raise StateAccessError("저장 파일을 읽을 수 없습니다.") from error
        except json.JSONDecodeError as error:
            raise InvalidStateError("저장 파일의 JSON 형식이 올바르지 않습니다.") from error

        try:
            return self._decode(data)
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidStateError("저장 데이터의 구조가 올바르지 않습니다.") from error

    def save(self, state: GameState) -> None:
        data = self._encode(state)
        temporary_path = self._path.with_suffix(self._path.suffix + ".tmp")

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
            temporary_path.replace(self._path)
        except OSError as error:
            raise StateSaveError("게임 상태를 저장할 수 없습니다.") from error

    def preserve_invalid_file(self) -> Path:
        backup_path = self._path.with_suffix(self._path.suffix + ".broken")
        sequence = 1
        while backup_path.exists():
            backup_path = self._path.with_suffix(f"{self._path.suffix}.broken.{sequence}")
            sequence += 1
        try:
            self._path.replace(backup_path)
        except OSError as error:
            raise StateAccessError("손상된 저장 파일을 보존할 수 없습니다.") from error
        return backup_path

    @staticmethod
    def _decode(data: Any) -> GameState:
        if not isinstance(data, dict) or not isinstance(data.get("quizzes"), list):
            raise ValueError("올바르지 않은 저장 형식입니다.")

        quizzes = [JsonGameStateRepository._decode_quiz(item) for item in data["quizzes"]]
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
    def _decode_quiz(item: Any) -> Quiz:
        if not isinstance(item, dict):
            raise TypeError("퀴즈는 객체여야 합니다.")
        question = item["question"]
        choices = item["choices"]
        answer = item["answer"]
        if not isinstance(choices, list):
            raise TypeError("선택지는 배열이어야 합니다.")
        return Quiz(question=question, choices=tuple(choices), answer=answer)

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
