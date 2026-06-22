#!/usr/bin/env bash
# Demo walkthrough — GDG Melbourne · AI Agent Conference Lessons · 2026-06-24
#
# Usage:  cd 72-2026.06-stand-in-agent-attendee && ./demo.sh
#
# Shell commands are offered to run in place.
# Manual steps (browser, console) pause until you press Enter.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AMBIENT_DIR="$SCRIPT_DIR/ai-attendee-ambient"
STANDARD_DIR="$SCRIPT_DIR/ai-attendee-standard"
SIM_DIR="$(cd "$SCRIPT_DIR/../72-2026.06-stand-in-agent-backend-sim" && pwd)"

# ── colours ───────────────────────────────────────────────────────────────────
BOLD="\033[1m"; RESET="\033[0m"
CYAN="\033[36m"; GREEN="\033[32m"; YELLOW="\033[33m"; MAGENTA="\033[35m"; RED="\033[31m"

# ── load env ──────────────────────────────────────────────────────────────────
if [ -f "$AMBIENT_DIR/.setup-env" ]; then
  # shellcheck source=/dev/null
  source "$AMBIENT_DIR/.setup-env"
fi
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
SIM_URL="${SIMULATION_BASE_URL:-http://localhost:8000}"
SCHEDULER_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

# ── helpers ───────────────────────────────────────────────────────────────────
divider() {
  echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

step() {
  local num="$1"; shift
  divider
  echo -e "  ${BOLD}STEP $num — $*${RESET}\n"
}

info()    { echo -e "  ${CYAN}ℹ  $*${RESET}"; }
concept() { echo -e "  ${MAGENTA}◆  CONCEPT: $*${RESET}"; }

manual_step() {
  echo -e "  ${YELLOW}▶  MANUAL:${RESET} $*"
  echo ""
  read -rp "  Press Enter when done... " _
  echo ""
}

run_step() {
  local description="$1"
  local cmd="$2"
  local dir="${3:-$SCRIPT_DIR}"

  echo -e "  ${GREEN}▶  ${description}${RESET}"
  echo -e "     ${BOLD}\$ ${cmd}${RESET}"
  [ "$dir" != "$SCRIPT_DIR" ] && echo -e "     ${CYAN}(in: $(basename "$dir")/)${RESET}"
  echo ""
  read -rp "  [Enter] run  /  [s] skip: " _choice
  echo ""
  if [[ "$_choice" != "s" && "$_choice" != "S" ]]; then
    (cd "$dir" && eval "$cmd") && echo -e "  ${GREEN}✓ done${RESET}" || echo -e "  ${RED}✗ command exited with error${RESET}"
  else
    echo -e "  ${YELLOW}⏭  skipped${RESET}"
  fi
  echo ""
}

pause() {
  read -rp "  Press Enter to continue... " _
}

# ── preflight ─────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${CYAN}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║       Stand-In Agent — Live Demo Walkthrough              ║"
echo "  ║       GDG Melbourne · AI Agent Conference Lessons          ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo -e "  Project:   ${BOLD}${PROJECT_ID:-NOT SET}${RESET}"
echo -e "  Sim URL:   ${BOLD}${SIM_URL}${RESET}"
echo -e "  Scheduler: ${BOLD}${SCHEDULER_LOCATION}${RESET}"
echo ""
if [ -z "$PROJECT_ID" ]; then
  echo -e "  ${RED}⚠  GCP_PROJECT_ID not set. Set it in ${AMBIENT_DIR}/.setup-env${RESET}"
  echo ""
fi
read -rp "  Ready? Press Enter to start... " _
echo ""

# =============================================================================
#  PART 1 — AMBIENT AGENT
# =============================================================================

step 1 "Create a persistent session for the Ambient agent"
info "State (last caption timestamp seen) lives in this Vertex AI session."
info "Each Scheduler tick reuses the same session → no duplicate captions."
info "Session ID saved to: ai-attendee-ambient/.ambient_session_id"
echo ""
run_step "Create ambient session" "task session:create" "$AMBIENT_DIR"
pause

# -----------------------------------------------------------------------------
step 2 "Start (or restart) the backend simulation stream"
info "The sim server is on Cloud Run and starts in idle state."
info "POST /sim/start resets the clock to t=0 and begins releasing captions."
echo ""
run_step "Start simulation" \
  "curl -s -X POST '${SIM_URL}/sim/start' | python3 -m json.tool"
echo ""
run_step "Verify stream is live" \
  "curl -s '${SIM_URL}/streams' | python3 -m json.tool"
pause

# -----------------------------------------------------------------------------
step 3 "Fire the Cloud Scheduler job (first ambient tick)"
info "This manually triggers ambient-cron without waiting for its schedule."
info "The ambient agent wakes up, checks /streams, fetches /transcript, emits alerts."
echo ""
run_step "Trigger scheduler job" \
  "gcloud scheduler jobs run ambient-cron --location='${SCHEDULER_LOCATION}' --project='${PROJECT_ID}'" \
  "$AMBIENT_DIR"
echo ""
info "Wait ~10 seconds for the agent to complete its sweep, then check logs."
echo ""
run_step "Tail agent logs (last 20 lines)" "task logs -- 20" "$AMBIENT_DIR"
pause

# -----------------------------------------------------------------------------
step 4 "Show the running system in the GCP Console"
echo ""
manual_step "Open Agent Engine → select the ambient agent → Playground.
     Watch the session events from the last tick.
     URL: https://console.cloud.google.com/agent-platform/runtimes"
echo ""
manual_step "Switch to Cloud Scheduler and show the cron job (ambient-cron).
     URL: https://console.cloud.google.com/cloudscheduler"
echo ""
concept "Function Calls"
echo ""
echo -e "     When the LLM returns ${BOLD}content.parts[0].text${RESET} only → execution stops."
echo -e "     When it returns ${BOLD}content.parts[*].functionCall${RESET} → the ADK"
echo -e "     runtime invokes the tool and sends results back in the next turn."
echo -e "     You can observe this in the playground's turn-by-turn trace."
echo ""
manual_step "Show a trace: Cloud Console → Trace Explorer (or playground sidebar)"
pause

# -----------------------------------------------------------------------------
step 5 "Pause the Cloud Scheduler (stop ambient ticks)"
info "No more ticks will fire until you resume the job."
echo ""
run_step "Pause scheduler job" \
  "gcloud scheduler jobs pause ambient-cron --location='${SCHEDULER_LOCATION}' --project='${PROJECT_ID}'"
pause

# =============================================================================
#  PART 2 — STANDARD AGENT
# =============================================================================

step 6 "Restart the simulation stream for the Standard agent demo"
info "Reset the sim clock to t=0 so the standard agent sees the full transcript."
echo ""
run_step "Restart simulation" \
  "curl -s -X POST '${SIM_URL}/sim/start' | python3 -m json.tool"
pause

# -----------------------------------------------------------------------------
step 7 "Demo the Standard agent in the Agent Engine playground"
echo ""
manual_step "Open the standard agent playground:
     URL: https://console.cloud.google.com/agent-platform/runtimes
     → Select the 'ai-attendee-standard' engine → Playground
     → Send: 'Attend the conference and alert me on relevant topics'"
echo ""
manual_step "Watch the agent loop: get_streams → get_sim_transcript → analyse → repeat.
     It drives itself until status == 'finished'."
echo ""
concept "agents-cli"
echo ""
echo -e "     ${BOLD}agents-cli${RESET} wraps ADK scaffolding so you don't write boilerplate."
echo -e "     Key commands used in this project:"
echo -e "       agents-cli run '...'    — one-shot local run"
echo -e "       agents-cli playground   — local dev server with UI"
echo -e "       agents-cli deploy       — package + deploy to Agent Engine"
echo -e "     The manifest (agents-cli-manifest.yaml) describes the agent's"
echo -e "     entry point, env vars, and resource requirements."
echo ""
manual_step "Show traces for the standard agent run (Cloud Trace or playground sidebar)"
pause

# =============================================================================
#  DONE
# =============================================================================

divider
echo ""
echo -e "  ${BOLD}${GREEN}Demo complete!${RESET}"
echo ""
echo -e "  ${CYAN}Cleanup (if needed):${RESET}"
echo -e "    Resume scheduler:   gcloud scheduler jobs resume ambient-cron --location=${SCHEDULER_LOCATION} --project=${PROJECT_ID}"
echo -e "    Reset sim to idle:  curl -X POST ${SIM_URL}/sim/reset"
echo ""
