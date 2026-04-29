#!/usr/bin/env bash
# GitHub environment detection helper for Hermes Agent skills.
#
# Usage:
#   source skills/github/github-auth/scripts/gh-env.sh
#
# Exports:
#   GH_AUTH_METHOD = gh | curl | none
#   GITHUB_TOKEN   = token for curl/API mode when discovered
#   GH_USER        = GitHub username if resolvable
#   GH_OWNER / GH_REPO / GH_OWNER_REPO when inside a git repo with origin on GitHub

GH_AUTH_METHOD="none"
GH_USER=""
GH_OWNER=""
GH_REPO=""
GH_OWNER_REPO=""

_KEY_NAME="GITHUB_TOKEN"
_EXISTING_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_TOKEN="$_EXISTING_TOKEN"
unset _EXISTING_TOKEN

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  GH_AUTH_METHOD="gh"
  GH_USER=$(gh api user --jq '.login' 2>/dev/null)
elif [ -n "$GITHUB_TOKEN" ]; then
  GH_AUTH_METHOD="curl"
else
  if [ -f "$HOME/.hermes/.env" ]; then
    _token_line=$(grep "^${_KEY_NAME}=" "$HOME/.hermes/.env" 2>/dev/null | head -1)
    if [ -n "$_token_line" ]; then
      GITHUB_TOKEN=${_token_line#*=}
      GITHUB_TOKEN=$(printf '%s' "$GITHUB_TOKEN" | tr -d '
')
      GH_AUTH_METHOD="curl"
    fi
    unset _token_line
  fi

  if [ "$GH_AUTH_METHOD" = "none" ] && [ -f "$HOME/.git-credentials" ]; then
    _cred_line=$(grep 'github.com' "$HOME/.git-credentials" 2>/dev/null | head -1)
    if [ -n "$_cred_line" ]; then
      GITHUB_TOKEN=$(printf '%s' "$_cred_line" | sed 's|https://[^:]*:\([^@]*\)@.*||')
      if [ -n "$GITHUB_TOKEN" ]; then
        GH_AUTH_METHOD="curl"
      fi
    fi
    unset _cred_line
  fi
fi

if [ "$GH_AUTH_METHOD" = "curl" ] && [ -z "$GH_USER" ] && [ -n "$GITHUB_TOKEN" ]; then
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('login', ''))" 2>/dev/null)
fi

_remote_url=$(git remote get-url origin 2>/dev/null)
if [ -n "$_remote_url" ] && printf '%s' "$_remote_url" | grep -q 'github.com'; then
  GH_OWNER_REPO=$(printf '%s' "$_remote_url" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
  GH_OWNER=$(printf '%s' "$GH_OWNER_REPO" | cut -d/ -f1)
  GH_REPO=$(printf '%s' "$GH_OWNER_REPO" | cut -d/ -f2)
fi
unset _remote_url _KEY_NAME

export GH_AUTH_METHOD GITHUB_TOKEN GH_USER GH_OWNER GH_REPO GH_OWNER_REPO

echo "GitHub Auth: $GH_AUTH_METHOD"
[ -n "$GH_USER" ] && echo "User: $GH_USER"
[ -n "$GH_OWNER_REPO" ] && echo "Repo: $GH_OWNER_REPO"
[ "$GH_AUTH_METHOD" = "none" ] && echo "⚠ Not authenticated — see github-auth skill"
