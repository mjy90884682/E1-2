import json
import tempfile
import unittest
from pathlib import Path

from game import QuizGame
from models import GameState, Quiz, QuizSession, ScoreRecord
from repository import InvalidStateError, JsonGameStateRepository


class MemoryRepository:
    def __init__(self) -> None:
        self.saved_state: GameState | None = None

    def load(self) -> GameState:
        if self.saved_state is None:
            raise RuntimeError("저장된 상태가 없습니다.")
        return self.saved_state

    def save(self, state: GameState) -> None:
        self.saved_state = state


class QuizTest(unittest.TestCase):
    def test_checks_answer(self) -> None:
        quiz = Quiz("정답은?", ("A", "B", "C", "D"), 2)
        self.assertTrue(quiz.check_answer(2))
        self.assertFalse(quiz.check_answer(1))

    def test_rejects_invalid_quiz(self) -> None:
        with self.assertRaises(ValueError):
            Quiz("문제", ("A", "B"), 1)


class QuizSessionTest(unittest.TestCase):
    def test_finishes_and_calculates_result(self) -> None:
        quizzes = [
            Quiz("첫 문제", ("A", "B", "C", "D"), 1),
            Quiz("둘째 문제", ("A", "B", "C", "D"), 2),
        ]
        session = QuizSession(quizzes)

        self.assertTrue(session.submit_answer(1))
        self.assertFalse(session.submit_answer(3))

        self.assertTrue(session.is_finished)
        self.assertEqual(session.result(), ScoreRecord(1, 2))


class QuizGameTest(unittest.TestCase):
    def test_updates_best_score(self) -> None:
        quiz = Quiz("문제", ("A", "B", "C", "D"), 1)
        repository = MemoryRepository()
        game = QuizGame(GameState([quiz]), repository)
        session = game.start_quiz()
        assert session is not None
        session.submit_answer(1)

        result, updated = game.complete_quiz(session)

        self.assertTrue(updated)
        self.assertEqual(result, ScoreRecord(1, 1))
        self.assertIsNotNone(repository.saved_state)


class JsonRepositoryTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            repository = JsonGameStateRepository(path)
            expected = GameState(
                [Quiz("문제", ("A", "B", "C", "D"), 3)],
                ScoreRecord(1, 1),
            )

            repository.save(expected)
            actual = repository.load()

            self.assertEqual(actual, expected)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("percentage", data["best_score"])

    def test_reports_broken_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("not json", encoding="utf-8")

            with self.assertRaises(InvalidStateError):
                JsonGameStateRepository(path).load()

    def test_preserves_invalid_file_without_overwriting_existing_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("broken", encoding="utf-8")
            path.with_suffix(".json.broken").write_text("older", encoding="utf-8")
            repository = JsonGameStateRepository(path)

            backup_path = repository.preserve_invalid_file()

            self.assertEqual(backup_path.name, "state.json.broken.1")
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "broken")
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
