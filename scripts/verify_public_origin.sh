#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
GIT_CLIENT_IMAGE=${GIT_CLIENT_IMAGE:-docker.gitea.com/gitea:1.24.7}
ORIGIN_URL=$(git -C "$PROJECT_ROOT" remote get-url origin)

case "$ORIGIN_URL" in
    http://*|https://*) ;;
    *)
        echo "FAIL: origin이 비인증 HTTP(S) 접근을 검증할 수 있는 주소가 아닙니다: $ORIGIN_URL" >&2
        exit 1
        ;;
esac

authority=${ORIGIN_URL#*://}
authority=${authority%%/*}
case "$authority" in
    *@*)
        echo "FAIL: origin URL에 사용자 정보나 자격 증명이 포함되어 있습니다." >&2
        exit 1
        ;;
esac

printf 'origin=%s\n' "$ORIGIN_URL"
printf 'client_image=%s\n' "$GIT_CLIENT_IMAGE"
printf 'authentication=disabled (clean container, empty environment, no host mounts or prompts)\n'

docker run --rm \
    --env "ORIGIN_URL=$ORIGIN_URL" \
    --entrypoint sh \
    "$GIT_CLIENT_IMAGE" \
    -eu -c '
        mkdir -p /tmp/empty-home
        env -i \
            HOME=/tmp/empty-home \
            PATH="$PATH" \
            ORIGIN_URL="$ORIGIN_URL" \
            GIT_CONFIG_GLOBAL=/dev/null \
            GIT_CONFIG_NOSYSTEM=1 \
            GIT_TERMINAL_PROMPT=0 \
            GIT_ASKPASS=/bin/false \
            git -c credential.helper= -c core.askPass=/bin/false \
                ls-remote --exit-code "$ORIGIN_URL" HEAD refs/heads/main
    '

echo "PASS: 인증 설정이 없는 컨테이너에서 origin의 HEAD와 main을 조회했습니다."
