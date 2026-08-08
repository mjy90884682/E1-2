# Screenshot files

자동 생성 파일은 `capture_submission_screenshots.py`가 지정한 Git tag를 임시 디렉터리에 추출하고, 그 원본의 실제 프로그램과 Git 출력을 사용해 만듭니다. 따라서 나중의 증거 커밋이 프로그램 결과를 바꾸지 않습니다.

`vscode-environment.png`만 실제 GUI 환경에서 수동으로 추가합니다. 권장 화면에는 다음 항목이 함께 보여야 합니다.

- VS Code에서 이 저장소를 연 상태
- 선택된 `.venv` Python interpreter
- Source Control 또는 GitHub 원격 연결 상태
- 비밀 토큰이나 개인정보가 노출되지 않은 터미널의 `python --version`
