# 공개 origin 접근 검증

다음 명령은 `git remote get-url origin`으로 주소를 가져오고, 호스트 파일을 전혀 마운트하지 않은 새 컨테이너에서 인증 프롬프트와 Git 설정을 비활성화한 뒤 `git ls-remote`를 실행합니다.

```bash
./scripts/verify_public_origin.sh
```

origin URL에 사용자 정보가 포함되어 있거나, 인증 없이 `HEAD`와 `main`을 조회할 수 없으면 실패합니다. 기본 Git 클라이언트 이미지는 Gitea 실습과 동일한 `docker.gitea.com/gitea:1.24.7`입니다.

검증 당시의 출력은 `snapshots/public-origin.txt`에 보존합니다.
