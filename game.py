from models import GameState, Quiz, QuizSession, ScoreRecord
from repository import GameStateRepository


class QuizGame:
    def __init__(self, state: GameState, repository: GameStateRepository) -> None:
        self._state = state
        self._repository = repository

    def start_quiz(self) -> QuizSession | None:
        if not self._state.quizzes:
            return None
        return QuizSession(self._state.quizzes)

    def complete_quiz(self, session: QuizSession) -> tuple[ScoreRecord, bool]:
        result = session.result()
        is_new_best = result.is_better_than(self._state.best_score)
        if is_new_best:
            self._state.best_score = result
            self.save()
        return result, is_new_best

    def add_quiz(self, quiz: Quiz) -> None:
        self._state.quizzes.append(quiz)
        self.save()

    def list_quizzes(self) -> tuple[Quiz, ...]:
        return tuple(self._state.quizzes)

    def get_best_score(self) -> ScoreRecord | None:
        return self._state.best_score

    def save(self) -> None:
        self._repository.save(self._state)
