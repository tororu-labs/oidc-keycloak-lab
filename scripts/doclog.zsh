#!/usr/bin/env zsh

note() {
  echo "### $(date '+%F %T') | $*"
}

doclog() {
  emulate -L zsh

  local raw="${1:-session}"
  local name="${raw:t:r}"
  local dir="scratch/logs/$name"
  local log tmpdir rc

  mkdir -p "$dir" || return 1
  log="$dir/$(date +%Y%m%d-%H%M%S).log"
  tmpdir=$(mktemp -d /tmp/doclog.XXXXXX) || return 1

  trap 'rm -rf "$tmpdir"' EXIT INT TERM

  {
    echo "note() {"
    echo "  echo \"### \$(date '+%F %T') | \$*\""
    echo "}"
    echo "HISTFILE=\"\$ZDOTDIR/.zsh_history\""
    echo "note 'logging started'"
    echo "echo \"### log file: \$DOCLOG_FILE\""
  } >"$tmpdir/.zshrc"

  echo "logging to: $log"
  DOCLOG_FILE="$log" ZDOTDIR="$tmpdir" script -q "$log" zsh -i
  rc=$?

  rm -rf "$tmpdir"
  trap - EXIT INT TERM
  return "$rc"
}

doclog_usage() {
  cat <<'EOF'
使い方:
  source scripts/doclog.zsh
  doclog docs/05_SetupFastAPI-OIDCLogin.md

ログ中で使えるメモ:
  note 'Step 1: demo-bff client を作成'
EOF
}

if [[ "${zsh_eval_context[-1]}" != "file" ]]; then
  if [[ $# -eq 0 ]]; then
    doclog_usage
  else
    doclog "$@"
  fi
fi
