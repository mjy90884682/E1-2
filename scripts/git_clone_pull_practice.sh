#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
GITEA_IMAGE=${GITEA_IMAGE:-docker.gitea.com/gitea:1.24.7}
RUN_ID="quiz-git-practice-$$"
CONTAINER_NAME="$RUN_ID-gitea"
NETWORK_NAME="$RUN_ID-network"
PRACTICE_USER=practice
PRACTICE_PASSWORD='local-practice-password'
REPOSITORY_NAME=quiz-practice

cleanup() {
    docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker network rm "$NETWORK_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

step() {
    printf '\n[%s] %s\n' "$1" "$2"
}

step 1 "격리된 Docker 네트워크와 Gitea를 시작합니다."
docker network create "$NETWORK_NAME" >/dev/null
docker run --detach \
    --name "$CONTAINER_NAME" \
    --hostname gitea \
    --network "$NETWORK_NAME" \
    --mount "type=bind,src=$PROJECT_ROOT,dst=/source,readonly" \
    --env GITEA__database__DB_TYPE=sqlite3 \
    --env GITEA__security__INSTALL_LOCK=true \
    --env GITEA__server__DOMAIN=gitea \
    --env GITEA__server__ROOT_URL=http://gitea:3000/ \
    --env GITEA__service__DISABLE_REGISTRATION=true \
    "$GITEA_IMAGE" >/dev/null

attempt=0
until docker exec "$CONTAINER_NAME" curl --fail --silent http://127.0.0.1:3000/api/healthz >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
        docker logs "$CONTAINER_NAME"
        echo "Gitea가 제한 시간 안에 준비되지 않았습니다." >&2
        exit 1
    fi
    sleep 1
done

step 2 "실습 사용자와 공개 저장소를 생성합니다."
docker exec --user git "$CONTAINER_NAME" gitea admin user create \
    --config /data/gitea/conf/app.ini \
    --username "$PRACTICE_USER" \
    --password "$PRACTICE_PASSWORD" \
    --email practice@example.invalid \
    --must-change-password=false >/dev/null

docker exec "$CONTAINER_NAME" curl --fail --silent \
    --user "$PRACTICE_USER:$PRACTICE_PASSWORD" \
    --header 'Content-Type: application/json' \
    --data "{\"name\":\"$REPOSITORY_NAME\",\"private\":false}" \
    http://127.0.0.1:3000/api/v1/user/repos >/dev/null

step 3 "현재 저장소를 Gitea 원격 저장소에 게시합니다."
docker exec "$CONTAINER_NAME" sh -eu -c '
    git config --global --add safe.directory /source
    git config --global --add safe.directory /source/.git
    git clone --quiet /source /tmp/original
    cd /tmp/original
    git checkout --quiet -B main origin/main
    git remote set-url origin http://practice:local-practice-password@gitea:3000/practice/quiz-practice.git
    git push --quiet --set-upstream origin main
'

step 4 "별도 작업 디렉터리에 clone하고 변경을 commit 및 push합니다."
docker exec "$CONTAINER_NAME" sh -eu -c '
    git clone --quiet http://gitea:3000/practice/quiz-practice.git /tmp/cloned
    cd /tmp/cloned
    git config user.name "Clone Practice"
    git config user.email practice@example.invalid
    printf "clone 작업 디렉터리에서 생성한 변경\n" > clone-pull-proof.txt
    git add clone-pull-proof.txt
    git commit --quiet -m "Docs: clone과 pull 실습 변경 추가"
    git remote set-url origin http://practice:local-practice-password@gitea:3000/practice/quiz-practice.git
    git push --quiet origin main
'

step 5 "기존 작업 디렉터리에서 pull하고 반영 결과를 검증합니다."
docker exec "$CONTAINER_NAME" sh -eu -c '
    cd /tmp/original
    git pull --quiet --ff-only
    test "$(cat clone-pull-proof.txt)" = "clone 작업 디렉터리에서 생성한 변경"
    git log -2 --oneline --decorate
'

printf '\nPASS: clone → commit → push → pull 실습이 격리된 Gitea에서 완료되었습니다.\n'
