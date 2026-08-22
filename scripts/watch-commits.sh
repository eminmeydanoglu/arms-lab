#!/usr/bin/env bash
# Commit watcher: fetches origin/main periodically; on new commits,
# rebase local branch and report what changed.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${WATCH_BRANCH:-main}"
REMOTE="${WATCH_REMOTE:-origin}"
POLL_SECS="${WATCH_POLL_SECS:-30}"
LOG_TAIL="${WATCH_LOG_TAIL:-10}"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

cd "$REPO"

# Ensure we track the remote branch
git config "branch.$BRANCH.remote" "$REMOTE" 2>/dev/null || true
git config "branch.$BRANCH.merge" "refs/heads/$BRANCH" 2>/dev/null || true

log "watching $REMOTE/$BRANCH (poll every ${POLL_SECS}s)"
while true; do
  git fetch --quiet "$REMOTE" "$BRANCH" 2>/dev/null || true

  if git rev-parse --verify -q "$BRANCH" >/dev/null 2>&1; then
    NEW_COUNT="$(git rev-list --count "$BRANCH..$REMOTE/$BRANCH" 2>/dev/null || echo 0)"
    if [ "$NEW_COUNT" -gt 0 ]; then
      log "pulled $NEW_COUNT new commit(s) from $REMOTE/$BRANCH"
      if git pull --rebase "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
        log "new commits:"
        git log --oneline -"$NEW_COUNT"
      else
        log "pull failed (conflict?); manual intervention needed"
      fi
    fi
  else
    log "local branch $BRANCH missing; creating from $REMOTE/$BRANCH"
    git switch -c "$BRANCH" --track "$REMOTE/$BRANCH" 2>/dev/null || true
  fi

  sleep "$POLL_SECS"
done
