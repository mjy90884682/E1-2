# Docker/Gitea Git 실습

`scripts/git_clone_pull_practice.sh`는 호스트의 Git 인증이나 별도 Gitea 설치 없이 Docker만으로 clone과 pull 흐름을 재현합니다.

```bash
./scripts/git_clone_pull_practice.sh
```

실행 순서:

1. 격리된 Docker 네트워크와 임시 Gitea를 시작합니다.
2. 실습 사용자와 공개 저장소를 생성합니다.
3. 현재 `main`을 Gitea에 push합니다.
4. 별도 디렉터리에 clone하고 파일을 추가해 commit·push합니다.
5. 기존 디렉터리에서 `git pull --ff-only`을 실행합니다.
6. 커밋과 파일 내용이 반영됐는지 검사합니다.
7. 컨테이너와 네트워크를 제거합니다.

기본 이미지는 `docker.gitea.com/gitea:1.24.7`이며 `GITEA_IMAGE` 환경 변수로 바꿀 수 있습니다. 실습은 임시 서버에서 수행하므로 실제 GitHub 저장소를 변경하지 않습니다.
