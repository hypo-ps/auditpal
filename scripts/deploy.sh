#!/usr/bin/env bash
# Deploy AuditPal to an existing EC2 instance via SSH + docker-compose.
#
# Configuration is read from environment variables or CLI flags:
#   EC2_HOST    (required)  Public IP or DNS of the EC2 instance
#   EC2_USER    (optional)  SSH user, default: ec2-user
#   SSH_KEY     (optional)  Path to private key, default: ~/.ssh/id_rsa
#   REMOTE_DIR  (optional)  Remote project path, default: /home/$EC2_USER/auditpal
#   APP_PORT    (optional)  Port the app is exposed on, default: 8501
#
# Usage:
#   ./scripts/deploy.sh --host 1.2.3.4 --key ~/.ssh/my-key.pem
#   EC2_HOST=1.2.3.4 SSH_KEY=~/.ssh/my-key.pem ./scripts/deploy.sh

set -euo pipefail

EC2_HOST="${EC2_HOST:-}"
EC2_USER="${EC2_USER:-ec2-user}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
REMOTE_DIR="${REMOTE_DIR:-}"
APP_PORT="${APP_PORT:-8501}"

print_usage() {
    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)   EC2_HOST="$2";   shift 2 ;;
        --user)   EC2_USER="$2";   shift 2 ;;
        --key)    SSH_KEY="$2";    shift 2 ;;
        --dir)    REMOTE_DIR="$2"; shift 2 ;;
        --port)   APP_PORT="$2";   shift 2 ;;
        -h|--help) print_usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; print_usage; exit 1 ;;
    esac
done

if [[ -z "$EC2_HOST" ]]; then
    echo "Error: EC2_HOST is required (use --host or set EC2_HOST env var)" >&2
    print_usage
    exit 1
fi

if [[ ! -f "$SSH_KEY" ]]; then
    echo "Error: SSH key not found at $SSH_KEY" >&2
    exit 1
fi

REMOTE_DIR="${REMOTE_DIR:-/home/$EC2_USER/auditpal}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
SSH_TARGET="$EC2_USER@$EC2_HOST"

echo "==> Deploying AuditPal to $SSH_TARGET:$REMOTE_DIR"

echo "==> Verifying SSH connectivity"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" 'echo "SSH OK on $(hostname)"'

echo "==> Verifying docker and docker-compose are installed on remote"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" bash -se <<'REMOTE_CHECK'
set -e
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is not installed on the EC2 instance." >&2
    echo "Install it first, e.g.:" >&2
    echo "  sudo yum install -y docker && sudo systemctl enable --now docker" >&2
    echo "  sudo usermod -aG docker \$USER && newgrp docker" >&2
    exit 1
fi
if ! (command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1); then
    echo "Error: docker-compose (v1) or 'docker compose' (v2 plugin) is required." >&2
    exit 1
fi
REMOTE_CHECK

echo "==> Ensuring remote directory exists: $REMOTE_DIR"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mkdir -p '$REMOTE_DIR'"

echo "==> Syncing project files via rsync (preserving remote credentials/ and data/)"
rsync -az --delete \
    --exclude '.venv/' \
    --exclude '.git/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'credentials/' \
    --exclude 'data/' \
    --exclude '.DS_Store' \
    -e "ssh ${SSH_OPTS[*]}" \
    "$PROJECT_ROOT/" "$SSH_TARGET:$REMOTE_DIR/"

echo "==> Verifying NotebookLM credentials are present on the remote"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" bash -se <<REMOTE_CRED_CHECK
set -e
if [[ ! -f "$REMOTE_DIR/credentials/storage_state.json" ]]; then
    echo "Error: $REMOTE_DIR/credentials/storage_state.json not found." >&2
    echo "Place your NotebookLM credentials there before re-running, e.g.:" >&2
    echo "  scp -i KEY ~/.notebooklm/storage_state.json $SSH_TARGET:$REMOTE_DIR/credentials/" >&2
    exit 1
fi
REMOTE_CRED_CHECK

echo "==> Building and starting containers on remote"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" bash -se <<REMOTE_DEPLOY
set -e
cd "$REMOTE_DIR"
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    COMPOSE="docker compose"
fi

# Bring the project down (with orphans) so re-deploys after a service or
# project rename free up bound ports cleanly.
\$COMPOSE down --remove-orphans || true

# Surface (but don't auto-kill) any *foreign* container still binding the
# app port, so the failure mode is obvious instead of a cryptic compose error.
if docker ps --format '{{.Names}} {{.Ports}}' | grep -E ":${APP_PORT}->" >/dev/null; then
    echo "Error: another container is already bound to port ${APP_PORT}:" >&2
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}' | grep -E "(NAMES|:${APP_PORT}->)" >&2
    echo "Stop/remove it manually and re-run this script." >&2
    exit 1
fi

\$COMPOSE up -d --build
\$COMPOSE ps
REMOTE_DEPLOY

echo ""
echo "==> Deployment complete."
echo "    App should be reachable at: http://$EC2_HOST:$APP_PORT"
echo "    (Make sure your EC2 security group allows inbound TCP on port $APP_PORT)"
