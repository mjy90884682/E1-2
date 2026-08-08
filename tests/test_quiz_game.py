import json
import tempfile
import unittest
from pathlib import Path

from game import QuizGame
from models import GameState, Quiz, QuizSession, ScoreRecord
from repository import InvalidStateError, JsonGameStateRepository, StateSaveError


class QuizTest(unittest.TestCase):
    def test_checks_answer(self) -> None:
        quiz = Quiz("정답은?", ("A", "B", "C", "D"), 2)
        self.assertTrue(quiz.check_answer(2))
        self.assertFalse(quiz.check_answer(1))

    def test_rejects_invalid_quiz(self) -> None:
        with self.assertRaises(ValueError):
            Quiz("문제", ("A", "B"), 1)

    def test_rejects_non_string_question_and_boolean_answer(self) -> None:
        with self.assertRaises(TypeError):
            Quiz(123, ("A", "B", "C", "D"), 1)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            Quiz("문제", ("A", "B", "C", "D"), True)


class ScoreRecordTest(unittest.TestCase):
    def test_compares_accuracy_before_correct_count(self) -> None:
        self.assertTrue(ScoreRecord(1, 1).is_better_than(ScoreRecord(9, 10)))

    def test_prefers_more_correct_answers_when_accuracy_is_equal(self) -> None:
        self.assertTrue(ScoreRecord(2, 4).is_better_than(ScoreRecord(1, 2)))


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
        game = QuizGame(GameState([quiz]))
        session = game.start_quiz()
        assert session is not None
        session.submit_answer(1)

        result, updated = game.complete_quiz(session)

        self.assertTrue(updated)
        self.assertEqual(result, ScoreRecord(1, 1))
        self.assertEqual(game.export_state().best_score, result)


class JsonRepositoryTest(unittest.TestCase):
    def test_reports_file_system_error_while_saving(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing" / "state.json"
            repository = JsonGameStateRepository(path)

            with self.assertRaises(StateSaveError):
                repository.save(GameState())

    def test_returns_none_when_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"

            self.assertIsNone(JsonGameStateRepository(path).load())

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

    def test_reports_invalid_field_types(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(
                json.dumps(
                    {
                        "quizzes": [
                            {
                                "question": 123,
                                "choices": ["A", "B", "C", "D"],
                                "answer": True,
                            }
                        ],
                        "best_score": None,
                    }
                ),
                encoding="utf-8",
            )

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
