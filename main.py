from pathlib import Path

from console_ui import ConsoleUI
from game import QuizGame
from models import default_state
from repository import InvalidStateError, JsonGameStateRepository, StateAccessError


def play_quiz(game: QuizGame, ui: ConsoleUI) -> None:
    session = game.start_quiz()
    if session is None:
        ui.show_message("등록된 퀴즈가 없습니다.")
        return

    while not session.is_finished:
        quiz = session.current_quiz
        if quiz is None:
            break
        choice = ui.ask_answer(quiz, session.current_number, session.total)
        ui.show_message("정답입니다!" if session.submit_answer(choice) else "오답입니다.")

    result, is_new_best = game.complete_quiz(session)
    ui.show_result(result, is_new_best)


def run_menu(game: QuizGame, ui: ConsoleUI) -> None:
    while True:
        ui.show_menu()
        choice = ui.ask_menu_choice()

        if choice == 1:
            play_quiz(game, ui)
        elif choice == 2:
            game.add_quiz(ui.ask_new_quiz())
            ui.show_message("퀴즈가 저장되었습니다.")
        elif choice == 3:
            ui.show_quizzes(game.list_quizzes())
        elif choice == 4:
            ui.show_best_score(game.get_best_score())
        else:
            return


def main() -> None:
    ui = ConsoleUI()
    repository = JsonGameStateRepository(Path(__file__).with_name("state.json"))
    try:
        state = repository.load()
    except InvalidStateError as error:
        ui.show_message(str(error))
        try:
            backup_path = repository.preserve_invalid_file()
        except StateAccessError as backup_error:
            ui.show_message(str(backup_error))
            return
        ui.show_message(f"기존 파일을 {backup_path.name}에 보존하고 기본 데이터로 시작합니다.")
        state = default_state()
    except StateAccessError as error:
        ui.show_message(str(error))
        return

    game = QuizGame(state, repository)
    try:
        run_menu(game, ui)
    except (KeyboardInterrupt, EOFError):
        ui.show_message("\n입력이 중단되었습니다. 저장 후 종료합니다.")
    finally:
        try:
            game.save()
        except OSError as error:
            ui.show_message(f"저장하지 못했습니다: {error}")


if __name__ == "__main__":
    main()
