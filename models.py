from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Quiz:
    question: str
    choices: tuple[str, ...]
    answer: int

    def __post_init__(self) -> None:
        if not isinstance(self.question, str):
            raise TypeError("문제는 문자열이어야 합니다.")
        if not isinstance(self.choices, tuple):
            raise TypeError("선택지는 튜플이어야 합니다.")
        if any(not isinstance(choice, str) for choice in self.choices):
            raise TypeError("모든 선택지는 문자열이어야 합니다.")
        if isinstance(self.answer, bool) or not isinstance(self.answer, int):
            raise TypeError("정답 번호는 정수여야 합니다.")
        if not self.question.strip():
            raise ValueError("문제는 비어 있을 수 없습니다.")
        if len(self.choices) != 4:
            raise ValueError("선택지는 정확히 4개여야 합니다.")
        if any(not choice.strip() for choice in self.choices):
            raise ValueError("선택지는 비어 있을 수 없습니다.")
        if not 1 <= self.answer <= len(self.choices):
            raise ValueError("정답 번호가 선택지 범위를 벗어났습니다.")

    def check_answer(self, choice: int) -> bool:
        return choice == self.answer


@dataclass(frozen=True)
class ScoreRecord:
    correct: int
    total: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.correct, bool)
            or not isinstance(self.correct, int)
            or isinstance(self.total, bool)
            or not isinstance(self.total, int)
        ):
            raise TypeError("점수는 정수여야 합니다.")
        if self.total < 0 or not 0 <= self.correct <= self.total:
            raise ValueError("올바르지 않은 점수입니다.")

    @property
    def percentage(self) -> float:
        return self.correct / self.total * 100 if self.total else 0.0

    def is_better_than(self, other: ScoreRecord | None) -> bool:
        if other is None:
            return True
        rate_comparison = self.correct * other.total - other.correct * self.total
        if rate_comparison != 0:
            return rate_comparison > 0
        return self.correct > other.correct


@dataclass
class GameState:
    quizzes: list[Quiz] = field(default_factory=list)
    best_score: ScoreRecord | None = None


class QuizSession:
    def __init__(self, quizzes: Sequence[Quiz]) -> None:
        if not quizzes:
            raise ValueError("퀴즈가 한 개 이상 필요합니다.")
        self._quizzes = tuple(quizzes)
        self._answers: list[int] = []

    @property
    def current_quiz(self) -> Quiz | None:
        if self.is_finished:
            return None
        return self._quizzes[len(self._answers)]

    @property
    def current_number(self) -> int:
        return len(self._answers) + 1

    @property
    def total(self) -> int:
        return len(self._quizzes)

    @property
    def is_finished(self) -> bool:
        return len(self._answers) == len(self._quizzes)

    def submit_answer(self, choice: int) -> bool:
        quiz = self.current_quiz
        if quiz is None:
            raise RuntimeError("이미 종료된 퀴즈입니다.")
        if not 1 <= choice <= len(quiz.choices):
            raise ValueError("답안 번호가 선택지 범위를 벗어났습니다.")

        self._answers.append(choice)
        return quiz.check_answer(choice)

    def result(self) -> ScoreRecord:
        if not self.is_finished:
            raise RuntimeError("아직 퀴즈가 끝나지 않았습니다.")
        correct = sum(
            quiz.check_answer(answer)
            for quiz, answer in zip(self._quizzes, self._answers)
        )
        return ScoreRecord(correct=correct, total=self.total)
