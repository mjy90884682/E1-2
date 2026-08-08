from collections.abc import Sequence

from models import GameState, Quiz, QuizSession, ScoreRecord


class QuizGame:
    def __init__(self, state: GameState, default_quizzes: Sequence[Quiz] = ()) -> None:
        self._state = state
        self._default_quizzes = tuple(default_quizzes)

    def _all_quizzes(self) -> tuple[Quiz, ...]:
        return self._default_quizzes + tuple(self._state.quizzes)

    def start_quiz(self) -> QuizSession | None:
        quizzes = self._all_quizzes()
        if not quizzes:
            return None
        return QuizSession(quizzes)

    def complete_quiz(self, session: QuizSession) -> tuple[ScoreRecord, bool]:
        result = session.result()
        is_new_best = result.is_better_than(self._state.best_score)
        if is_new_best:
            self._state.best_score = result
        return result, is_new_best

    def add_quiz(self, quiz: Quiz) -> None:
        self._state.quizzes.append(quiz)

    def list_quizzes(self) -> tuple[Quiz, ...]:
        return self._all_quizzes()

    def get_best_score(self) -> ScoreRecord | None:
        return self._state.best_score

    def export_state(self) -> GameState:
        return GameState(list(self._state.quizzes), self._state.best_score)
