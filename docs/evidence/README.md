# 재현 가능한 제출 증거

## clone과 pull 실습

Docker가 실행 중인 환경에서 다음 명령을 사용합니다.

```bash
./scripts/git_clone_pull_practice.sh
```

스크립트는 임시 Gitea 서버를 만들고 현재 저장소 게시, 별도 디렉터리 clone, 변경 commit·push, 기존 디렉터리 pull과 내용 검증을 순서대로 수행합니다. 컨테이너와 네트워크는 성공 여부와 관계없이 종료 시 제거됩니다.

기본 이미지는 Gitea 공식 Docker 문서의 안정 버전 예시인 `docker.gitea.com/gitea:1.24.7`입니다. 다른 버전은 다음처럼 지정할 수 있습니다.

```bash
GITEA_IMAGE=docker.gitea.com/gitea:1.24.7 ./scripts/git_clone_pull_practice.sh
```
