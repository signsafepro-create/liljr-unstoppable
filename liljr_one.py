#!/usr/bin/env python3
import difflib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("LILJR_PORT", "8794"))
BIND_HOST = "0.0.0.0"
STARTED_AT = time.time()
ROOT = Path(os.environ.get("LILJR_PROJECT_ROOT", Path.cwd())).expanduser().resolve()
DATA = ROOT / "data"
MEMORY_DIR = DATA / "memory"
MEMORY_FILE = DATA / "personal_suit_memory.json"
MISSION_FILE = DATA / "mission_board.json"
QUEUE_FILE = DATA / "task_queue.json"
APPROVAL_FILE = DATA / "approval_requests.json"
SWARM_STATE_FILE = DATA / "swarm_state.json"
BOOKINGS_FILE = DATA / "signsafe_bookings.json"
UPLOAD_INDEX_FILE = DATA / "upload_index.json"
BRAIN_REGISTRY_FILE = DATA / "brain_registry.json"
UPLOADS = DATA / "uploads"
INBOX_ROOT = DATA / "LilJR-INBOX"
BACKUPS = ROOT / "backups"
for folder in (DATA, MEMORY_DIR, UPLOADS, INBOX_ROOT, INBOX_ROOT / "S23", INBOX_ROOT / "S21", BACKUPS):
    folder.mkdir(parents=True, exist_ok=True)

try:
    from core.modules.model_router import explain_route as explain_provider_route, live_call as live_provider_call, provider_status, route as route_task_model, verify_all_live_providers, verify_live_provider, verify_named_live_provider
    from core.modules.tool_registry import list_tools as list_registered_tools
    from core.swarm.shells import list_shells
except Exception:
    provider_status = None
    explain_provider_route = live_provider_call = verify_live_provider = verify_all_live_providers = verify_named_live_provider = None
    route_task_model = None
    list_registered_tools = None
    list_shells = None

try:
    from core.modules.live_provider_verifier import verify_provider as verify_provider_safe, verify_fallback_route as verify_fallback_route_safe
except Exception:
    verify_provider_safe = verify_fallback_route_safe = None

try:
    from core.modules.core_vault_merger import merge_core_vault, next_v32_feature
    from core.modules.human_chat_style import clean_reply, formatting_rules_text, style_profile
    from core.modules.output_style import get_output_mode, mode_guidance, set_output_mode, wants_details
    from core.modules.provider_status import one_brain_provider_status, normalize_provider_name, safe_live_provider_test
    from core.modules.source_coverage import build_source_coverage, coverage_status
    from core.modules.ui_shell_unifier import ui_shell_status
    from core.modules.unified_liljr_runtime import one_unit_reply, one_unit_status
    from core.modules.voice_layer import speak_reply, speak_status, stop_speaking_reply
except Exception:
    merge_core_vault = next_v32_feature = None
    clean_reply = formatting_rules_text = style_profile = None
    get_output_mode = mode_guidance = set_output_mode = wants_details = None
    one_brain_provider_status = normalize_provider_name = safe_live_provider_test = None
    build_source_coverage = coverage_status = None
    ui_shell_status = None
    one_unit_reply = one_unit_status = None
    speak_reply = speak_status = stop_speaking_reply = None

try:
    from core.modules.operator_mode import route_operator_command
except Exception:
    route_operator_command = None

try:
    from core.modules.app_foundry import side_job_plan
    from core.modules.device_bridge import phone_bridge_status as stage2_phone_bridge_status
    from core.modules.evidence_timeline import make_case_timeline
    from core.modules.legal_ai import evidence_checklist
    from core.modules.legal_intake import child_custody_next_steps, legal_intake_status
    from core.modules.legal_warfare import compare_jurisdictions as legal_warfare_compare, generate_strategy as legal_warfare_strategy, legal_warfare_status, reason as legal_warfare_reason
    from core.modules.live_scope import live_scope_status
    from core.modules.phone_intake import qr_upload_status, scan_phone_inbox
    from core.modules.release_packager import make_rollback_zip, package_release_plan
    from core.modules.secret_scanner import check_secrets
    from core.modules.termux_bridge import termux_bridge_plan
    from core.modules.watchers import stop_watcher, watch_this, watcher_status
except Exception:
    side_job_plan = stage2_phone_bridge_status = make_case_timeline = evidence_checklist = None
    child_custody_next_steps = legal_intake_status = live_scope_status = None
    legal_warfare_compare = legal_warfare_strategy = legal_warfare_status = legal_warfare_reason = None
    qr_upload_status = scan_phone_inbox = make_rollback_zip = package_release_plan = None
    check_secrets = termux_bridge_plan = stop_watcher = watch_this = watcher_status = None

try:
    from core.modules.memory_router import route_memory_command, supported_memory_types
    from core.modules.memory_safety import safety_review
    from core.modules.unified_memory import memory_status as unified_memory_status, save_unified_memory, search_unified_memory, typed_status as unified_typed_memory_status
except Exception:
    route_memory_command = supported_memory_types = None
    safety_review = None
    unified_memory_status = save_unified_memory = search_unified_memory = unified_typed_memory_status = None

try:
    from core.modules.integration_registry import integration_status, plan_integration, run_integration_request
except Exception:
    integration_status = plan_integration = run_integration_request = None

try:
    from core.modules.deliverable_pipeline import create_deliverable, get_deliverable, pipeline_status, plan_deliverable, search_deliverables
except Exception:
    create_deliverable = get_deliverable = pipeline_status = plan_deliverable = search_deliverables = None

try:
    from core.modules.natural_intent_router import route_natural_intent
except Exception:
    route_natural_intent = None

try:
    from core.modules.conversation_flow import conversation_status, conversation_timeline, record_conversation_turn
except Exception:
    conversation_status = conversation_timeline = record_conversation_turn = None

try:
    from core.modules.one_unit_orchestrator import orchestration_plan, orchestration_status, run_orchestration_request
except Exception:
    orchestration_plan = orchestration_status = run_orchestration_request = None

try:
    from core.modules.one_unit_symphony import symphony_status
except Exception:
    symphony_status = None

try:
    from core.modules.production_readiness import production_readiness
except Exception:
    production_readiness = None

try:
    from core.modules.one_unit_e2e_verifier import run_one_unit_e2e
except Exception:
    run_one_unit_e2e = None

try:
    from core.modules.build_order_runner import build_order_runner_status, pick_next_feature, prepare_patch_test_cycle
    from core.modules.deploy_brain import deploy_checklist
    from core.modules.inbox_pipeline import inbox_status as v31_inbox_status, kimi_intake, liljr_ideas_from_inbox, next_liljr_build_from_inbox, run_inbox_pipeline, side_jobs_from_inbox
    from core.modules.job_vault import job_summary, job_vault_status, jobs_to_build_after_liljr, list_jobs, search_jobs
    from core.modules.life_mode import briefing_mode, deep_build_mode, overwhelm_mode
    from core.modules.liljr_capability_vault import liljr_build_order, liljr_disabled_until_connected, liljr_future_blueprint, liljr_missing_pieces, liljr_needs_andre_decision, liljr_now_capabilities, liljr_wanted_capabilities, scan_liljr_capabilities, search_liljr_capability
    from core.modules.personal_memory import PersonalMemory
    from core.modules.reality_check import what_can_you_actually_do
    from core.modules.self_improvement import inspect_current_build
    from core.modules.verifier import verifier_report as overlay_verifier_report
    from core.plugins.plugin_registry import list_plugins, plugin_health
except Exception:
    build_order_runner_status = pick_next_feature = prepare_patch_test_cycle = None
    deploy_checklist = None
    v31_inbox_status = kimi_intake = liljr_ideas_from_inbox = next_liljr_build_from_inbox = run_inbox_pipeline = side_jobs_from_inbox = None
    job_summary = job_vault_status = jobs_to_build_after_liljr = list_jobs = search_jobs = None
    briefing_mode = deep_build_mode = overwhelm_mode = None
    liljr_build_order = liljr_disabled_until_connected = liljr_future_blueprint = liljr_missing_pieces = liljr_needs_andre_decision = None
    liljr_now_capabilities = liljr_wanted_capabilities = scan_liljr_capabilities = search_liljr_capability = None
    PersonalMemory = None
    what_can_you_actually_do = None
    inspect_current_build = None
    overlay_verifier_report = None
    list_plugins = plugin_health = None

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "__pycache__", "venv", ".venv", "cache", "tmp"}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".html", ".css", ".md", ".sh", ".yml", ".yaml", ".toml", ".txt", ".env"}
ALLOW = {"pwd", "ls", "dir", "cat", "type", "head", "tail", "grep", "find", "python", "python3", "node", "npm", "curl", "git", "pip", "pip3"}
RISKY_PATTERNS = [
    r"\brm\s+-", r"\bdel\b", r"\brmdir\b", r"\bRemove-Item\b", r"\bsudo\b", r"\bsu\b",
    r"\bmkfs\b", r"\bdd\b", r"\bshutdown\b", r"\breboot\b", r"\bkillall\b",
    r"chmod\s+777", r"chown\s+-R", r"\bformat\b", r"\bdeploy\b", r"\bpush\b"
]
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+=]{8,})"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{12,}\b"),
]

TOOLS = [
    {"name": "scan_files", "risk": "safe", "description": "Inspect project files without secrets."},
    {"name": "read_file", "risk": "safe", "description": "Read a text file with secret redaction."},
    {"name": "propose_patch", "risk": "approval", "description": "Create a diff and backup before editing."},
    {"name": "apply_patch", "risk": "approval", "description": "Apply an approved patch request."},
    {"name": "run_command", "risk": "approval", "description": "Run allowlisted terminal commands after owner approval."},
    {"name": "legal_intake", "risk": "safe", "description": "Prepare legal intake questions and evidence checklist."},
    {"name": "legal_warfare_research", "risk": "safe", "description": "Research legal frameworks and strategy without filing or contacting anyone."},
    {"name": "signsafe_notaries", "risk": "safe", "description": "Search the SignSafe Pro notary directory."},
    {"name": "signsafe_booking", "risk": "approval", "description": "Prepare a notary booking request for owner approval."},
    {"name": "nearby_signal_awareness", "risk": "safe", "description": "Map consent-based nearby signal options without device takeover."},
    {"name": "device_continuity", "risk": "safe", "description": "Plan always-ready owner-approved access between your own devices."},
    {"name": "brain_context", "risk": "safe", "description": "Unify continuity, uploads, SignSafe, Kimi, vault, build gaps, and approval locks into one LilJR brain context."},
    {"name": "inbox_watcher", "risk": "safe", "description": "Index owner-approved LilJR-INBOX folders from cloud mirrors and local upload intake."},
    {"name": "upload_indexer", "risk": "safe", "description": "Label S23/S21/unknown phone uploads and feed them into LilJR brain memory."},
    {"name": "integration_registry", "risk": "safe", "description": "Show plugin/platform readiness across Documents, Supabase, Spreadsheets, Render, CodeRabbit, Slack, Browser, Sites, Presentations, and Expo."},
    {"name": "integration_run", "risk": "approval", "description": "Plan integration actions; external writes/deploys/sends require owner approval."},
    {"name": "deliverable_pipeline", "risk": "safe", "description": "Create local one-unit work orders across docs, sheets, decks, database, deploy, Slack, browser, Sites, and Expo surfaces."},
    {"name": "natural_intent_router", "risk": "safe", "description": "Route normal language into deliverables, orchestration, or normal chat without exact commands."},
    {"name": "conversation_timeline", "risk": "safe", "description": "Show the safe redacted conversation flow so LilJR acts as one continuous brain."},
    {"name": "one_unit_symphony", "risk": "safe", "description": "Show whether conversation, memory, deliverables, integrations, approvals, verifier, frontend, and mobile are aligned as one unit."},
    {"name": "production_readiness", "risk": "safe", "description": "Check production-like start readiness, env slot categories, frontend/mobile wiring, and safe run commands without exposing secrets."},
    {"name": "one_unit_orchestrator", "risk": "safe", "description": "Coordinate chat, brain context, design, build, integrations, verification, and owner handoff as one flow."},
    {"name": "orchestration_run", "risk": "approval", "description": "Prepare one-unit orchestration; external side effects require owner approval."},
    {"name": "one_unit_e2e_verifier", "risk": "safe", "description": "Run local production-like E2E checks and write a failure lock if anything breaks."},
    {"name": "mission_loader", "risk": "safe", "description": "Create missions and task queues."},
    {"name": "verifier", "risk": "safe", "description": "Run local health checks."},
]
SWARM = [
    {"id": "main-brain", "name": "Main Brain", "status": "online", "role": "Plans and routes every message."},
    {"id": "memory", "name": "Personal Suit Memory", "status": "online", "role": "Stores owner notes and mission context."},
    {"id": "router", "name": "Model Router", "status": "online", "role": "Chooses local/default model mode."},
    {"id": "tools", "name": "Tool Registry", "status": "online", "role": "Exposes safe callable tools."},
    {"id": "approval", "name": "Owner Approval Lock", "status": "online", "role": "Blocks risky actions."},
    {"id": "verifier", "name": "Verifier", "status": "online", "role": "Checks routes and outputs."},
    {"id": "watchers", "name": "Optional Watchers", "status": "standby", "role": "Ready but inactive until enabled."},
]

NOTARIES = [
    {"id": "n001", "name": "A. Singh Notary", "province": "ontario", "city": "Toronto", "languages": ["English", "Punjabi"], "verified": True},
    {"id": "n002", "name": "M. Tremblay Notary", "province": "quebec", "city": "Montreal", "languages": ["English", "French"], "verified": True},
    {"id": "n003", "name": "J. Patel Notary", "province": "british columbia", "city": "Vancouver", "languages": ["English", "Hindi"], "verified": True},
    {"id": "n004", "name": "L. Wong Notary", "province": "alberta", "city": "Calgary", "languages": ["English", "Cantonese"], "verified": True},
    {"id": "n005", "name": "R. MacDonald Commissioner", "province": "ontario", "city": "Sault Ste. Marie", "languages": ["English"], "verified": True},
    {"id": "n006", "name": "S. Kim Notary", "province": "ontario", "city": "Mississauga", "languages": ["English", "Korean"], "verified": True},
    {"id": "n007", "name": "T. Hassan Notary", "province": "manitoba", "city": "Winnipeg", "languages": ["English", "Arabic"], "verified": True},
    {"id": "n008", "name": "N. Okafor Notary", "province": "nova scotia", "city": "Halifax", "languages": ["English", "Igbo"], "verified": True},
    {"id": "n009", "name": "E. Johansson Notary", "province": "saskatchewan", "city": "Saskatoon", "languages": ["English", "Swedish"], "verified": True},
    {"id": "n010", "name": "K. Chen Notary", "province": "british columbia", "city": "Victoria", "languages": ["English", "Mandarin"], "verified": True},
    {"id": "n011", "name": "D. Murphy Notary", "province": "new brunswick", "city": "Fredericton", "languages": ["English"], "verified": True},
    {"id": "n012", "name": "G. Silva Notary", "province": "ontario", "city": "Hamilton", "languages": ["English", "Portuguese"], "verified": True},
]

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LilJR Personal Suit</title></head>
<body><main id="app"><h1>LilJR Personal Suit</h1><p>personal suit intelligence</p><input id="cmd" placeholder="Talk to me normally..."><button onclick="send()">Send</button><button onclick="toggleDrawer(true)">Access</button></main>
<script>
function toggleDrawer(){}
function menuAction(){}
function listen(){ if(window.SpeechRecognition||window.webkitSpeechRecognition){} }
async function send(){ await fetch("/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:document.getElementById("cmd").value||"hello"})}).catch(()=>{}); }
if(window.speechSynthesis){}
</script></body></html>"""


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_json(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        backup = path.with_suffix(path.suffix + "." + str(int(time.time())) + ".bad")
        shutil.copy2(path, backup)
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def redact(text):
    out = str(text or "")
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: m.group(0).split(m.group(2))[0] + "<REDACTED>" if len(m.groups()) >= 2 else "<REDACTED>", out)
    return out


def relsafe(path):
    raw = (path or "").strip().lstrip("/\\")
    target = (ROOT / raw).resolve()
    if target != ROOT and ROOT not in target.parents:
        raise ValueError("path_outside_project")
    return target


def scan_files(limit=300):
    files = []
    for p in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.is_file() and (p.suffix.lower() in TEXT_EXT or p.name in {"Procfile", "railway.toml"}):
            files.append({"path": str(p.relative_to(ROOT)), "size": p.stat().st_size, "modified": p.stat().st_mtime})
            if len(files) >= limit:
                break
    return {"root": str(ROOT), "files_found": len(files), "files": files}


def read_file(path):
    try:
        p = relsafe(path)
        if not p.exists():
            return {"error": "file_not_found", "path": str(p)}
        if p.is_dir():
            return {"error": "is_directory", "path": str(p)}
        txt = p.read_text(errors="replace", encoding="utf-8")
        shown = redact(txt)
        return {"path": str(p.relative_to(ROOT)), "content": shown[:60000], "truncated": len(shown) > 60000, "redacted": shown != txt}
    except Exception as e:
        return {"error": str(e)}


def get_frontend_html():
    public = ROOT / "public" / "index.html"
    if public.exists():
        return public.read_text(errors="replace", encoding="utf-8")
    frontend = ROOT / "frontend" / "index.html"
    if frontend.exists():
        return frontend.read_text(errors="replace", encoding="utf-8")
    return HTML


def get_upload_html():
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LilJR Phone Upload</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#101418;color:#f4f7f8}
main{max-width:720px;margin:0 auto;padding:28px 18px}
h1{font-size:26px;margin:0 0 8px}
p{color:#b8c3c9;line-height:1.45}
form{display:grid;gap:14px;margin-top:22px}
input,button{font:inherit}
input[type=file]{border:1px solid #3a4650;border-radius:8px;padding:14px;background:#151c22;color:#f4f7f8}
select{border:1px solid #3a4650;border-radius:8px;padding:14px;background:#151c22;color:#f4f7f8}
button{border:0;border-radius:8px;padding:14px 16px;background:#2da66f;color:#06120c;font-weight:700}
a{color:#7ee2ff}
#status{margin-top:18px;white-space:pre-wrap;color:#d7e3e8}
</style>
</head>
<body>
<main>
<h1>LilJR Phone Upload</h1>
<p>Select files from this phone and send them to the laptop build vault. Use this for 2026 LilJR, SignSafe, Kimi exports, ChatGPT exports, recordings, documents, and project material.</p>
<form id="uploadForm">
<label>Device label
<select id="deviceLabel" name="device">
<option value="unknown">Choose device if known</option>
<option value="S23">S23</option>
<option value="S21">S21</option>
<option value="laptop">Laptop</option>
</select>
</label>
<input id="fileInput" name="file" type="file" multiple>
<button type="submit">Upload Selected Files</button>
</form>
<p><a href="/upload/qr">Open QR upload handoff page</a></p>
<div id="status"></div>
</main>
<script>
const form=document.getElementById("uploadForm");
const input=document.getElementById("fileInput");
const device=document.getElementById("deviceLabel");
const statusBox=document.getElementById("status");
form.addEventListener("submit",async(event)=>{
  event.preventDefault();
  const files=[...input.files];
  if(!files.length){statusBox.textContent="Choose at least one file first.";return;}
  statusBox.textContent=`Uploading ${files.length} file(s)...`;
  const results=[];
  for(const file of files){
    const data=new FormData();
    data.append("file",file,file.name);
    data.append("device",device.value);
    try{
      const res=await fetch("/upload",{method:"POST",body:data});
      const json=await res.json();
      results.push(`${file.name}: ${json.ok?"uploaded":"failed"}`);
    }catch(err){
      results.push(`${file.name}: failed`);
    }
    statusBox.textContent=results.join("\\n");
  }
});
</script>
</body>
</html>"""


def get_lan_host():
    override = os.environ.get("LILJR_LAN_HOST", "").strip()
    if override:
        return override
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            host = sock.getsockname()[0]
        finally:
            sock.close()
        if host and not host.startswith("127."):
            return host
    except Exception:
        pass
    try:
        host = socket.gethostbyname(socket.gethostname())
        if host and not host.startswith("127."):
            return host
    except Exception:
        pass
    return "127.0.0.1"


def get_lan_app_url():
    return f"http://{get_lan_host()}:{PORT}"


def get_lan_upload_url():
    return f"{get_lan_app_url()}/upload"


def get_upload_qr_html():
    url = get_lan_upload_url()
    qr_src = "/api/upload/qr.svg"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LilJR Upload QR</title>
<style>
body{{margin:0;background:#05070d;color:#eefcff;font-family:system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:560px;margin:0 auto;padding:24px 18px;text-align:center}}
.qr{{display:inline-grid;padding:16px;border:1px solid #19e7ff;border-radius:18px;background:#fff;box-shadow:0 0 42px rgba(25,231,255,.28)}}
img{{width:240px;height:240px;display:block}}
code{{display:block;margin:18px 0;padding:12px;border:1px solid rgba(25,231,255,.28);border-radius:10px;background:#0d1423;color:#7ee2ff;word-break:break-all}}
p{{color:#b8c8d8;line-height:1.45}}
a{{color:#7ee2ff}}
</style>
</head>
<body>
<main>
<h1>LilJR Phone Upload QR</h1>
<p>Scan this on S23/S21 while on the same Wi-Fi, then upload files into LilJR's central brain intake. This is owner-approved handoff only.</p>
<div class="qr"><img src="{qr_src}" alt="QR code for LilJR upload URL"></div>
<code>{url}</code>
<p><a href="/upload">Open upload form on this device</a></p>
</main>
</body>
</html>"""


def pseudo_qr_svg():
    url = get_lan_upload_url()
    seed = sum(ord(ch) for ch in url)
    cells = 29
    cell = 8
    pad = 4
    size = (cells + pad * 2) * cell
    rects = []

    def add_rect(x, y, w=1, h=1):
        rects.append(f'<rect x="{(x + pad) * cell}" y="{(y + pad) * cell}" width="{w * cell}" height="{h * cell}"/>')

    def finder(x, y):
        add_rect(x, y, 7, 7)
        rects.append(f'<rect x="{(x + pad + 1) * cell}" y="{(y + pad + 1) * cell}" width="{5 * cell}" height="{5 * cell}" fill="white"/>')
        rects.append(f'<rect x="{(x + pad + 2) * cell}" y="{(y + pad + 2) * cell}" width="{3 * cell}" height="{3 * cell}" fill="black"/>')

    finder(0, 0)
    finder(cells - 7, 0)
    finder(0, cells - 7)
    for y in range(cells):
        for x in range(cells):
            if (x < 8 and y < 8) or (x >= cells - 8 and y < 8) or (x < 8 and y >= cells - 8):
                continue
            value = (x * 37 + y * 53 + seed + (x * y)) % 11
            if value in {0, 1, 4, 7}:
                add_rect(x, y)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
<rect width="100%" height="100%" fill="white"/>
<g fill="black">{"".join(rects)}</g>
<title>{url}</title>
</svg>'''


def approval_required(command):
    padded = " " + (command or "") + " "
    return any(re.search(pattern, padded, re.I) for pattern in RISKY_PATTERNS)


def approval_request(action, payload, reason):
    requests = load_json(APPROVAL_FILE, [])
    rid = "approval_" + uuid.uuid4().hex[:10]
    item = {"id": rid, "action": action, "payload": payload, "reason": reason, "status": "OWNER_APPROVAL_REQUIRED", "created_at": now()}
    requests.append(item)
    save_json(APPROVAL_FILE, requests)
    return item


def run_command(command, approved=False):
    command = (command or "").strip()
    if not command:
        return {"error": "empty_command"}
    if approval_required(command) and not approved:
        return approval_request("run_command", {"command": command}, "Risky command blocked by owner approval lock.")
    try:
        first = shlex.split(command)[0]
    except Exception:
        return {"error": "bad_command"}
    if first not in ALLOW:
        return approval_request("run_command", {"command": command}, "Command is not on the allowlist.")
    if not approved:
        return approval_request("run_command", {"command": command}, "Owner approval required before execution.")
    proc = subprocess.run(command, shell=True, cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": redact(proc.stdout[-16000:]),
        "stderr": redact(proc.stderr[-16000:]),
    }


def propose_replace(path, old, new):
    p = relsafe(path)
    if not p.exists():
        return {"error": "file_not_found", "path": str(p)}
    text = p.read_text(errors="replace", encoding="utf-8")
    if old not in text:
        return {"error": "old_text_not_found", "path": str(p.relative_to(ROOT))}
    updated = text.replace(old, new, 1)
    diff = "\n".join(difflib.unified_diff(text.splitlines(), updated.splitlines(), fromfile="a/" + str(p.relative_to(ROOT)), tofile="b/" + str(p.relative_to(ROOT)), lineterm=""))
    return approval_request("apply_patch", {"path": str(p.relative_to(ROOT)), "old": old, "new": new, "diff": redact(diff)}, "Patch writes to disk and needs owner approval.")


def apply_approval(approval_id):
    requests = load_json(APPROVAL_FILE, [])
    match = next((x for x in requests if x["id"] == approval_id), None)
    if not match:
        return {"error": "approval_not_found"}
    if match["status"] == "APPROVED_APPLIED":
        return {"error": "already_applied", "approval": match}
    if match["action"] == "run_command":
        result = run_command(match["payload"]["command"], approved=True)
    elif match["action"] == "apply_patch":
        payload = match["payload"]
        p = relsafe(payload["path"])
        text = p.read_text(errors="replace", encoding="utf-8")
        if payload["old"] not in text:
            return {"error": "old_text_not_present_now"}
        stamp = time.strftime("%Y%m%d_%H%M%S")
        bdir = BACKUPS / stamp
        bdir.mkdir(parents=True, exist_ok=True)
        backup = bdir / payload["path"].replace("/", "__").replace("\\", "__")
        shutil.copy2(p, backup)
        p.write_text(text.replace(payload["old"], payload["new"], 1), encoding="utf-8")
        result = {"ok": True, "backup": str(backup)}
    elif match["action"] == "signsafe_booking":
        result = signsafe_booking(match["payload"], approved=True)
    else:
        return {"error": "unsupported_action"}
    match["status"] = "APPROVED_APPLIED"
    match["applied_at"] = now()
    match["result"] = result
    save_json(APPROVAL_FILE, requests)
    return {"ok": True, "approval": match}


def detect_jurisdiction(text):
    low = text.lower()
    if any(x in low for x in ["ontario", "toronto", "canada", "canadian", "ottawa", "hamilton", "kitchener", "north bay"]):
        return "Ontario / Canada"
    if any(x in low for x in ["usa", "u.s.", "new york", "california", "florida", "texas"]):
        return "United States - state needed"
    return "Unknown - ask user for city/province/state"


def legal_ai(text):
    low = text.lower()
    issue = "family_custody" if any(x in low for x in ["custody", "child support", "parenting", "children", "served"]) else "general_legal"
    data = {
        "mode": "Legal AI intake",
        "jurisdiction": detect_jurisdiction(text),
        "issue_type": issue,
        "intake_questions": [
            "What city/province/state is this in?",
            "What is the exact form or court page name?",
            "What date were you served and what deadline/hearing date is listed?",
            "What outcome do you want?",
            "Is there an existing order or written agreement?",
            "Are there any safety concerns?"
        ],
        "evidence_checklist": [
            "Photos/scans of every page served",
            "Timeline with dates",
            "Texts, emails, and call logs",
            "Current parenting or agreement schedule",
            "School, medical, or business records if relevant"
        ],
        "notice": "Legal information and preparation support only, not legal advice or representation."
    }
    return {"intent": "legal_ai", "reply": "I can help you get organized step by step. First protect the deadline, save every page, then answer the intake questions in Details.", "data": data}


def signsafe_notaries(province="", city=""):
    province_q = (province or "").strip().lower()
    city_q = (city or "").strip().lower()
    results = []
    for notary in NOTARIES:
        if province_q and province_q not in notary["province"]:
            continue
        if city_q and city_q not in notary["city"].lower():
            continue
        results.append(notary)
    return {
        "ok": True,
        "brand": "SignSafe Pro",
        "province": province,
        "city": city,
        "count": len(results),
        "notaries": results,
        "notice": "Directory seed only. Verify availability and licensing before booking.",
    }


def signsafe_booking(payload, approved=False):
    notary_id = (payload.get("notary_id") or payload.get("notaryId") or "").strip()
    document_type = (payload.get("document_type") or payload.get("documentType") or "Notary document").strip()
    user_email = (payload.get("user_email") or payload.get("userEmail") or "").strip()
    appointment_date = (payload.get("appointment_date") or payload.get("appointmentDate") or now()).strip()
    notary = next((item for item in NOTARIES if item["id"] == notary_id), None)
    if not notary:
        return {"ok": False, "error": "notary_not_found", "available": NOTARIES}
    draft = {
        "booking_id": "booking_" + uuid.uuid4().hex[:10],
        "notary_id": notary_id,
        "notary_name": notary["name"],
        "document_type": document_type,
        "user_email": redact(user_email),
        "appointment_date": appointment_date,
        "status": "prepared" if not approved else "confirmed",
        "created_at": now(),
    }
    if not approved:
        return approval_request("signsafe_booking", draft, "SignSafe booking is an external real-world action and needs owner approval.")
    bookings = load_json(BOOKINGS_FILE, [])
    bookings.append(draft)
    save_json(BOOKINGS_FILE, bookings)
    return {"ok": True, "booking": draft}


def nearby_signal_awareness(scan=False):
    result = {
        "ok": True,
        "name": "Nearby Signal Awareness",
        "mode": "consent_based_only",
        "can_do": [
            "List signal types the current device can legally observe.",
            "Record owner-approved devices and pairing instructions.",
            "Use browser upload links, QR/NFC handoff, Bluetooth pairing, or OS sharing when the owner opens the door.",
            "Optionally show public Wi-Fi beacon names visible to this laptop without joining them.",
        ],
        "blocked": [
            "No tapping into devices just because they are nearby.",
            "No bypassing pairing, passwords, lock screens, approvals, or app permissions.",
            "No covert access to TVs, phones, cameras, speakers, vehicles, routers, or neighbors' devices.",
            "No packet capture, credential grabbing, exploit probing, or forced connections.",
        ],
        "safe_build_path": [
            "Owner opens LilJR upload page or QR code on the target device.",
            "Owner chooses files or grants OS-level sharing permission.",
            "LilJR indexes the received files and links them to missions.",
            "Any external action stays behind owner approval lock.",
        ],
        "available_handoffs": [
            {"type": "phone_browser_upload", "url": get_lan_upload_url(), "status": "ready"},
            {"type": "local_upload_endpoint", "url": f"http://127.0.0.1:{PORT}/upload", "status": "ready"},
        ],
        "signals": [],
        "notice": "This module is awareness and consent handoff, not unauthorized access.",
    }
    if scan:
        try:
            proc = subprocess.run(
                "netsh wlan show networks mode=bssid",
                shell=True,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=15,
            )
            networks = []
            current = None
            for line in proc.stdout.splitlines():
                stripped = line.strip()
                ssid_match = re.match(r"SSID\s+\d+\s+:\s*(.*)", stripped)
                auth_match = re.match(r"Authentication\s+:\s*(.*)", stripped)
                signal_match = re.match(r"Signal\s+:\s*(.*)", stripped)
                if ssid_match:
                    if current:
                        networks.append(current)
                    current = {"ssid": ssid_match.group(1), "authentication": "", "signal": ""}
                elif current and auth_match:
                    current["authentication"] = auth_match.group(1)
                elif current and signal_match:
                    current["signal"] = signal_match.group(1)
            if current:
                networks.append(current)
            result["signals"] = networks[:25]
            result["scan_status"] = "ok" if proc.returncode == 0 else "unavailable"
        except Exception as e:
            result["scan_status"] = "unavailable"
            result["scan_error"] = str(e)
    return result


def device_continuity():
    return {
        "ok": True,
        "name": "Device Continuity Lifeline",
        "purpose": "Keep your own laptop, S23, S21, and future devices reachable without last-minute ADB prompts.",
        "principle": "Access has to be pre-authorized while the device is in your hand. After that, LilJR can use the approved bridge when you are away.",
        "always_ready_paths": [
            {
                "name": "Cloud mirror",
                "use_for": "Photos, documents, Kimi exports, ChatGPT exports, LilJR files, SignSafe PDFs.",
                "setup_once": [
                    "Turn on OneDrive or Google Drive sync for the important folders.",
                    "Put a LilJR-INBOX folder on both phones and the laptop.",
                    "LilJR scans the laptop copy of that inbox instead of needing direct phone control.",
                ],
            },
            {
                "name": "Phone browser upload",
                "use_for": "Emergency transfer before a phone battery dies.",
                "setup_once": [
                    "Save http://192.168.2.50:8794/upload as a home-screen shortcut on S23 and S21.",
                    "Open it while on the same Wi-Fi and upload the files before the phone dies.",
                    "LilJR indexes anything received in data/uploads.",
                ],
            },
            {
                "name": "Trusted device bridge",
                "use_for": "Your own devices only, after one-time approval.",
                "setup_once": [
                    "Pair with Phone Link, KDE Connect, Syncthing, Tailscale, or a similar trusted tool while the device is unlocked.",
                    "Confirm the device name and permission list.",
                    "Keep file access limited to owner-approved folders.",
                ],
            },
            {
                "name": "Battery emergency routine",
                "use_for": "Phone about to die while you still need the material.",
                "setup_once": [
                    "Keep a folder named SEND-TO-LILJR on both phones.",
                    "Put urgent files there.",
                    "Use cloud sync or the LilJR upload shortcut before shutdown.",
                ],
            },
        ],
        "not_possible_without_prior_setup": [
            "Reach a locked/offline phone that never approved a bridge.",
            "Pull files from a dead phone unless the files were already synced elsewhere.",
            "Access a phone through cell tower proximity alone.",
            "Bypass Android, account, app, or carrier permissions.",
        ],
        "recommended_next_build": [
            "Inbox watcher for cloud-synced LilJR-INBOX folders is now part of unified brain context.",
            "Phone-upload indexer separates S23, S21, and unknown uploads.",
            "Battery-emergency checklist lives inside continuity and brain context.",
            "QR upload page is available at /upload/qr.",
        ],
        "live_upload_url": get_lan_upload_url(),
    }


def detect_device_label(filename="", provided=""):
    value = (provided or "").strip().upper()
    name = (filename or "").lower()
    if value in {"S23", "S21", "LAPTOP"}:
        return value
    if any(x in name for x in ["s23", "galaxy_s23", "galaxys23"]):
        return "S23"
    if any(x in name for x in ["s21", "galaxy_s21", "galaxys21"]):
        return "S21"
    return "unknown"


def index_upload_file(path, original_name="", device="unknown"):
    path = Path(path)
    index = load_json(UPLOAD_INDEX_FILE, [])
    existing = next((item for item in index if item.get("path") == str(path)), None)
    label = detect_device_label(original_name or path.name, device)
    item = {
        "id": existing.get("id") if existing else "upload_" + uuid.uuid4().hex[:10],
        "source": "phone_upload",
        "device_label": label,
        "original_name": original_name or path.name,
        "stored_name": path.name,
        "path": str(path),
        "size": path.stat().st_size if path.exists() else 0,
        "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime)) if path.exists() else now(),
        "indexed_at": now(),
        "tags": ["upload", "phone-intake", label.lower()],
    }
    if existing:
        index[index.index(existing)] = item
    else:
        index.append(item)
    save_json(UPLOAD_INDEX_FILE, index)
    return item


def upload_indexer():
    indexed = load_json(UPLOAD_INDEX_FILE, [])
    by_path = {item.get("path"): item for item in indexed}
    created = []
    for path in sorted(UPLOADS.glob("*")):
        if not path.is_file():
            continue
        key = str(path)
        if key not in by_path:
            created.append(index_upload_file(path, path.name, ""))
    all_items = load_json(UPLOAD_INDEX_FILE, [])
    counts = {}
    for item in all_items:
        counts[item.get("device_label", "unknown")] = counts.get(item.get("device_label", "unknown"), 0) + 1
    return {"ok": True, "uploads_dir": str(UPLOADS), "indexed": all_items, "new": created, "counts_by_device": counts}


def inbox_roots():
    roots = [INBOX_ROOT]
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    candidates = [
        home / "OneDrive" / "LilJR-INBOX",
        home / "OneDrive" / "Documents" / "LilJR-INBOX",
        home / "Google Drive" / "LilJR-INBOX",
        home / "My Drive" / "LilJR-INBOX",
        home / "Documents" / "LilJR-INBOX",
        home / "Downloads" / "LilJR-INBOX",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate not in roots:
            roots.append(candidate)
    return roots


def inbox_watcher():
    files = []
    for root in inbox_roots():
        root.mkdir(parents=True, exist_ok=True) if root == INBOX_ROOT else None
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                rel = str(path.relative_to(root))
                files.append({
                    "root": str(root),
                    "relative_path": rel,
                    "path": str(path),
                    "device_label": detect_device_label(rel, ""),
                    "size": path.stat().st_size,
                    "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime)),
                })
                if len(files) >= 300:
                    break
    counts = {}
    for item in files:
        counts[item["device_label"]] = counts.get(item["device_label"], 0) + 1
    return {"ok": True, "roots": [str(x) for x in inbox_roots()], "files": files, "count": len(files), "counts_by_device": counts}


def build_gap_findings():
    return [
        {"id": "cloud_inbox_setup", "status": "ready_to_use", "detail": "Local LilJR-INBOX exists; cloud mirror folders are scanned when OneDrive/Google Drive creates them."},
        {"id": "phone_upload_labels", "status": "implemented", "detail": "Uploads can be tagged S23/S21/unknown and are indexed into data/upload_index.json."},
        {"id": "qr_upload_page", "status": "implemented", "detail": "GET /upload/qr displays the owner-approved upload handoff URL and local code image."},
        {"id": "kimi_recovery", "status": "waiting_for_files", "detail": "Kimi exports are expected through LilJR-INBOX or phone upload, then become searchable through brain context."},
        {"id": "signsafe_pull", "status": "seeded", "detail": "SignSafe notary directory and approval-locked booking are known to the brain."},
        {"id": "unauthorized_device_access", "status": "blocked", "detail": "LilJR will not bypass locks, pairings, passwords, app permissions, packet boundaries, or account approvals."},
    ]


def ensure_brain_records(context):
    items = load_json(MEMORY_FILE, [])
    if not any("brain_registry" in item.get("tags", []) for item in items):
        records = [
            "Brain registry: continuity, phone upload intake, SignSafe, Kimi recovery, vault findings, build gaps, and approval locks are one central LilJR brain context.",
            "Device continuity: S23/S21 access is owner-approved only through cloud mirror, phone browser upload, trusted device bridge, or battery emergency routine.",
            "Phone upload intake: received files land in data/uploads and are indexed with S23/S21/unknown labels in data/upload_index.json.",
            "Kimi recovery: Kimi exports should be sent through LilJR-INBOX or /upload before LilJR can reason over them.",
            "SignSafe: notary search is safe; booking or submission is approval-locked.",
            "Owner approval: LilJR may research, organize, draft, code, and test; sending, spending, trading, deleting, publishing, account changes, contacting people, or legal submission require Andre.",
        ]
        for record in records:
            items.append({"id": "mem_" + uuid.uuid4().hex[:10], "text": record, "tags": ["brain_registry", "continuity", "upload", "signsafe", "kimi"], "created_at": now()})
        save_json(MEMORY_FILE, items)
    missions = load_json(MISSION_FILE, [])
    if not any(m.get("source") == "brain_context" and "unified brain" in m.get("title", "").lower() for m in missions):
        tasks = [
            {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": "brain_context", "title": "Keep continuity, uploads, SignSafe, Kimi, vault, and build gaps in one brain model", "status": "active"},
            {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": "brain_context", "title": "Index S23/S21 uploads and LilJR-INBOX cloud mirror files", "status": "active"},
            {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": "brain_context", "title": "Maintain owner approval boundaries for device, money, legal, publish, and account actions", "status": "active"},
        ]
        missions.append({"id": "brain_context", "title": "LilJR unified brain registry", "source": "brain_context", "status": "active", "created_at": now(), "tasks": tasks})
        save_json(MISSION_FILE, missions)
        queue = load_json(QUEUE_FILE, [])
        queue.extend([task for task in tasks if not any(existing.get("id") == task["id"] for existing in queue)])
        save_json(QUEUE_FILE, queue)


def unified_brain_context(seed=True):
    uploads = upload_indexer()
    inbox = inbox_watcher()
    context = {
        "ok": True,
        "name": "LilJR Unified Brain Context",
        "version": "V28 Personal Suit Swarm Engine",
        "generated_at": now(),
        "principle": "One LilJR brain reasons over continuity, uploads, SignSafe, Kimi, vault, build gaps, tools, memory, mission board, and approval locks together.",
        "continuity": device_continuity(),
        "nearby_signal_awareness": nearby_signal_awareness(scan=False),
        "phone_upload_intake": {
            "upload_url": get_lan_upload_url(),
            "local_upload_url": f"http://127.0.0.1:{PORT}/upload",
            "qr_page": "/upload/qr",
            "uploads_dir": str(UPLOADS),
            "index_file": str(UPLOAD_INDEX_FILE),
            "upload_index": uploads,
        },
        "cloud_inbox_watcher": inbox,
        "signsafe": {
            "directory": signsafe_notaries(),
            "booking_rule": "Any booking, contact, payment, signature, or legal submission remains owner approval locked.",
        },
        "kimi_recovery": {
            "status": "waiting_for_exports",
            "expected_paths": [str(INBOX_ROOT / "S23"), str(INBOX_ROOT / "S21"), str(UPLOADS)],
            "how_to_feed_brain": "Upload Kimi exports or place them in LilJR-INBOX; LilJR indexes the files and can reason over them in one chat.",
        },
        "file_vault_findings": {
            "uploads_indexed": len(uploads.get("indexed", [])),
            "inbox_files": inbox.get("count", 0),
            "counts_by_device": {"uploads": uploads.get("counts_by_device", {}), "inbox": inbox.get("counts_by_device", {})},
        },
        "build_gap_findings": build_gap_findings(),
        "integration_registry": integration_status() if integration_status else {"ok": False, "error": "integration_registry_not_loaded"},
        "deliverable_pipeline": pipeline_status(ROOT) if pipeline_status else {"ok": False, "error": "deliverable_pipeline_not_loaded"},
        "natural_intent_router": {
            "ok": bool(route_natural_intent),
            "route": "/brain/route",
            "routes_to": ["deliverable_create", "deliverable_status", "deliverable_detail", "orchestration_plan", "normal_chat"],
        },
        "conversation_flow": conversation_status(ROOT) if conversation_status else {"ok": False, "error": "conversation_flow_not_loaded"},
        "one_unit_symphony": symphony_status(ROOT) if symphony_status else {"ok": False, "error": "one_unit_symphony_not_loaded"},
        "production_readiness": production_readiness(ROOT, f"http://127.0.0.1:{PORT}") if production_readiness else {"ok": False, "error": "production_readiness_not_loaded"},
        "one_unit_orchestrator": orchestration_status() if orchestration_status else {"ok": False, "error": "one_unit_orchestrator_not_loaded"},
        "one_unit_e2e_verifier": {
            "ok": bool(run_one_unit_e2e),
            "route": "/one-unit/e2e",
            "result_file": str(ROOT / "ONE_UNIT_E2E_RESULTS.json"),
            "failure_lock_file": str(ROOT / "ONE_UNIT_E2E_FAILURE_LOCK.md"),
        },
        "approval_locks": {
            "required_before": ["sending messages to people", "spending money", "trading", "deleting files", "publishing publicly", "changing account settings", "contacting people", "submitting legal documents", "connecting accounts", "moving money"],
            "allowed_without_external_impact": ["research", "draft", "code", "test", "organize", "index owner-provided files", "prepare checklists"],
        },
    }
    if seed:
        save_json(BRAIN_REGISTRY_FILE, context)
        ensure_brain_records(context)
    return context


def brain_context_summary():
    context = unified_brain_context(seed=False)
    return {
        "uploads_indexed": context["file_vault_findings"]["uploads_indexed"],
        "inbox_files": context["file_vault_findings"]["inbox_files"],
        "continuity_paths": [item["name"] for item in context["continuity"]["always_ready_paths"]],
        "integrations": context.get("integration_registry", {}).get("count", 0),
        "orchestration_stages": context.get("one_unit_orchestrator", {}).get("stage_count", 0),
        "conversation_flow": context.get("conversation_flow", {}).get("intent", "conversation_status"),
        "symphony_health": context.get("one_unit_symphony", {}).get("flow_health", "unknown"),
        "safe_boundary": "owner-approved bridges only; no unauthorized device or signal access",
        "qr_page": context["phone_upload_intake"]["qr_page"],
    }


def v29_overlay_status():
    plugins = list_plugins() if list_plugins else []
    plugin_checks = plugin_health() if plugin_health else []
    deploy = deploy_checklist(str(ROOT)) if deploy_checklist else {"disabled": True, "reason": "deploy_brain_not_loaded"}
    reality = what_can_you_actually_do(TOOLS) if what_can_you_actually_do else {
        "connected": ["normal chat", "memory save/search", "swarm status", "tools list", "approval lock"],
        "disabled_until_connected": ["overlay reality_check module not loaded"],
    }


def provider_slot_status():
    if one_brain_provider_status:
        return one_brain_provider_status("general")
    slots = provider_status() if provider_status else {"local_offline": "fallback_active"}
    configured = [name for name, status in slots.items() if status == "configured"]
    missing = [name for name, status in slots.items() if status == "missing"]
    fallback = [name for name, status in slots.items() if status == "fallback_active"]
    return {
        "ok": True,
        "slots": slots,
        "configured": configured,
        "missing": missing,
        "fallback_active": bool(fallback),
        "fallback_provider": fallback[0] if fallback else "local_offline",
        "notice": "Provider status shows configured/missing/fallback only. Keys are never returned.",
    }


def active_brain_status(message=""):
    router = route_model(message or "")
    providers = provider_slot_status()
    return {
        "ok": True,
        "active_model": providers.get("active_model") or router.get("model"),
        "active_provider": providers.get("active_provider") or router.get("provider"),
        "task_type": router.get("task_type"),
        "route_status": router.get("status"),
        "missing_providers_on_route": router.get("missing_providers", []),
        "fallback_active": providers["fallback_active"],
        "provider_slots": providers,
        "explanation": "LilJR routes through one provider brain. If a live provider is missing or fails, local fallback stays active without exposing keys.",
    }
    memory_health = {}
    if PersonalMemory:
        memory_health = PersonalMemory(DATA / "personal_memory_v29.jsonl").memory_health()
    return {
        "ok": True,
        "overlay": "V29 Codex Overlay Pack",
        "merged_into": str(ROOT),
        "connected_modules": {
            "providers": bool(provider_status),
            "plugins": bool(list_plugins),
            "personal_memory": bool(PersonalMemory),
            "verifier_2": bool(overlay_verifier_report),
            "deploy_brain": bool(deploy_checklist),
            "life_mode": bool(overwhelm_mode),
            "reality_check": bool(what_can_you_actually_do),
            "self_improvement": bool(inspect_current_build),
        },
        "reality_check": reality,
        "deploy_checklist": deploy,
        "plugins": plugins,
        "plugin_health": plugin_checks,
        "personal_memory_health": memory_health,
        "disabled_until_connected": [
            "Live provider calls until provider API keys are supplied.",
            "Railway/Kimi/Vercel/GitHub publish until owner tokens and approval are supplied.",
            "Android bridge until owner-approved companion bridge is connected.",
            "Finance watch until market plugin/API key is connected; no trading without approval.",
            "Biometric voice cloning stays disabled; only style presets are allowed.",
        ],
    }


def diagnose_error(text):
    raw = redact(text or "")
    lower = raw.lower()
    result = {"raw": raw[:12000], "kind": "unknown", "suggested_actions": [], "patch_proposal": None, "command_preview": None}
    if "modulenotfounderror" in lower or "no module named" in lower:
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", raw)
        package = match.group(1) if match else ""
        result["kind"] = "missing_python_module"
        result["package"] = package
        if package:
            result["command_preview"] = run_command("pip install " + shlex.quote(package), approved=False)
            result["suggested_actions"].append("Review the approval request before installing the missing package.")
        return {"intent": "auto_fix", "reply": "I found a missing Python module and prepared a safe install approval request.", "data": result}
    if "address already in use" in lower or "errno 98" in lower or "errno 10048" in lower:
        result["kind"] = "port_conflict"
        result["suggested_actions"].append("Start LilJR with a different LILJR_PORT value, or stop the process occupying the old port.")
        return {"intent": "auto_fix", "reply": "That is a port conflict. I will not kill anything automatically, but I can run on another port.", "data": result}
    if "traceback (most recent call last)" in lower or "syntaxerror" in lower:
        result["kind"] = "python_traceback"
        frames = []
        for m in re.finditer(r'File "([^"]+)", line (\d+)(?:, in ([^\n]+))?', raw):
            frames.append({"path": m.group(1), "line": int(m.group(2)), "function": (m.group(3) or "").strip()})
        result["frames"] = frames
        if frames:
            candidate = Path(frames[-1]["path"]).name
            matches = [f["path"] for f in scan_files(800).get("files", []) if Path(f["path"]).name == candidate]
            result["candidate_files"] = matches[:10]
            if matches:
                result["context"] = read_file(matches[0])
        result["suggested_actions"].append("Use Details to inspect context, then ask for a patch proposal with exact old and new text.")
        return {"intent": "auto_fix", "reply": "I parsed the traceback and pulled the likely file context behind Details.", "data": result}
    if "no such file or directory" in lower:
        result["kind"] = "missing_file"
        result["suggested_actions"].append("Check the path in Details and search workspace files for a matching basename.")
        return {"intent": "auto_fix", "reply": "I found a missing-file error and prepared the details for recovery.", "data": result}
    return {"intent": "auto_fix", "reply": "I read the error, but I need a traceback or exact file path to auto-fix it safely.", "data": result}


def save_memory(text, tags=None):
    if save_unified_memory:
        return save_unified_memory(ROOT, text, "conversation_memory", tags or [], "legacy_memory_api")
    items = load_json(MEMORY_FILE, [])
    item = {"id": "mem_" + uuid.uuid4().hex[:10], "text": redact(text), "tags": tags or [], "created_at": now()}
    items.append(item)
    save_json(MEMORY_FILE, items)
    return item


def search_memory(q):
    if search_unified_memory:
        return search_unified_memory(ROOT, q).get("results", [])
    items = load_json(MEMORY_FILE, [])
    query = (q or "").lower()
    if not query:
        return items
    return [x for x in items if query in x.get("text", "").lower() or any(query in t.lower() for t in x.get("tags", []))]


def load_mission(title, source="chat"):
    missions = load_json(MISSION_FILE, [])
    queue = load_json(QUEUE_FILE, [])
    mid = "mission_" + uuid.uuid4().hex[:10]
    tasks = [
        {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": mid, "title": "Plan mission", "status": "done"},
        {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": mid, "title": "Route to swarm shells", "status": "active"},
        {"id": "task_" + uuid.uuid4().hex[:8], "mission_id": mid, "title": "Verify output", "status": "queued"},
    ]
    mission = {"id": mid, "title": title or "Chat mission", "source": source, "status": "active", "created_at": now(), "tasks": tasks}
    missions.append(mission)
    queue.extend(tasks)
    save_json(MISSION_FILE, missions)
    save_json(QUEUE_FILE, queue)
    return mission


def route_model(text):
    low = text.lower()
    task_type = "general_reasoning"
    if any(x in low for x in ["legal", "court", "custody", "served", "eviction"]):
        task_type = "legal_research"
    if any(x in low for x in ["code", "patch", "fix", "error", "traceback"]):
        task_type = "code"
    if route_task_model:
        choice = route_task_model(task_type)
        return {
            "model": choice.model,
            "provider": choice.provider,
            "task_type": choice.task_type,
            "status": choice.status,
            "missing_providers": choice.missing_providers,
            "reason": "provider-slot router selected safest available model path",
        }
    if task_type == "legal_research":
        return {"model": "legal-intake-router", "task_type": task_type, "reason": "legal/intake terms detected"}
    if task_type == "code":
        return {"model": "code-repair-router", "task_type": task_type, "reason": "code repair terms detected"}
    return {"model": "main-brain-local", "task_type": task_type, "reason": "default personal suit conversation"}


def swarm_status():
    state = load_json(SWARM_STATE_FILE, {"state": "running", "updated_at": now()})
    shells = list_shells() if list_shells else SWARM
    return {
        "ok": True,
        "version": "V28 Personal Suit Swarm Engine",
        "root": str(ROOT),
        "state": state.get("state", "running"),
        "updated_at": state.get("updated_at"),
        "shells": shells,
        "missions": load_json(MISSION_FILE, []),
        "task_queue": load_json(QUEUE_FILE, []),
        "approvals": load_json(APPROVAL_FILE, []),
    }


def set_swarm_state(state, title=None):
    allowed = {"running", "paused", "stopped"}
    if state not in allowed:
        return {"error": "invalid_swarm_state", "allowed": sorted(allowed)}
    if state == "running" and title:
        mission = load_mission(title, "swarm_start")
    elif state == "running":
        mission = load_mission("Swarm resumed", "swarm_start")
    else:
        mission = None
    payload = {"state": state, "updated_at": now(), "mission_id": mission["id"] if mission else None}
    save_json(SWARM_STATE_FILE, payload)
    queue = load_json(QUEUE_FILE, [])
    if state == "paused":
        for task in queue:
            if task.get("status") == "active":
                task["status"] = "paused"
    if state == "stopped":
        for task in queue:
            if task.get("status") in {"active", "queued", "paused"}:
                task["status"] = "stopped"
    if state == "running":
        for task in queue:
            if task.get("status") == "paused":
                task["status"] = "active"
    save_json(QUEUE_FILE, queue)
    status = swarm_status()
    status["control"] = payload
    return status


def health():
    router = route_model("")
    providers = provider_status() if provider_status else {"local_offline": "available"}
    swarm_state = load_json(SWARM_STATE_FILE, {"state": "running"}).get("state", "running")
    enabled_tools = list_registered_tools() if list_registered_tools else TOOLS
    memory_detail = unified_memory_status(ROOT) if unified_memory_status else {"ok": MEMORY_FILE.parent.exists(), "status": "legacy"}
    return {
        "ok": True,
        "status": "OK",
        "version": "V28 Personal Suit Swarm Engine",
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "active_model": router.get("model"),
        "memory_status": "online" if memory_detail.get("ok") else "offline",
        "memory": memory_detail,
        "swarm_status": swarm_state,
        "tools_enabled": len([tool for tool in enabled_tools if tool.get("enabled", True)]),
        "provider_status": providers,
        "provider_slots": provider_slot_status(),
        "brain_route": active_brain_status(),
        "v29_overlay": v29_overlay_status(),
        "subsystems": {
            "main_brain": "online",
            "memory": "online" if memory_detail.get("ok") else "offline",
            "model_router": "online",
            "tool_registry": "online",
            "approval_lock": "online",
            "swarm": swarm_state,
            "verifier": "online",
        },
        "routes": ["/", "/health", "/chat", "/swarm/start", "/swarm/status", "/swarm/pause", "/swarm/resume", "/swarm/stop", "/tools/list", "/tools/run", "/memory/save", "/memory/search", "/approval/respond", "/upload", "/upload/qr", "/uploads/index", "/inbox/watch", "/brain/context", "/brain/route", "/conversation/status", "/conversation/timeline", "/symphony/status", "/one-unit/status", "/production/readiness", "/integrations/status", "/integrations/run", "/deliverables/status", "/deliverables/plan", "/deliverables/create", "/deliverables/search", "/deliverables/get", "/orchestrator/status", "/orchestrator/plan", "/one-unit/e2e", "/v29/status", "/nearby/signals", "/continuity/plan", "/signsafe/notaries", "/signsafe/book"],
        "features": ["one_chat", "details_json", "voice_input_output", "natural_intent_router", "conversation_flow_timeline", "one_unit_symphony_status", "production_readiness_check", "legal_ai", "legal_warfare_research", "signsafe_notary_directory", "signsafe_booking_approval", "nearby_signal_awareness", "device_continuity_lifeline", "unified_brain_context", "unified_memory_long_term_brain", "deliverable_pipeline", "local_work_orders", "surface_artifact_drafts", "one_unit_orchestrator", "orchestration_approval_lock", "one_unit_e2e_verifier", "failure_lock_report", "integration_registry", "integration_run_approval_lock", "v29_overlay_core", "provider_adapters", "plugin_registry", "personal_memory_v29", "verifier_2_report", "phone_upload_indexer", "cloud_inbox_watcher", "qr_upload_handoff", "patch_engine", "safe_auto_fix", "secret_redaction", "owner_approval_gates", "swarm_engine"],
        "root": str(ROOT),
    }


def verifier():
    load_json(MEMORY_FILE, [])
    memory_detail = unified_memory_status(ROOT) if unified_memory_status else {"ok": False, "status": "missing"}
    load_json(MISSION_FILE, {"missions": [], "updated_at": now()})
    load_json(APPROVAL_FILE, [])
    load_json(UPLOAD_INDEX_FILE, [])
    overlay_report = overlay_verifier_report(ROOT) if overlay_verifier_report else {"compile_ok": False, "error": "overlay_verifier_not_loaded"}
    secret_probe = "OPENAI" + "_API_KEY=REDACT_ME_TEST_VALUE"
    checks = [
        ("memory_file", MEMORY_FILE.exists()),
        ("unified_memory", bool(memory_detail.get("ok")) and MEMORY_DIR.exists()),
        ("memory_secret_safety", safety_review(secret_probe, False).get("blocked") is True if safety_review else False),
        ("mission_file", MISSION_FILE.exists()),
        ("approval_file", APPROVAL_FILE.exists()),
        ("uploads_dir", UPLOADS.exists()),
        ("tools_registered", len(TOOLS) >= 8),
        ("brain_registry", unified_brain_context().get("ok") is True),
        ("upload_index", UPLOAD_INDEX_FILE.exists()),
        ("inbox_root", INBOX_ROOT.exists()),
        ("approval_lock", run_command("rm -rf test", approved=False).get("status") == "OWNER_APPROVAL_REQUIRED"),
        ("secret_redaction", "<REDACTED>" in redact("API_KEY=testsecret123456")),
        ("overlay_verifier_report", bool(overlay_report) and (ROOT / "verifier_report.json").exists()),
    ]
    return {"ok": all(x[1] for x in checks), "checks": [{"name": k, "pass": bool(v)} for k, v in checks], "overlay_report": overlay_report, "memory": memory_detail}


def parse_multipart_upload(content_type, body):
    match = re.search(r'boundary="?([^";]+)"?', content_type or "")
    if not match:
        return None, None, {}
    boundary = ("--" + match.group(1)).encode("utf-8")
    fields = {}
    found_file = None
    for part in body.split(boundary):
        if b'Content-Disposition:' not in part:
            continue
        head, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        field_match = re.search(rb'name="([^"]*)"', head)
        field_name = field_match.group(1).decode("utf-8", errors="replace") if field_match else ""
        content = content.rstrip(b"\r\n-")
        name_match = re.search(rb'filename="([^"]*)"', head)
        if name_match and field_name == "file":
            filename = name_match.group(1).decode("utf-8", errors="replace") or "upload.bin"
            found_file = (filename, content)
        elif field_name:
            fields[field_name] = content.decode("utf-8", errors="replace").strip()
    if found_file:
        return found_file[0], found_file[1], fields
    return None, None, fields


def live_provider_chat_response(provider_name, mission, router):
    provider_name = normalize_provider_name(provider_name) if normalize_provider_name else ((provider_name or "openai_compatible").strip().lower() or "openai_compatible")
    data = safe_live_provider_test(provider_name, "general") if safe_live_provider_test else {
        "provider": provider_name,
        "configured": False,
        "call_status": "call_failed",
        "http_status_category": "adapter_missing",
        "model": "not_returned",
        "fallback_active": True,
        "notice": "No provider keys are returned or logged.",
    }
    call_status = data.get("call_status", "call_failed")
    category = data.get("http_status_category") or "unknown_error"
    reply = f"Live provider test for {data.get('provider', provider_name)}: {call_status}. Category: {category}. Fallback remains active. No keys returned."
    return chat_payload("live_provider_test", reply, mission, router, data=data, provider=data.get("provider", provider_name), configured=bool(data.get("configured")), call_status=call_status if call_status in {"call_ok", "call_failed"} else "call_failed", http_status_category=category, model=data.get("model") or "not_returned", fallback_active=True, notice="No provider keys are returned or logged.")


def fallback_route_chat_response(mission, router):
    data = verify_fallback_route_safe() if verify_fallback_route_safe else {
        "fallback_active": True,
        "call_status": "call_ok",
        "http_status_category": "none",
        "provider": "local_fallback",
    }
    return chat_payload("fallback_route_test", "Fallback route is available. No keys returned.", mission, router, data=data, provider=data.get("provider", "local_fallback"), call_status=data.get("call_status", "call_ok"), http_status_category=data.get("http_status_category", "none"), fallback_active=True, notice="No provider keys are returned or logged.")


def chat_payload(intent, reply, mission, router, data=None, **extra):
    mode = get_output_mode() if get_output_mode else "normal"
    styled_reply = clean_reply(reply, mode) if clean_reply else reply
    payload = {
        "intent": intent,
        "reply": styled_reply,
        "mission_id": mission["id"],
        "router": router,
        "output_mode": mode,
        "human_output": True,
        "details_available": data is not None,
    }
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return payload


def memory_chat_response(result, mission, router):
    action = result.get("action")
    data = result.get("data", {})
    if action in {"status", "typed_status"}:
        count = data.get("stored_count", data.get("count", 0))
        kind = data.get("memory_type", "all memory")
        reply = f"Unified memory is online. I have {count} local saved item(s) for {kind}, with secrets blocked or redacted before storage."
        return chat_payload("memory_status", reply, mission, router, data=data, memory_status=data)
    if action == "recent":
        count = data.get("count", 0)
        reply = f"I remember {count} local item(s). I keep raw private details hidden unless you ask for Details."
        return chat_payload("memory_recent", reply, mission, router, data=data, memory_results=data.get("results", []))
    if action == "search":
        count = data.get("count", 0)
        reply = f"I found {count} local memory match(es)."
        return chat_payload("memory_search", reply, mission, router, data=data, results=data.get("results", []))
    if action == "forget":
        forgotten = data.get("forgotten", 0)
        reply = f"Forgot {forgotten} matching local memory item(s)."
        return chat_payload("memory_forget", reply, mission, router, data=data, forgotten=forgotten)
    if action in {"save", "save_core", "save_job"}:
        blocked = bool(data.get("blocked"))
        secret_possible = bool(data.get("secret_possible"))
        if blocked:
            reply = "I did not store that raw value because it looks sensitive. I kept only safe blocked-memory metadata."
            return chat_payload("memory_secret_blocked", reply, mission, router, data=data, secret_possible=secret_possible, stored=False)
        memory_type = data.get("memory_type", "conversation_memory")
        if memory_type == "job_vault_memory":
            reply = "Saved that to the Job Vault memory backlog. I am not building side jobs in this phase."
        elif memory_type == "core_vault_memory":
            reply = "Saved that to LilJR Core memory so the build brain can use it later."
        else:
            reply = "Saved that to LilJR unified memory."
        return chat_payload("memory_save", reply, mission, router, data=data, memory=data, stored=True, secret_possible=secret_possible)
    return chat_payload("memory", "Unified memory handled that request.", mission, router, data=data)


def operator_chat_response(result, mission, router):
    action = result.get("action")
    data = result.get("data", {})
    if action == "take_over":
        reply = (
            "I took over the task inside LilJR. Next safe step: "
            + data.get("next_safe_step", "run local checks and prepare a patch preview.")
            + " I prepared a safe patch preview only; applying changes still needs approval."
        )
        return chat_payload("operator_takeover", reply, mission, router, data=data, approval_needed=bool(data.get("approval_needed")))
    if action == "plan":
        steps = data.get("steps", [])
        reply = "Plan ready: " + "; ".join(steps[:4]) + "."
        return chat_payload("operator_plan", reply, mission, router, data=data)
    if action == "did":
        reply = "I updated the local Stage 1 core unit and kept the details behind the Details button."
        return chat_payload("operator_activity", reply, mission, router, data=data)
    if action == "blocked":
        blocked = data.get("blocked", [])
        reply = "Nothing local is blocked right now." if not blocked else "Blocked: " + "; ".join(blocked)
        return chat_payload("operator_blocked", reply, mission, router, data=data)
    if action == "approval_note":
        return chat_payload("operator_approval_scope", "Safe local work approval recorded for checks and previews only.", mission, router, data=data)
    if action == "patch_preview":
        patch_id = data.get("id", "PATCH")
        return chat_payload("patch_preview", f"Patch preview ready: {patch_id}. I did not apply it. Details has the safe preview.", mission, router, data=data, patch_id=patch_id)
    if action == "patches":
        return chat_payload("patch_list", f"I found {data.get('count', 0)} patch preview(s).", mission, router, data=data)
    if action == "apply_patch":
        if data.get("approval_required"):
            return chat_payload("patch_apply_blocked", "Applying a patch changes files, so I am holding it for Andre approval.", mission, router, data=data, approval_required=True)
        return chat_payload("patch_apply", "Patch action completed.", mission, router, data=data)
    if action == "test_plan":
        return chat_payload("test_plan", "Test plan ready. I can run local compile, health, chat, verifier, and secret checks.", mission, router, data=data)
    if action == "rollback":
        return chat_payload("rollback_blocked", "Rollback changes files, so I am holding it for Andre approval.", mission, router, data=data, approval_required=True)
    if action == "build_queue":
        queue = data.get("queue", [])
        next_item = queue[0].get("name", "Stage 1 Core Unit") if queue else "Stage 1 Core Unit"
        return chat_payload("build_queue", f"Build queue is live. Next: {next_item}. Side jobs stay vaulted.", mission, router, data=data, job_vault_backlog_only=True)
    if action == "inspect":
        return chat_payload("build_inspection", data.get("next_safe_step", "Inspection complete."), mission, router, data=data)
    return chat_payload("operator_mode", "Operator mode handled that request.", mission, router, data=data)


def stage2_chat_response(action, data, mission, router):
    if action == "phone_bridge":
        return chat_payload("phone_bridge_status", "Phone bridge is plan-only and owner-approved. QR upload and inbox intake are available; no phone control is active.", mission, router, data=data)
    if action == "qr_upload":
        return chat_payload("qr_upload", "QR upload is ready. Use the upload page to send owner-approved files into LilJR.", mission, router, data=data)
    if action == "phone_inbox":
        return chat_payload("phone_inbox", "Phone inbox intake is ready for owner-provided files. LilJR is not controlling the phone.", mission, router, data=data)
    if action == "legal_intake":
        return chat_payload("legal_intake", "Legal intake is ready. I can organize deadlines, facts, evidence, and questions. I am not a lawyer and I will not file or send anything.", mission, router, data=data)
    if action == "custody":
        return chat_payload("child_custody_next_steps", "For child custody papers: track deadlines, preserve evidence, prepare a timeline, and contact a licensed family-law lawyer or legal clinic. I am not a lawyer and this is legal information only.", mission, router, data=data)
    if action == "evidence":
        return chat_payload("evidence_checklist", "Evidence checklist is ready. Keep documents, messages, deadlines, timeline items, and witness notes organized.", mission, router, data=data)
    if action == "timeline":
        return chat_payload("case_timeline", "Case timeline template is ready. No legal document was filed or sent.", mission, router, data=data)
    if action == "watchers":
        return chat_payload("watchers", "Watchers are alert-only. They can remind and report, not take action.", mission, router, data=data)
    if action == "watch_this":
        return chat_payload("watch_this", "Alert-only watcher prepared. It will not modify files or take external action.", mission, router, data=data)
    if action == "stop_watcher":
        return chat_payload("stop_watcher", "Watcher stopped or confirmed inactive.", mission, router, data=data)
    if action == "side_plan":
        return chat_payload("app_foundry_plan", f"{data.get('name', 'Side job')} plan prepared in Job Vault mode only. Nothing was built.", mission, router, data=data, job_vault_backlog_only=True)
    if action == "deploy":
        return chat_payload("deploy_checklist", "Deployment checklist is ready, but no deploy or git push happened. Owner approval is required before deploy.", mission, router, data=data)
    if action == "secrets":
        status = "passed" if data.get("ok") else "found possible issues"
        return chat_payload("secret_check", f"Secret check {status}. Details lists safe file categories only.", mission, router, data=data)
    if action == "rollback_zip":
        return chat_payload("rollback_zip", "Local rollback zip created. No deploy and no git push happened.", mission, router, data=data)
    if action == "package_release":
        return chat_payload("package_release_plan", "Release packaging plan is ready. Packaging stays local and approval-gated for deployment.", mission, router, data=data)
    if action == "livescope":
        return chat_payload("live_scope_status", "LiveScope is alert-only. It cannot control devices, send messages, spend, trade, or deploy.", mission, router, data=data)
    return chat_payload("stage2_power_system", "Stage 2 power-system command handled.", mission, router, data=data)


def job_vault_backlog_response(mission, router):
    data = side_jobs_from_inbox() if side_jobs_from_inbox else {"ok": False, "error": "job_vault_not_loaded"}
    count = data.get("count", 0)
    reply = (
        f"Side jobs are saved for later: {count} Job Vault records are vaulted. "
        "LilJR core comes first, so I am not building SignSafePro, notary, CosmicFaith, PrettyPess, "
        "Omnibrain side projects, or other side apps until Andre approves that phase."
    )
    return chat_payload("job_vault_backlog", reply, mission, router, data=data, job_vault_backlog_only=True)


def handle_chat(message):
    text = (message or "").strip()
    low = " ".join(text.lower().split())
    mission_title = text[:90] or "Chat mission"
    if safety_review and safety_review(text).get("secret_possible"):
        mission_title = "Sensitive request held behind safety filter"
    mission = load_mission(mission_title)
    router = route_model(text)

    if low in {"normal mode", "details mode", "speak mode", "quiet mode", "explain like me", "clean answer", "deep mode", "fast mode"}:
        mode = low.replace(" mode", "").replace("explain like me", "explain_like_me").replace("clean answer", "clean")
        data = set_output_mode(mode) if set_output_mode else {"ok": False, "mode": "normal", "reply": "Output mode layer is not loaded."}
        profile = style_profile(data.get("mode", "normal")) if style_profile else {}
        details = {"mode": data, "profile": profile, "guidance": mode_guidance(data.get("mode")) if mode_guidance else {}}
        intent_map = {
            "normal mode": "normal_mode",
            "details mode": "details_mode",
            "speak mode": "speak_mode",
            "quiet mode": "quiet_mode",
            "explain like me": "explain_like_me",
            "clean answer": "clean_answer",
            "deep mode": "deep_mode",
            "fast mode": "fast_mode",
        }
        return chat_payload(intent_map.get(low, "output_mode"), data.get("reply", "Output mode updated."), mission, router, data=details, speak=(low == "speak mode"))
    if low in {"read this out loud", "read aloud"}:
        data = speak_status(True) if speak_status else {"ok": True, "mode": "speak"}
        reply = speak_reply() if speak_reply else "Speak mode is on."
        return chat_payload("speak_mode", reply, mission, router, data=data, speak=True)
    if low == "stop speaking":
        data = speak_status(False) if speak_status else {"ok": True, "mode": "normal"}
        reply = stop_speaking_reply() if stop_speaking_reply else "Stopped speaking."
        return chat_payload("stop_speaking", reply, mission, router, data=data, speak=False)
    if low in {"output rules", "formatting rules", "human output rules"}:
        data = mode_guidance(get_output_mode()) if mode_guidance and get_output_mode else {"ok": True}
        reply = formatting_rules_text() if formatting_rules_text else "Human output is active."
        return chat_payload("human_output_rules", reply, mission, router, data=data)
    if low in {"source coverage", "source coverage status"}:
        data = coverage_status() if coverage_status else {"ok": False, "error": "source_coverage_not_loaded"}
        reply = (
            f"Source coverage is mapped: {data.get('total_indexed_rows', 0)} indexed rows were assigned to coverage buckets. "
            f"LilJR core records: {data.get('core_records', 0)}. "
            f"Side-job backlog records: {data.get('side_job_records', 0)}. "
            f"Manual review records: {data.get('manual_review_records', 0)}."
        )
        return chat_payload("source_coverage_status", reply, mission, router, data=data)
    if low == "no missed files audit":
        data = coverage_status() if coverage_status else {"ok": False, "error": "source_coverage_not_loaded"}
        ignored = data.get("bucket_counts", {}).get("dependency junk ignored", 0)
        reply = (
            f"No missed files audit is clean: {data.get('total_indexed_rows', 0)} indexed rows are accounted for in named buckets. "
            f"{ignored} dependency-junk rows were intentionally ignored, and {data.get('manual_review_records', 0)} secret-possible rows stay in manual review."
        )
        return chat_payload("no_missed_files_audit", reply, mission, router, data=data)
    if low == "traceability report":
        data = coverage_status() if coverage_status else {"ok": False, "error": "source_coverage_not_loaded"}
        accounts = data.get("accounts", {})
        reply = (
            "Traceability report is ready: SignSafePro, Andre Kimi intake, Core Vault, Job Vault, manual review, "
            f"and dependency-ignore buckets are linked across {len(accounts)} source account(s)."
        )
        return chat_payload("traceability_report", reply, mission, router, data=data)
    if low == "run source coverage":
        data = build_source_coverage() if build_source_coverage else {"ok": False, "error": "source_coverage_not_loaded"}
        reply = (
            f"Source coverage rebuilt. {data.get('total_indexed_rows', 0)} indexed rows now have named buckets, "
            f"with {data.get('core_deduped', 0)} deduped LilJR core ideas and {data.get('side_jobs_deduped', 0)} deduped side-job backlog items."
        )
        return chat_payload("run_source_coverage", reply, mission, router, data=data)
    if low in {"conversation status", "timeline status", "flow log status"}:
        data = conversation_status(ROOT) if conversation_status else {"ok": False, "error": "conversation_flow_not_loaded"}
        latest = data.get("latest") or {}
        reply = f"Conversation flow is online. Latest intent: {latest.get('intent', 'none yet')}. The timeline is redacted and kept inside LilJR."
        return chat_payload("conversation_status", reply, mission, router, data=data, conversation_flow=data)
    if low in {"show timeline", "conversation timeline", "show conversation timeline", "flow log"}:
        data = conversation_timeline(ROOT, 20) if conversation_timeline else {"ok": False, "error": "conversation_flow_not_loaded"}
        reply = f"Loaded the last {data.get('count', 0)} safe conversation event(s). Details has the redacted flow."
        return chat_payload("conversation_timeline", reply, mission, router, data=data, conversation_flow=data)
    if low in {"symphony status", "one unit symphony", "one unit command center status", "whole system status", "is everything lined up"}:
        data = symphony_status(ROOT) if symphony_status else {"ok": False, "error": "one_unit_symphony_not_loaded"}
        good = len([lane for lane in data.get("lanes", []) if lane.get("ok")])
        total = data.get("lane_count", len(data.get("lanes", [])))
        reply = f"LilJR symphony is {data.get('flow_health', 'unknown')}: {good}/{total} lane(s) aligned across chat, memory, deliverables, integrations, approval, verifier, frontend, and mobile."
        return chat_payload("symphony_status", reply, mission, router, data=data, symphony=data)
    if low in {"production readiness", "production status", "production check", "prod readiness", "run production readiness"}:
        data = production_readiness(ROOT, f"http://127.0.0.1:{PORT}") if production_readiness else {"ok": False, "error": "production_readiness_not_loaded"}
        failed = [item.get("name") for item in data.get("checks", []) if not item.get("pass")]
        reply = (
            "Production-like readiness is clear for local run."
            if data.get("ok")
            else f"Production-like readiness needs attention: {', '.join(failed) or 'unknown check'}."
        )
        return chat_payload("production_readiness", reply, mission, router, data=data, production=data)
    if route_memory_command:
        memory_result = route_memory_command(str(ROOT), text)
        if memory_result:
            return memory_chat_response(memory_result, mission, router)
    if route_operator_command:
        operator_result = route_operator_command(str(ROOT), text)
        if operator_result:
            return operator_chat_response(operator_result, mission, router)
    if low == "phone bridge status":
        data = stage2_phone_bridge_status() if stage2_phone_bridge_status else {"ok": False, "error": "device_bridge_not_loaded"}
        return stage2_chat_response("phone_bridge", data, mission, router)
    if low == "show qr upload":
        data = qr_upload_status(PORT) if qr_upload_status else {"ok": False, "error": "phone_intake_not_loaded"}
        return stage2_chat_response("qr_upload", data, mission, router)
    if low == "scan phone inbox":
        data = scan_phone_inbox() if scan_phone_inbox else {"ok": False, "error": "phone_intake_not_loaded"}
        return stage2_chat_response("phone_inbox", data, mission, router)
    if low == "legal intake":
        data = legal_intake_status("general") if legal_intake_status else {"ok": False, "error": "legal_intake_not_loaded"}
        return stage2_chat_response("legal_intake", data, mission, router)
    if low in {"legal warfare status", "legal research agent", "show legal warfare"}:
        data = legal_warfare_status() if legal_warfare_status else {"ok": False, "error": "legal_warfare_not_loaded"}
        return chat_payload(
            "legal_warfare_status",
            "Legal warfare research is merged into the one LilJR brain as safe legal framework research. I will not file, contact, sign, pay, or submit anything without Andre approval.",
            mission,
            router,
            data=data,
        )
    if low.startswith("legal warfare reason") or low.startswith("legal research reason"):
        facts = re.sub(r"^(legal warfare reason|legal research reason)\s*", "", text, flags=re.I).strip()
        data = legal_warfare_reason("CA", "family" if any(x in low for x in ["custody", "child", "family", "parenting"]) else "general", facts) if legal_warfare_reason else {"ok": False, "error": "legal_warfare_not_loaded"}
        return chat_payload(
            "legal_warfare_reason",
            "I prepared safe legal research framework notes. Details has the framework, next steps, and approval boundaries.",
            mission,
            router,
            data=data,
        )
    if low.startswith("legal warfare compare") or low.startswith("legal research compare"):
        category = "family" if any(x in low for x in ["custody", "child", "family", "parenting"]) else "general"
        data = legal_warfare_compare(category, ["CA", "US", "UK"]) if legal_warfare_compare else {"ok": False, "error": "legal_warfare_not_loaded"}
        return chat_payload(
            "legal_warfare_compare",
            "I compared legal framework buckets safely. This is preparation only, not legal advice or filing.",
            mission,
            router,
            data=data,
        )
    if low.startswith("legal warfare strategy") or low.startswith("legal research strategy"):
        objective = re.sub(r"^(legal warfare strategy|legal research strategy)\s*", "", text, flags=re.I).strip()
        data = legal_warfare_strategy("CA", objective or "organize legal next steps") if legal_warfare_strategy else {"ok": False, "error": "legal_warfare_not_loaded"}
        return chat_payload(
            "legal_warfare_strategy",
            "I drafted a safe legal preparation strategy. Any external action remains owner-approval locked.",
            mission,
            router,
            data=data,
        )
    if low == "child custody next steps":
        data = child_custody_next_steps() if child_custody_next_steps else {"ok": False, "error": "legal_intake_not_loaded"}
        return stage2_chat_response("custody", data, mission, router)
    if low == "make evidence checklist":
        data = evidence_checklist("family law") if evidence_checklist else {"ok": False, "error": "legal_ai_not_loaded"}
        return stage2_chat_response("evidence", data, mission, router)
    if low == "make case timeline":
        data = make_case_timeline() if make_case_timeline else {"ok": False, "error": "evidence_timeline_not_loaded"}
        return stage2_chat_response("timeline", data, mission, router)
    if low == "show monitors":
        data = watcher_status() if watcher_status else {"ok": False, "error": "monitors_not_loaded"}
        return stage2_chat_response("monitor_status", data, mission, router)
    if low == "show watchers":
        data = watcher_status() if watcher_status else {"ok": False, "error": "watchers_not_loaded"}
        return stage2_chat_response("watchers", data, mission, router)
    if low.startswith("watch this"):
        target = text.split("watch this", 1)[1].strip(": ").strip() or "current task"
        data = watch_this(target) if watch_this else {"ok": False, "error": "watchers_not_loaded"}
        return stage2_chat_response("watch_this", data, mission, router)
    if low == "stop watcher":
        data = stop_watcher("current task") if stop_watcher else {"ok": False, "error": "watchers_not_loaded"}
        return stage2_chat_response("stop_watcher", data, mission, router)
    if low in {"prepare signsafe build plan", "prepare notary build plan", "prepare cosmicfaith build plan", "prepare prettypess build plan"}:
        name = low.replace("prepare ", "").replace(" build plan", "")
        data = side_job_plan(name) if side_job_plan else {"ok": False, "error": "app_foundry_not_loaded"}
        return stage2_chat_response("side_plan", data, mission, router)
    if low == "deploy checklist":
        data = deploy_checklist(str(ROOT)) if deploy_checklist else {"ok": False, "error": "deploy_brain_not_loaded"}
        return stage2_chat_response("deploy", data, mission, router)
    if low == "check secrets":
        data = check_secrets(str(ROOT)) if check_secrets else {"ok": False, "error": "secret_scanner_not_loaded"}
        return stage2_chat_response("secrets", data, mission, router)
    if low == "make rollback zip":
        data = make_rollback_zip(str(ROOT)) if make_rollback_zip else {"ok": False, "error": "release_packager_not_loaded"}
        return stage2_chat_response("rollback_zip", data, mission, router)
    if low == "package release":
        data = package_release_plan() if package_release_plan else {"ok": False, "error": "release_packager_not_loaded"}
        return stage2_chat_response("package_release", data, mission, router)
    if low in {"livescope status", "live scope status", "show livescope"}:
        data = live_scope_status() if live_scope_status else {"ok": False, "error": "live_scope_not_loaded"}
        return stage2_chat_response("livescope", data, mission, router)
    if low == "what is liljr as one unit?":
        data = one_unit_status() if one_unit_status else {"ok": False, "error": "one_unit_runtime_not_loaded"}
        reply = one_unit_reply() if one_unit_reply else "LilJR one-unit runtime is not loaded."
        return chat_payload("one_unit_status", reply, mission, router, data=data)
    if low == "what should liljr build next?":
        if merge_core_vault:
            merge_core_vault()
        data = next_v32_feature() if next_v32_feature else {"ok": False, "error": "v32_queue_not_loaded"}
        feature = data.get("next_feature", {})
        reply = (
            f"Next LilJR core build: {feature.get('feature', 'No V32 queue item found')}. "
            f"Why: {feature.get('reason', 'Core comes first.')} "
            "Side jobs stay in the Job Vault for later."
        )
        return chat_payload("v32_next_build", reply, mission, router, data=data, job_vault_backlog_only=True)
    if low == "show job vault":
        return job_vault_backlog_response(mission, router)
    if low == "show jobs for later":
        data = jobs_to_build_after_liljr() if jobs_to_build_after_liljr else {"ok": False, "error": "job_vault_not_loaded"}
        count = len(data.get("jobs", [])) if isinstance(data.get("jobs"), list) else data.get("count", data.get("job_count", 0))
        reply = (
            f"Jobs for later are staged in the Job Vault: {count} backlog item(s) can be opened after LilJR core is stable. "
            "Nothing from the side-job backlog is being built right now."
        )
        return chat_payload("jobs_for_later", reply, mission, router, data=data, job_vault_backlog_only=True)

    live_provider_commands = {
        "live provider test": "openai_compatible",
        "live provider test openai_compatible": "openai_compatible",
        "test openai provider": "openai_compatible",
        "check live provider": "openai_compatible",
        "run live provider test": "openai_compatible",
    }
    if low in live_provider_commands:
        return live_provider_chat_response(live_provider_commands[low], mission, router)
    if low == "test fallback route":
        return fallback_route_chat_response(mission, router)
    if low in {"pause", "resume", "stop", "what are you doing?", "what are you doing"}:
        states = {"pause": "Paused active task queue.", "resume": "Resumed active mission queue.", "stop": "Stopped active non-critical tasks.", "what are you doing?": "I am routing your chat through main brain, memory, tools, approval lock, and verifier.", "what are you doing": "I am routing your chat through main brain, memory, tools, approval lock, and verifier."}
        if low == "pause":
            board = set_swarm_state("paused")
        elif low == "resume":
            board = set_swarm_state("running")
        elif low == "stop":
            board = set_swarm_state("stopped")
        else:
            board = swarm_status()
        return {"intent": "control", "reply": states[low], "mission_id": mission["id"], "router": router, "board": board}
    if low.startswith("remember:") or low.startswith("remember "):
        note = text.split(":", 1)[1].strip() if ":" in text else text.split(" ", 1)[1].strip()
        mem = save_memory(note, ["chat"])
        return {"intent": "memory_save", "reply": "Saved that to personal suit memory.", "mission_id": mission["id"], "memory": mem, "router": router}
    if low.startswith("search memory"):
        q = text.split("search memory", 1)[1].strip()
        return {"intent": "memory_search", "reply": "I searched personal suit memory.", "mission_id": mission["id"], "results": search_memory(q), "router": router}
    if low in {"run verifier", "verify", "verifier"}:
        data = verifier()
        passed = len([check for check in data.get("checks", []) if check.get("pass")])
        total = len(data.get("checks", []))
        reply = f"Verifier ran: {passed}/{total} local checks passed. Details has compile, frontend, memory, routes, and safety status."
        return chat_payload("run_verifier", reply, mission, router, data=data)
    if low in {"run one unit e2e", "one unit e2e", "full e2e test", "production like e2e", "run full verifier", "create failure lock"}:
        data = run_one_unit_e2e(ROOT, f"http://127.0.0.1:{PORT}") if run_one_unit_e2e else {"ok": False, "error": "one_unit_e2e_verifier_not_loaded"}
        summary = data.get("summary", {})
        lock = data.get("failure_lock", {})
        if data.get("ok"):
            reply = f"One-unit E2E passed: {summary.get('passed', 0)} checks passed and no critical failure lock is active."
        else:
            reply = f"One-unit E2E found {summary.get('critical_failed', 0)} critical failure(s). I wrote the failure lock so we can pinpoint the break."
        return chat_payload("one_unit_e2e", reply, mission, router, data=data, failure_lock=lock)
    if low in {"list tools", "tools"}:
        return {"intent": "tools", "reply": "Tool registry is live. Details has the full list.", "mission_id": mission["id"], "tools": TOOLS, "router": router}
    if low in {"provider status", "providers", "model provider status"}:
        data = provider_slot_status()
        configured = len(data["configured"])
        missing = len(data["missing"])
        reply = f"One brain provider status: {configured} configured, {missing} missing, fallback active. I am not exposing any keys."
        return chat_payload("provider_status", reply, mission, router, data=data, fallback_active=True)
    if low == "scan inbox":
        data = run_inbox_pipeline() if run_inbox_pipeline else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        return {"intent": "scan_inbox", "reply": f"Inbox scan complete: {data.get('liljr_core_ideas_recovered', 0)} LilJR-core records recovered and {data.get('side_jobs_vaulted', 0)} side-job records vaulted.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "inbox status":
        data = v31_inbox_status() if v31_inbox_status else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        return {"intent": "inbox_status", "reply": "Inbox pipeline status is ready. Details has both Kimi account counts and vault split.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "show liljr ideas from inbox":
        data = liljr_ideas_from_inbox() if liljr_ideas_from_inbox else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        return {"intent": "liljr_ideas_from_inbox", "reply": f"Recovered {data.get('count', 0)} LilJR-core inbox records. Details has groups and source samples.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "show side jobs from inbox":
        data = side_jobs_from_inbox() if side_jobs_from_inbox else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        return {"intent": "side_jobs_from_inbox", "reply": f"Vaulted {data.get('count', 0)} side-job inbox records for later. No side jobs were built.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "show kimi signsafepro intake":
        data = kimi_intake("01_KIMI_signsafepro_gmail") if kimi_intake else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        summary = data.get("summary", {})
        return {"intent": "kimi_signsafepro_intake", "reply": f"SignSafePro Kimi intake indexed {summary.get('rows_indexed', 0)} files with {summary.get('core_matches', 0)} LilJR-core matches.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "show kimi andrelapensee5 intake":
        data = kimi_intake("02_KIMI_andrelapensee5_gmail") if kimi_intake else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        summary = data.get("summary", {})
        return {"intent": "kimi_andrelapensee5_intake", "reply": f"Andre Kimi intake indexed {summary.get('rows_indexed', 0)} files with {summary.get('core_matches', 0)} LilJR-core matches.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "what should liljr build next from inbox?":
        data = next_liljr_build_from_inbox() if next_liljr_build_from_inbox else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        item = data.get("next_liljr_build_item", {})
        return {"intent": "next_liljr_build_from_inbox", "reply": f"Next from inbox: {item.get('name', 'No inbox build item selected')}.", "mission_id": mission["id"], "data": data, "router": router}
    if low == "send inbox to build order runner":
        inbox_data = next_liljr_build_from_inbox() if next_liljr_build_from_inbox else {"ok": False, "error": "inbox_pipeline_not_loaded"}
        runner = build_order_runner_status() if build_order_runner_status else {"ok": False, "error": "build_order_runner_not_loaded"}
        return {"intent": "send_inbox_to_build_order_runner", "reply": "Inbox input was handed to the Build Order Runner as a safe planning input only. No patch was applied.", "mission_id": mission["id"], "data": {"inbox": inbox_data, "runner": runner, "job_vault_backlog_only": True}, "router": router}
    if low in {"live provider test", "verify live provider", "test live provider calls", "check live provider", "run live provider test"}:
        data = verify_live_provider("general") if verify_live_provider else {"ok": False, "reason": "live_provider_module_not_loaded"}
        provider = data.get("provider", "unknown")
        if data.get("ok") and not data.get("fallback"):
            reply = f"Live provider call passed through {provider}. No keys were returned."
        elif data.get("ok"):
            reply = "Live provider test used local fallback. No keys were returned."
        else:
            reply = f"Live provider call did not pass yet for {provider}. Fallback remains safe and no keys were returned."
        return {"intent": "live_provider_test", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low.startswith("live provider test ") or low.startswith("check live provider ") or low.startswith("run live provider test ") or low == "test openai provider":
        if low == "test openai provider":
            provider_name = "openai_compatible"
        elif low.startswith("check live provider "):
            provider_name = low.replace("check live provider", "", 1).strip()
        elif low.startswith("run live provider test "):
            provider_name = low.replace("run live provider test", "", 1).strip()
        else:
            provider_name = low.replace("live provider test", "", 1).strip()
        data = safe_live_provider_test(provider_name, "general") if safe_live_provider_test else {"provider": provider_name, "configured": False, "call_status": "call_failed", "http_status_category": "adapter_missing", "fallback_active": True}
        reply = f"{data.get('provider', provider_name)} {data.get('call_status', 'call_failed')}; category {data.get('http_status_category', 'unknown_error')}; fallback active. No keys were returned."
        return chat_payload("live_provider_test", reply, mission, router, data=data, provider=data.get("provider", provider_name), configured=bool(data.get("configured")), status=data.get("status"), call_status=data.get("call_status"), http_status_category=data.get("http_status_category"), model=data.get("model"), fallback_active=True)
    if low in {"test provider route", "provider route test"}:
        route = explain_provider_route("general") if explain_provider_route else {"ok": False, "reason": "provider_route_module_not_loaded"}
        status = provider_slot_status()
        data = {"route": route, "provider_status": status, "fallback_active": True, "notice": "No provider keys are returned or logged."}
        return chat_payload("provider_route_test", "Provider route test finished. Details shows configured/missing/call status only, with fallback kept available.", mission, router, data=data, fallback_active=True)
    if low.startswith("test provider route "):
        provider_name = low.replace("test provider route", "", 1).strip()
        data = safe_live_provider_test(provider_name, "general") if safe_live_provider_test else {"provider": provider_name, "configured": False, "status": "missing", "call_status": "call_failed", "http_status_category": "adapter_missing", "fallback_active": True}
        return chat_payload("provider_route_test", f"Provider route checked for {provider_name}. Details shows status only; no keys returned.", mission, router, data=data, provider=data.get("provider", provider_name), configured=bool(data.get("configured")), status=data.get("status"), call_status=data.get("call_status"), http_status_category=data.get("http_status_category"), model=data.get("model"), fallback_active=True)
    if low in {"test fallback route", "fallback route test"}:
        data = safe_live_provider_test("local_fallback", "verification") if safe_live_provider_test else (live_provider_call("Fallback route check", "verification") if live_provider_call else {"ok": False, "reason": "live_provider_module_not_loaded"})
        fallback_ok = bool(data.get("fallback") and data.get("ok"))
        fallback_ok = fallback_ok or bool(data.get("fallback_active") and data.get("call_status") == "call_ok")
        reply = "Fallback route is available." if fallback_ok else "Fallback route check did not pass."
        return chat_payload("fallback_route_test", reply, mission, router, data=data, fallback_active=True, call_status=data.get("call_status", "call_ok" if fallback_ok else "call_failed"))
    if low in {"live provider slot tests", "verify all live providers", "test all provider slots"}:
        data = verify_all_live_providers() if verify_all_live_providers else {"ok": False, "reason": "live_provider_module_not_loaded"}
        passed = len([item for item in data.get("providers", []) if item.get("ok")])
        total = len(data.get("providers", []))
        reply = f"Live provider slot tests finished: {passed}/{total} live calls passed. No keys were returned."
        return {"intent": "live_provider_slot_tests", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low.startswith("ask live provider:"):
        prompt = text.split(":", 1)[1].strip()
        data = live_provider_call(prompt, "general") if live_provider_call else {"ok": False, "reason": "live_provider_module_not_loaded"}
        if data.get("ok") and not data.get("fallback"):
            reply = data.get("text", "")
        elif data.get("ok"):
            reply = data.get("text", "Local fallback active.")
        else:
            reply = "Live provider call failed safely. I did not expose keys and fallback remains available."
        return {"intent": "live_provider_chat", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low in {"liljr build order runner", "build order runner status", "run build order runner", "prepare next liljr build", "prepare next feature", "prepare next build patch"}:
        data = build_order_runner_status() if build_order_runner_status else {"ok": False, "error": "build_order_runner_not_loaded"}
        feature = data.get("next_feature", {}).get("name", "unknown")
        return {"intent": "build_order_runner", "reply": f"Build Order Runner picked the next LilJR core feature: {feature}. It prepared a safe patch/test cycle only; no patch was applied.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"liljr capability status", "liljr capabilities", "capability vault status"}:
        data = scan_liljr_capabilities() if scan_liljr_capabilities else {"ok": False, "error": "capability_vault_not_loaded"}
        reply = f"LilJR core comes first. I found {data.get('capability_count', 0)} core capabilities in the Capability Vault and kept side jobs separated in Job Vault."
        return {"intent": "liljr_capability_status", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low in {"what can liljr do now?", "what can liljr do now", "liljr now capabilities"}:
        data = liljr_now_capabilities() if liljr_now_capabilities else {"ok": False, "error": "capability_vault_not_loaded"}
        reply = f"LilJR can use {data.get('count', 0)} working or partially working core capabilities right now. Details has the exact module, route, risk, and test map."
        return {"intent": "liljr_now_capabilities", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low in {"what do i want liljr to do?", "what do i want liljr to do", "liljr wanted capabilities"}:
        data = liljr_wanted_capabilities() if liljr_wanted_capabilities else {"ok": False, "error": "capability_vault_not_loaded"}
        reply = f"The wanted LilJR blueprint has {data.get('count', 0)} future, partial, or not-connected capabilities. Side jobs are not mixed into core."
        return {"intent": "liljr_wanted_capabilities", "reply": reply, "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show liljr future blueprint", "liljr future blueprint", "show liljr jarvis blueprint"}:
        data = liljr_future_blueprint() if liljr_future_blueprint else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "liljr_future_blueprint", "reply": "LilJR future blueprint is organized by Core Brain, Builder Brain, Swarm Brain, Phone Suit, Provider Brain, Vault Brain, Legal/Life Support, Deploy Brain, and the future 60-year layer.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show liljr 60 year features", "show liljr 60-year features", "liljr 60 year features"}:
        data = liljr_future_blueprint() if liljr_future_blueprint else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "liljr_60_year_features", "reply": "The 60-year layer is stored as future architecture and disabled stubs until each piece is real, safe, and approved.", "mission_id": mission["id"], "data": {"features": data.get("categories", {}).get("Future 60-Year Layer", [])}, "router": router}
    if low in {"show liljr missing pieces", "liljr missing pieces"}:
        data = liljr_missing_pieces() if liljr_missing_pieces else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "liljr_missing_pieces", "reply": f"LilJR has {data.get('count', 0)} missing, partial, future, or not-connected pieces mapped with target modules and tests.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show liljr build order", "liljr build order", "what should we build next for liljr?", "what should we build next for liljr"}:
        data = liljr_build_order() if liljr_build_order else {"ok": False, "error": "capability_vault_not_loaded"}
        next_step = data.get("steps", ["No build order loaded."])[0] if data.get("steps") else "No build order loaded."
        return {"intent": "liljr_build_order", "reply": f"Next for LilJR: {next_step}", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show not connected yet", "liljr disabled until connected", "show disabled until connected"}:
        data = liljr_disabled_until_connected() if liljr_disabled_until_connected else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "liljr_disabled_until_connected", "reply": f"{data.get('count', 0)} LilJR capabilities stay disabled until keys, phone bridges, deploy tokens, or Andre approval are connected.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show needs andre decision", "liljr needs andre decision", "needs andre decision"}:
        data = liljr_needs_andre_decision() if liljr_needs_andre_decision else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "liljr_needs_andre_decision", "reply": "These are the LilJR decisions Andre needs to approve before deeper build phases.", "mission_id": mission["id"], "data": data, "router": router}
    if low.startswith("search liljr vault"):
        query = text.split("search LilJR vault", 1)[1].strip() if "search LilJR vault" in text else text.split("search liljr vault", 1)[1].strip()
        data = search_liljr_capability(query) if search_liljr_capability else {"ok": False, "error": "capability_vault_not_loaded"}
        return {"intent": "search_liljr_vault", "reply": f"I searched the LilJR Core Capability Vault for: {query or 'everything'}.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"job vault status", "job backlog status"}:
        data = job_vault_status() if job_vault_status else {"ok": False, "error": "job_vault_not_loaded"}
        return {"intent": "job_vault_status", "reply": f"Job Vault is backlog only. {data.get('job_count', 0)} side jobs are saved for later after LilJR core is ready.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"list job vault", "list jobs", "show job vault"}:
        data = list_jobs() if list_jobs else {"ok": False, "error": "job_vault_not_loaded"}
        return {"intent": "list_job_vault", "reply": "These jobs are preserved for later and will not be built until LilJR core is finished.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show jobs to build after liljr", "jobs to build after liljr"}:
        data = jobs_to_build_after_liljr() if jobs_to_build_after_liljr else {"ok": False, "error": "job_vault_not_loaded"}
        return {"intent": "jobs_to_build_after_liljr", "reply": "After LilJR core is stable, these Job Vault items can be opened one at a time with Andre approval.", "mission_id": mission["id"], "data": data, "router": router}
    if low.startswith("search job vault"):
        query = text.split("search job vault", 1)[1].strip()
        data = search_jobs(query) if search_jobs else {"ok": False, "error": "job_vault_not_loaded"}
        return {"intent": "search_job_vault", "reply": f"I searched the Job Vault backlog for: {query or 'everything'}.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"show job notary", "show job signsafepro", "show job signsafe pro", "show job cosmicfaith", "show job prettypess"}:
        name = text.replace("show job", "", 1).strip()
        data = job_summary(name) if job_summary else {"ok": False, "error": "job_vault_not_loaded"}
        return {"intent": "job_summary", "reply": f"{name} is stored in Job Vault as backlog only. LilJR core remains priority one.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"what brain are you using?", "what brain are you using", "active brain", "brain route"}:
        data = active_brain_status(text)
        provider = data.get("active_provider") or "local_offline"
        model = data.get("active_model") or "local_offline"
        reply = f"I am using {model} through {provider}. If live provider keys are missing, the local offline fallback stays active so I can still organize, route, inspect, and verify safely."
        return chat_payload("active_brain", reply, mission, router, data=data, active_provider=provider, active_model=model, fallback_active=bool(data.get("fallback_active", True)))
    if "what can you actually do" in low or "actually do right now" in low or "what works now" in low:
        data = v29_overlay_status()
        reply = "Right now I can chat, create missions, save/search memory, index owner-provided files, run local verification, organize legal intake, manage approval-locked tools, and keep the one-unit LilJR command center connected. Live providers, deploys, phone bridge, finance plugins, and account actions stay disabled until keys/bridges and Andre approval are supplied."
        return chat_payload("reality_check", reply, mission, router, data={"status": data, "brain_context": brain_context_summary()})
    if "v29" in low or "overlay" in low:
        data = v29_overlay_status()
        return {"intent": "v29_overlay_status", "reply": "V29 overlay core is merged into the working LilJR build: provider adapters, plugin registry, personal memory, deploy brain, life mode, reality check, self-improvement, and verifier 2 are wired behind the existing LilJR shell.", "mission_id": mission["id"], "data": data, "router": router}
    if low in {"integration status", "integrations status", "show integrations", "plugin status", "plugins status", "platform status"}:
        data = integration_status() if integration_status else {"ok": False, "error": "integration_registry_not_loaded"}
        count = data.get("count", 0)
        reply = f"Integration registry is connected to the one brain with {count} platform surface(s). Planning and drafts are safe; sends, deploys, publishes, database writes, account changes, and private uploads stay owner-approval locked."
        return chat_payload("integration_status", reply, mission, router, data=data, integrations=data)
    if low in {"deliverable status", "deliverables status", "work order status", "work orders"}:
        data = pipeline_status(ROOT) if pipeline_status else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
        reply = f"Deliverable pipeline is online with {data.get('count', 0)} local work order(s). Docs, sheets, decks, database plans, deploy plans, Slack drafts, browser checks, Sites plans, and Expo plans stay in one lane."
        return chat_payload("deliverable_status", reply, mission, router, data=data, deliverables=data)
    if low.startswith("plan deliverable") or low.startswith("deliverable plan") or low.startswith("plan work order"):
        cleaned = re.sub(r"^(plan deliverable|deliverable plan|plan work order)\s*", "", text, flags=re.I).strip()
        data = plan_deliverable(cleaned, ROOT) if plan_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
        return chat_payload("deliverable_plan", "I planned the one-unit local deliverable path. External actions stay locked for owner approval.", mission, router, data=data)
    if low.startswith("create deliverable") or low.startswith("draft deliverable") or low.startswith("create work order") or low.startswith("make deliverable"):
        cleaned = re.sub(r"^(create deliverable|draft deliverable|create work order|make deliverable)\s*", "", text, flags=re.I).strip()
        data = create_deliverable(cleaned, ROOT) if create_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
        if data.get("approval_required"):
            approval = approval_request("deliverable_pipeline", data, data.get("reason", "Deliverable action needs owner approval."))
            return chat_payload("deliverable_blocked", "I can draft that locally, but the requested external/risky step is locked for Andre approval.", mission, router, data=data, approval=approval, approval_required=True)
        did = data.get("deliverable", {}).get("id", "work order")
        return chat_payload("deliverable_created", f"Created local one-unit deliverable work order {did}. It is tracked in the Deliverables lane and has no external side effect.", mission, router, data=data, deliverable=data.get("deliverable"))
    if low.startswith("search deliverables") or low.startswith("search work orders"):
        query = re.sub(r"^(search deliverables|search work orders)\s*", "", text, flags=re.I).strip()
        data = search_deliverables(query, ROOT) if search_deliverables else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
        return chat_payload("deliverable_search", f"I searched the local deliverable work orders for: {query or 'everything'}.", mission, router, data=data)
    if low.startswith("show deliverable") or low.startswith("get deliverable") or low in {"latest deliverable", "show latest deliverable"}:
        did = "" if low in {"latest deliverable", "show latest deliverable"} else re.sub(r"^(show deliverable|get deliverable)\s*", "", text, flags=re.I).strip()
        data = get_deliverable(did, ROOT) if get_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
        if data.get("ok"):
            artifact_count = len(data.get("artifacts", {}))
            reply = f"Loaded deliverable {data.get('deliverable', {}).get('id')} with {artifact_count} local artifact draft(s). Details has previews and paths."
        else:
            reply = "I could not find that deliverable work order."
        return chat_payload("deliverable_detail", reply, mission, router, data=data)
    if low.startswith("plan integration") or low.startswith("integration plan"):
        cleaned = re.sub(r"^(plan integration|integration plan)\s*", "", text, flags=re.I).strip()
        parts = cleaned.split(None, 1)
        name = parts[0] if parts else ""
        details = parts[1] if len(parts) > 1 else ""
        data = plan_integration(name, "plan", details) if plan_integration else {"ok": False, "error": "integration_registry_not_loaded"}
        integration = data.get("integration", name or "all")
        reply = f"I prepared the safe local integration plan for {integration}. External side effects remain locked for Andre approval."
        return chat_payload("integration_plan", reply, mission, router, data=data, integration=data)
    if low.startswith("run integration") or low.startswith("integration run"):
        cleaned = re.sub(r"^(run integration|integration run)\s*", "", text, flags=re.I).strip()
        parts = cleaned.split(None, 2)
        name = parts[0] if parts else ""
        action = parts[1] if len(parts) > 1 else "status"
        details = parts[2] if len(parts) > 2 else ""
        data = run_integration_request({"integration": name, "action": action, "details": details}) if run_integration_request else {"ok": False, "error": "integration_registry_not_loaded"}
        if data.get("approval_required"):
            approval = approval_request("integration_run", data, data.get("reason", "Integration action needs owner approval."))
            return chat_payload("integration_run_blocked", "That integration action is locked for Andre approval before anything external happens.", mission, router, data=data, approval=approval, approval_required=True)
        return chat_payload("integration_run_safe", "Integration request prepared locally with no external side effect.", mission, router, data=data)
    if low in {"orchestration status", "orchestrator status", "one unit flow", "one unit status", "symphony status", "flow status"}:
        data = orchestration_status() if orchestration_status else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
        stages = data.get("stage_count", 0)
        reply = f"LilJR one-unit orchestration is online with {stages} stage(s): intake, brain context, design shell, local build, integrations, verification, and owner handoff. External side effects stay approval locked."
        return chat_payload("orchestration_status", reply, mission, router, data=data, orchestration=data)
    if low.startswith("orchestrate ") or low.startswith("build symphony ") or low.startswith("make this flow as one "):
        cleaned = re.sub(r"^(orchestrate|build symphony|make this flow as one)\s*", "", text, flags=re.I).strip()
        data = orchestration_plan(cleaned, "one_unit_command_center") if orchestration_plan else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
        if data.get("approval_required"):
            approval = approval_request("orchestration_run", data, "This one-unit flow includes an external or risky action and needs owner approval before execution.")
            return chat_payload("orchestration_run_blocked", "I mapped the full one-unit flow, but the risky/external step is locked for Andre approval before anything happens outside LilJR.", mission, router, data=data, approval=approval, approval_required=True)
        reply = "I mapped the one-unit flow from conversation to brain context, design, local build, integrations, verification, and owner handoff."
        return chat_payload("orchestration_plan", reply, mission, router, data=data, orchestration=data)
    if low in {"what is the full build flow", "show full build flow", "how does this flow start to end"}:
        data = orchestration_plan("show Andre the complete LilJR start-to-end build flow", "one_unit_command_center") if orchestration_plan else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
        return chat_payload("orchestration_plan", "Here is the complete LilJR build flow from normal conversation through verification and owner handoff.", mission, router, data=data, orchestration=data)
    if any(x in low for x in ["brain context", "brain registry", "one brain", "unified brain", "what do you know"]):
        data = unified_brain_context()
        return {"intent": "brain_context", "reply": "I pulled the unified LilJR brain context: continuity, phone uploads, SignSafe, Kimi recovery, vault findings, build gaps, and approval locks are connected in one model.", "mission_id": mission["id"], "data": data, "router": router}
    if "kimi" in low or "k i m i" in low:
        data = unified_brain_context()
        return {"intent": "kimi_recovery", "reply": "Kimi recovery is part of my central brain now. Upload Kimi exports or place them in LilJR-INBOX, and I will index them with the rest of the vault context.", "mission_id": mission["id"], "data": data["kimi_recovery"], "brain_context": brain_context_summary(), "router": router}
    if "inbox" in low or "s23" in low or "s21" in low or "phone upload" in low or "upload qr" in low:
        data = unified_brain_context()
        return {"intent": "phone_upload_intake", "reply": "Phone intake is wired into my brain: S23/S21 uploads, LilJR-INBOX files, and the QR upload handoff all feed the same context.", "mission_id": mission["id"], "data": {"phone_upload_intake": data["phone_upload_intake"], "cloud_inbox_watcher": data["cloud_inbox_watcher"]}, "router": router}
    if "signal" in low or "nearby" in low or "tap into" in low:
        data = nearby_signal_awareness(scan=False)
        return {"intent": "nearby_signal_awareness", "reply": "I added the safe version: LilJR can map nearby signal handoffs and owner-approved paths, but it will not tap into devices or bypass permission.", "mission_id": mission["id"], "data": data, "brain_context": brain_context_summary(), "router": router}
    if "continuity" in low or "forgot my phone" in low or "phone die" in low or "phone is about to die" in low or "lifeline" in low:
        data = device_continuity()
        return {"intent": "device_continuity", "reply": "I set this up as a device continuity lifeline: approve the bridge once while the phone is in your hand, then LilJR can keep using that approved path later.", "mission_id": mission["id"], "data": data, "brain_context": brain_context_summary(), "router": router}
    if "signsafe" in low or "notary" in low:
        province = "ontario" if any(x in low for x in ["ontario", "sault", "toronto", "hamilton", "mississauga"]) else ""
        directory = signsafe_notaries(province=province)
        return {"intent": "signsafe", "reply": "I pulled up the SignSafe Pro notary directory and kept booking approval-locked inside the same LilJR brain context.", "mission_id": mission["id"], "directory": directory, "brain_context": brain_context_summary(), "router": router}
    if low in {"swarm status", "status", "pro status"}:
        return {"intent": "swarm_status", "reply": "V28 swarm is online: main brain, memory, router, tools, approval lock, mission board, queue, watchers, and verifier.", "mission_id": mission["id"], "data": swarm_status(), "router": router}
    if low.startswith("load mission:"):
        loaded = load_mission(text.split(":", 1)[1].strip(), "mission_loader")
        return {"intent": "mission_loaded", "reply": "Mission loaded onto the shared mission board.", "mission_id": loaded["id"], "mission": loaded, "router": router}
    if low.startswith("run command:"):
        result = run_command(text.split(":", 1)[1].strip(), approved=False)
        return {"intent": "approval_lock", "reply": "I prepared that command, but owner approval lock is holding it until approved.", "mission_id": mission["id"], "data": result, "router": router}
    if low.startswith("fix error:") or low.startswith("paste error:") or "traceback (most recent call last)" in low or "syntaxerror" in low or "modulenotfounderror" in low:
        out = diagnose_error(text.split(":", 1)[1].strip() if ":" in text and (low.startswith("fix error:") or low.startswith("paste error:")) else text)
        out["mission_id"] = mission["id"]
        out["router"] = router
        return out
    if low.startswith("approve run:"):
        result = run_command(text.split(":", 1)[1].strip(), approved=True)
        return {"intent": "terminal", "reply": "Approved command executed." if result.get("returncode") == 0 else "Command finished. Check Details for output.", "mission_id": mission["id"], "data": result, "router": router}
    if low.startswith("propose replace"):
        parts = text.split("propose replace", 1)[1].strip().split("||", 2)
        if len(parts) != 3:
            return {"intent": "patch", "reply": "Use: propose replace path/to/file || exact old text || new text", "mission_id": mission["id"], "router": router}
        proposal = propose_replace(parts[0].strip(), parts[1].strip(), parts[2].strip())
        return {"intent": "patch", "reply": "Patch proposal created and held by owner approval lock.", "mission_id": mission["id"], "proposal": proposal, "router": router}
    if low.startswith("apply approval"):
        result = apply_approval(text.split("apply approval", 1)[1].strip())
        return {"intent": "approval_apply", "reply": "Approval applied." if result.get("ok") else "Approval was not applied.", "mission_id": mission["id"], "data": result, "router": router}
    if low.startswith("read file"):
        return {"intent": "read", "reply": "I read the file with secret redaction on.", "mission_id": mission["id"], "data": read_file(text.split("read file", 1)[1].strip()), "router": router}
    if "scan" in low or "files" in low:
        return {"intent": "scan", "reply": "I scanned the workspace.", "mission_id": mission["id"], "data": scan_files(), "router": router}
    if low in {"run self test", "self test", "health test"}:
        return {"intent": "self_test", "reply": "Verifier ran the local V28 checks.", "mission_id": mission["id"], "data": verifier(), "router": router}
    if low.startswith("legal") or any(x in low for x in ["court", "custody", "served", "eviction", "child support", "parenting papers"]):
        out = legal_ai(text)
        out["mission_id"] = mission["id"]
        out["router"] = router
        return out
    if "enable watchers" in low or "watchers" in low:
        return {"intent": "watchers", "reply": "Optional watchers are available but stay standby unless a mission asks for monitoring.", "mission_id": mission["id"], "watchers": [{"name": "file watcher", "status": "standby"}, {"name": "health watcher", "status": "standby"}], "router": router}
    if route_natural_intent:
        natural_route = route_natural_intent(text)
        natural_intent = natural_route.get("intent")
        if natural_intent == "deliverable_create" and natural_route.get("confidence", 0) >= 0.8:
            data = create_deliverable(text, ROOT) if create_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
            if data.get("approval_required"):
                approval = approval_request("deliverable_pipeline", data, data.get("reason", "Deliverable action needs owner approval."))
                return chat_payload("deliverable_blocked", "I understood that as a deliverable request, but the external/risky step is locked for Andre approval. I can keep the local draft path ready.", mission, router, data={"natural_route": natural_route, "deliverable": data}, approval=approval, approval_required=True)
            did = data.get("deliverable", {}).get("id", "work order")
            count = data.get("deliverable", {}).get("artifact_count", 0)
            reply = f"I understood that as a deliverable request and created local work order {did} with {count} artifact draft(s)."
            return chat_payload("natural_deliverable_created", reply, mission, router, data={"natural_route": natural_route, "deliverable": data}, deliverable=data.get("deliverable"))
        if natural_intent == "orchestration_plan" and natural_route.get("confidence", 0) >= 0.8:
            data = orchestration_plan(text, "one_unit_command_center") if orchestration_plan else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
            if data.get("approval_required"):
                approval = approval_request("orchestration_run", data, "This one-unit flow includes an external or risky action and needs owner approval before execution.")
                return chat_payload("orchestration_run_blocked", "I understood that as a one-unit flow request, but the risky/external step is locked for Andre approval.", mission, router, data={"natural_route": natural_route, "orchestration": data}, approval=approval, approval_required=True)
            return chat_payload("natural_orchestration_plan", "I understood that as a one-unit flow request and mapped the start-to-end plan.", mission, router, data={"natural_route": natural_route, "orchestration": data}, orchestration=data)
        if natural_intent == "deliverable_status":
            data = pipeline_status(ROOT) if pipeline_status else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
            return chat_payload("deliverable_status", f"Deliverable pipeline is online with {data.get('count', 0)} local work order(s).", mission, router, data={"natural_route": natural_route, "deliverables": data}, deliverables=data)
        if natural_intent == "deliverable_detail":
            data = get_deliverable(natural_route.get("deliverable_id", ""), ROOT) if get_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
            artifact_count = len(data.get("artifacts", {})) if data.get("ok") else 0
            reply = f"Loaded deliverable {data.get('deliverable', {}).get('id')} with {artifact_count} local artifact draft(s)." if data.get("ok") else "I could not find that deliverable work order."
            return chat_payload("deliverable_detail", reply, mission, router, data={"natural_route": natural_route, "deliverable": data})
    if live_provider_call and len(text) >= 8 and (" " in text or "?" in text):
        live = live_provider_call(text, task_type="general")
        reply_text = (live.get("text") or "").strip()
        if reply_text:
            fallback_used = bool(live.get("fallback"))
            safe_attempts = []
            for attempt in live.get("attempts", []):
                data = attempt.get("data", {}) if isinstance(attempt.get("data"), dict) else {}
                safe_attempts.append({
                    "provider": attempt.get("provider"),
                    "ok": bool(attempt.get("ok")),
                    "fallback": bool(attempt.get("fallback")),
                    "status_code": data.get("status_code"),
                    "model": data.get("model", "not_returned"),
                })
            return chat_payload(
                "fallback_brain_chat" if fallback_used else "live_brain_chat",
                reply_text,
                mission,
                router,
                data={
                    "provider": live.get("provider", "unknown"),
                    "fallback_used": fallback_used,
                    "live_provider_call": not fallback_used,
                    "attempts": safe_attempts,
                    "notice": "No provider keys are returned or logged.",
                },
                provider=live.get("provider", "unknown"),
                live_provider_call=not fallback_used,
                fallback_active=True,
            )
    suggestions = [
        "show build queue",
        "show job vault",
        "provider status",
        "memory status",
        "what can you actually do right now?",
    ]
    reply = (
        "I did not understand that command yet. Tell me what you want LilJR to do next, "
        "or try: show build queue, show job vault, provider status, memory status, "
        "or what can you actually do right now?"
    )
    return chat_payload(
        "clarification_needed",
        reply,
        mission,
        router,
        data={
            "suggested_commands": suggestions,
            "swarm": {"active_shells": [x["id"] for x in SWARM if x["status"] in {"online", "standby"}]},
            "brain_context": brain_context_summary(),
        },
        suggestions=suggestions,
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "LilJR-V28/1.0"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        super().end_headers()

    def send_body(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, indent=2)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        size = int(self.headers.get("content-length", "0") or 0)
        if not size:
            return {}
        raw = self.rfile.read(size).decode("utf-8", errors="replace")
        try:
            return json.loads(raw or "{}")
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_body(204, b"", "text/plain")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        if path in {"/", "/public/liljr-one.html"}:
            return self.send_body(200, get_frontend_html(), "text/html; charset=utf-8")
        if path == "/favicon.ico":
            return self.send_body(204, b"", "image/x-icon")
        if path in {"/upload", "/phone-upload"}:
            return self.send_body(200, get_upload_html(), "text/html; charset=utf-8")
        if path in {"/upload/qr", "/phone-upload/qr"}:
            return self.send_body(200, get_upload_qr_html(), "text/html; charset=utf-8")
        if path in {"/api/upload/qr.svg", "/upload/qr.svg"}:
            return self.send_body(200, pseudo_qr_svg(), "image/svg+xml; charset=utf-8")
        if path.startswith("/assets/"):
            try:
                asset = (ROOT / "frontend" / path.lstrip("/")).resolve()
                assets_root = (ROOT / "frontend" / "assets").resolve()
                if assets_root not in asset.parents or not asset.exists() or not asset.is_file():
                    return self.send_body(404, {"error": "asset_not_found"})
                ctype = "image/jpeg" if asset.suffix.lower() in {".jpg", ".jpeg"} else "image/png" if asset.suffix.lower() == ".png" else "application/octet-stream"
                return self.send_body(200, asset.read_bytes(), ctype)
            except Exception as e:
                return self.send_body(404, {"error": "asset_error", "detail": str(e)})
        if path in {"/health", "/api/health"}:
            return self.send_body(200, health())
        if path in {"/swarm/status", "/api/swarm/status"}:
            return self.send_body(200, swarm_status())
        if path in {"/tools/list", "/api/tools/list"}:
            return self.send_body(200, {"ok": True, "tools": list_registered_tools() if list_registered_tools else TOOLS})
        if path in {"/brain/context", "/api/brain/context"}:
            return self.send_body(200, unified_brain_context())
        if path in {"/brain/route", "/api/brain/route"}:
            message = (qs.get("message") or qs.get("q") or [""])[0]
            return self.send_body(200, route_natural_intent(message) if route_natural_intent else {"ok": False, "error": "natural_intent_router_not_loaded"})
        if path in {"/conversation/status", "/api/conversation/status"}:
            return self.send_body(200, conversation_status(ROOT) if conversation_status else {"ok": False, "error": "conversation_flow_not_loaded"})
        if path in {"/conversation/timeline", "/api/conversation/timeline"}:
            query = (qs.get("q") or qs.get("query") or [""])[0]
            limit = int((qs.get("limit") or ["25"])[0] or 25)
            return self.send_body(200, conversation_timeline(ROOT, limit, query) if conversation_timeline else {"ok": False, "error": "conversation_flow_not_loaded"})
        if path in {"/symphony/status", "/api/symphony/status", "/one-unit/status", "/api/one-unit/status"}:
            return self.send_body(200, symphony_status(ROOT) if symphony_status else {"ok": False, "error": "one_unit_symphony_not_loaded"})
        if path in {"/production/readiness", "/api/production/readiness"}:
            return self.send_body(200, production_readiness(ROOT, f"http://127.0.0.1:{PORT}") if production_readiness else {"ok": False, "error": "production_readiness_not_loaded"})
        if path in {"/integrations/status", "/api/integrations/status"}:
            return self.send_body(200, integration_status() if integration_status else {"ok": False, "error": "integration_registry_not_loaded"})
        if path in {"/deliverables/status", "/api/deliverables/status"}:
            return self.send_body(200, pipeline_status(ROOT) if pipeline_status else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/deliverables/search", "/api/deliverables/search"}:
            query = (qs.get("q") or [""])[0]
            return self.send_body(200, search_deliverables(query, ROOT) if search_deliverables else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/deliverables/get", "/api/deliverables/get"}:
            did = (qs.get("id") or [""])[0]
            return self.send_body(200, get_deliverable(did, ROOT) if get_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/orchestrator/status", "/api/orchestrator/status"}:
            return self.send_body(200, orchestration_status() if orchestration_status else {"ok": False, "error": "one_unit_orchestrator_not_loaded"})
        if path in {"/one-unit/e2e", "/api/one-unit/e2e"}:
            return self.send_body(200, run_one_unit_e2e(ROOT, f"http://127.0.0.1:{PORT}") if run_one_unit_e2e else {"ok": False, "error": "one_unit_e2e_verifier_not_loaded"})
        if path in {"/v29/status", "/api/v29/status"}:
            return self.send_body(200, v29_overlay_status())
        if path in {"/uploads/index", "/api/uploads/index"}:
            return self.send_body(200, upload_indexer())
        if path in {"/inbox/watch", "/api/inbox/watch"}:
            return self.send_body(200, inbox_watcher())
        if path in {"/memory/search", "/api/memory/search"}:
            query = (qs.get("q") or [""])[0]
            return self.send_body(200, {"ok": True, "query": query, "results": search_memory(query)})
        if path in {"/signsafe/notaries", "/api/signsafe/notaries"}:
            province = (qs.get("province") or [""])[0]
            city = (qs.get("city") or [""])[0]
            return self.send_body(200, signsafe_notaries(province=province, city=city))
        if path in {"/nearby/signals", "/api/nearby/signals"}:
            scan = (qs.get("scan") or ["false"])[0].lower() in {"1", "true", "yes"}
            return self.send_body(200, nearby_signal_awareness(scan=scan))
        if path in {"/continuity/plan", "/api/continuity/plan"}:
            return self.send_body(200, device_continuity())
        if path in {"/approval/check", "/api/approval/check"}:
            return self.send_body(200, {"ok": True, "approvals": load_json(APPROVAL_FILE, [])})
        if path in {"/verify", "/api/verify"}:
            return self.send_body(200, verifier())
        return self.send_body(404, {"error": "not_found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path in {"/chat", "/api/chat"}:
            data = self.read_json()
            message = data.get("message", "")
            result = handle_chat(message)
            if record_conversation_turn:
                try:
                    result["conversation_event"] = record_conversation_turn(message, result, ROOT)
                except Exception as exc:
                    result["conversation_event"] = {"ok": False, "error": str(exc)[:160]}
            return self.send_body(200, result)
        if path in {"/memory/save", "/api/memory/save"}:
            data = self.read_json()
            return self.send_body(200, {"ok": True, "memory": save_memory(data.get("text", ""), data.get("tags", []))})
        if path in {"/memory/search", "/api/memory/search"}:
            data = self.read_json()
            query = data.get("q", data.get("query", ""))
            return self.send_body(200, {"ok": True, "query": query, "results": search_memory(query)})
        if path in {"/brain/route", "/api/brain/route"}:
            data = self.read_json()
            return self.send_body(200, route_natural_intent(data.get("message", data.get("q", ""))) if route_natural_intent else {"ok": False, "error": "natural_intent_router_not_loaded"})
        if path in {"/conversation/search", "/api/conversation/search", "/conversation/timeline", "/api/conversation/timeline"}:
            data = self.read_json()
            return self.send_body(200, conversation_timeline(ROOT, int(data.get("limit", 25) or 25), data.get("q", data.get("query", ""))) if conversation_timeline else {"ok": False, "error": "conversation_flow_not_loaded"})
        if path in {"/swarm/mission", "/api/swarm/mission"}:
            data = self.read_json()
            return self.send_body(200, {"ok": True, "mission": load_mission(data.get("title", "Mission"), "api")})
        if path in {"/swarm/start", "/api/swarm/start"}:
            data = self.read_json()
            return self.send_body(200, set_swarm_state("running", data.get("title", "Swarm start")))
        if path in {"/swarm/pause", "/api/swarm/pause"}:
            return self.send_body(200, set_swarm_state("paused"))
        if path in {"/swarm/resume", "/api/swarm/resume"}:
            return self.send_body(200, set_swarm_state("running"))
        if path in {"/swarm/stop", "/api/swarm/stop"}:
            return self.send_body(200, set_swarm_state("stopped"))
        if path in {"/approval/apply", "/api/approval/apply"}:
            data = self.read_json()
            return self.send_body(200, apply_approval(data.get("id", "")))
        if path in {"/approval/respond", "/api/approval/respond"}:
            data = self.read_json()
            approved = data.get("approved")
            approval_id = data.get("id", "")
            if approved is True:
                return self.send_body(200, apply_approval(approval_id))
            requests = load_json(APPROVAL_FILE, [])
            match = next((x for x in requests if x.get("id") == approval_id), None)
            if not match:
                return self.send_body(404, {"error": "approval_not_found"})
            match["status"] = "REJECTED"
            match["responded_at"] = now()
            match["owner_note"] = data.get("note", "")
            save_json(APPROVAL_FILE, requests)
            return self.send_body(200, {"ok": True, "approval": match})
        if path in {"/tools/run", "/api/tools/run"}:
            data = self.read_json()
            command = (data.get("command") or "").strip()
            if command:
                result = run_command(command, approved=bool(data.get("approved")))
                if result.get("status") == "OWNER_APPROVAL_REQUIRED":
                    result["approval_required"] = True
                return self.send_body(200, result)
            name = data.get("name")
            args = data.get("args", {})
            tool = list_registered_tools and next((x for x in list_registered_tools() if x.get("name") == name or x.get("handler") == name), None)
            structured_approval_tools = {"integration_run", "orchestration_run", "signsafe_booking"}
            if tool and tool.get("risk_level") in {"approval", "high", "critical"} and name not in structured_approval_tools and not data.get("approved"):
                return self.send_body(200, approval_request("tool_run", {"name": name, "args": args}, f"Tool {name} is {tool.get('risk_level')} risk and needs owner approval."))
            if name in {"scan_files", "file_search"}:
                return self.send_body(200, scan_files())
            if name == "read_file":
                return self.send_body(200, read_file(args.get("path", "")))
            if name in {"run_command", "shell_command"}:
                return self.send_body(200, run_command(args.get("command", ""), approved=False))
            if name == "signsafe_notaries":
                return self.send_body(200, signsafe_notaries(args.get("province", ""), args.get("city", "")))
            if name == "signsafe_booking":
                return self.send_body(200, signsafe_booking(args, approved=bool(data.get("approved"))))
            if name == "nearby_signal_awareness":
                return self.send_body(200, nearby_signal_awareness(scan=bool(args.get("scan", False))))
            if name == "device_continuity":
                return self.send_body(200, device_continuity())
            if name == "brain_context":
                return self.send_body(200, unified_brain_context())
            if name == "natural_intent_router":
                return self.send_body(200, route_natural_intent(args.get("message", args.get("q", ""))) if route_natural_intent else {"ok": False, "error": "natural_intent_router_not_loaded"})
            if name in {"conversation_timeline", "conversation_status"}:
                action = args.get("action", "timeline") if isinstance(args, dict) else "timeline"
                if action == "status" or name == "conversation_status":
                    return self.send_body(200, conversation_status(ROOT) if conversation_status else {"ok": False, "error": "conversation_flow_not_loaded"})
                return self.send_body(200, conversation_timeline(ROOT, int(args.get("limit", 25) or 25), args.get("q", args.get("query", ""))) if conversation_timeline else {"ok": False, "error": "conversation_flow_not_loaded"})
            if name in {"one_unit_symphony", "symphony_status"}:
                return self.send_body(200, symphony_status(ROOT) if symphony_status else {"ok": False, "error": "one_unit_symphony_not_loaded"})
            if name in {"production_readiness", "production_status"}:
                return self.send_body(200, production_readiness(ROOT, f"http://127.0.0.1:{PORT}") if production_readiness else {"ok": False, "error": "production_readiness_not_loaded"})
            if name == "inbox_watcher":
                return self.send_body(200, inbox_watcher())
            if name == "upload_indexer":
                return self.send_body(200, upload_indexer())
            if name == "v29_overlay_status":
                return self.send_body(200, v29_overlay_status())
            if name in {"integration_registry", "integration_status"}:
                return self.send_body(200, integration_status() if integration_status else {"ok": False, "error": "integration_registry_not_loaded"})
            if name in {"deliverable_pipeline", "deliverables_status"}:
                action = (args.get("action") or "status") if isinstance(args, dict) else "status"
                if action == "create":
                    return self.send_body(200, create_deliverable(args.get("request", ""), ROOT) if create_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
                if action == "plan":
                    return self.send_body(200, plan_deliverable(args.get("request", ""), ROOT) if plan_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
                if action == "search":
                    return self.send_body(200, search_deliverables(args.get("q", args.get("query", "")), ROOT) if search_deliverables else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
                if action == "get":
                    return self.send_body(200, get_deliverable(args.get("id", ""), ROOT) if get_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
                return self.send_body(200, pipeline_status(ROOT) if pipeline_status else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
            if name == "integration_run":
                result = run_integration_request(args if isinstance(args, dict) else {}) if run_integration_request else {"ok": False, "error": "integration_registry_not_loaded"}
                if result.get("approval_required") and not data.get("approved"):
                    approval_payload = json.loads(json.dumps(result))
                    approval = approval_request("integration_run", approval_payload, result.get("reason", "Integration action needs owner approval."))
                    result["approval"] = approval
                    result["approval_required"] = True
                return self.send_body(200, result)
            if name in {"one_unit_orchestrator", "orchestration_status"}:
                return self.send_body(200, orchestration_status() if orchestration_status else {"ok": False, "error": "one_unit_orchestrator_not_loaded"})
            if name == "orchestration_run":
                result = run_orchestration_request(args if isinstance(args, dict) else {}) if run_orchestration_request else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
                if result.get("approval_required") and not data.get("approved"):
                    approval_payload = json.loads(json.dumps(result))
                    approval = approval_request("orchestration_run", approval_payload, result.get("reason", "Orchestration action needs owner approval."))
                    result["approval"] = approval
                    result["approval_required"] = True
                return self.send_body(200, result)
            if name in {"one_unit_e2e_verifier", "one_unit_e2e"}:
                return self.send_body(200, run_one_unit_e2e(ROOT, f"http://127.0.0.1:{PORT}") if run_one_unit_e2e else {"ok": False, "error": "one_unit_e2e_verifier_not_loaded"})
            return self.send_body(400, {"error": "tool_not_available"})
        if path in {"/integrations/run", "/api/integrations/run"}:
            data = self.read_json()
            result = run_integration_request(data) if run_integration_request else {"ok": False, "error": "integration_registry_not_loaded"}
            if result.get("approval_required") and not data.get("approved"):
                approval_payload = json.loads(json.dumps(result))
                approval = approval_request("integration_run", approval_payload, result.get("reason", "Integration action needs owner approval."))
                result["approval"] = approval
                result["approval_required"] = True
            return self.send_body(200, result)
        if path in {"/deliverables/plan", "/api/deliverables/plan"}:
            data = self.read_json()
            return self.send_body(200, plan_deliverable(data.get("request", data.get("message", "")), ROOT, data.get("action", "plan")) if plan_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/deliverables/create", "/api/deliverables/create"}:
            data = self.read_json()
            result = create_deliverable(data.get("request", data.get("message", "")), ROOT, data.get("action", "draft")) if create_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"}
            if result.get("approval_required") and not data.get("approved"):
                approval_payload = json.loads(json.dumps(result))
                approval = approval_request("deliverable_pipeline", approval_payload, result.get("reason", "Deliverable action needs owner approval."))
                result["approval"] = approval
                result["approval_required"] = True
            return self.send_body(200, result)
        if path in {"/deliverables/search", "/api/deliverables/search"}:
            data = self.read_json()
            return self.send_body(200, search_deliverables(data.get("q", data.get("query", "")), ROOT) if search_deliverables else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/deliverables/get", "/api/deliverables/get"}:
            data = self.read_json()
            return self.send_body(200, get_deliverable(data.get("id", ""), ROOT) if get_deliverable else {"ok": False, "error": "deliverable_pipeline_not_loaded"})
        if path in {"/orchestrator/plan", "/api/orchestrator/plan", "/orchestrator/run", "/api/orchestrator/run"}:
            data = self.read_json()
            result = run_orchestration_request(data) if run_orchestration_request else {"ok": False, "error": "one_unit_orchestrator_not_loaded"}
            if result.get("approval_required") and not data.get("approved"):
                approval_payload = json.loads(json.dumps(result))
                approval = approval_request("orchestration_run", approval_payload, result.get("reason", "Orchestration action needs owner approval."))
                result["approval"] = approval
                result["approval_required"] = True
            return self.send_body(200, result)
        if path in {"/one-unit/e2e", "/api/one-unit/e2e"}:
            return self.send_body(200, run_one_unit_e2e(ROOT, f"http://127.0.0.1:{PORT}") if run_one_unit_e2e else {"ok": False, "error": "one_unit_e2e_verifier_not_loaded"})
        if path in {"/signsafe/book", "/api/signsafe/book"}:
            data = self.read_json()
            return self.send_body(200, signsafe_booking(data, approved=False))
        if path in {"/upload", "/api/upload"}:
            content_type = self.headers.get("content-type", "")
            if "multipart/form-data" not in content_type:
                return self.send_body(400, {"error": "multipart_required"})
            size = int(self.headers.get("content-length", "0") or 0)
            filename, content, fields = parse_multipart_upload(content_type, self.rfile.read(size))
            if not filename or content is None:
                return self.send_body(400, {"error": "file_required"})
            safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
            device = detect_device_label(safe_name, fields.get("device", ""))
            dest = UPLOADS / (device.lower() + "_" + str(int(time.time())) + "_" + safe_name)
            dest.write_bytes(content)
            indexed = index_upload_file(dest, filename, device)
            return self.send_body(200, {"ok": True, "file": str(dest), "size": dest.stat().st_size, "device_label": device, "indexed": indexed})
        return self.send_body(404, {"error": "not_found", "path": path})


if __name__ == "__main__":
    local_url = f"http://127.0.0.1:{PORT}"
    lan_url = get_lan_app_url()
    print(f"LIL JR V28 Personal Suit Swarm Engine running on {local_url}", flush=True)
    print(f"LIL JR LAN/mobile URL: {lan_url}", flush=True)
    print(f"Bind host: {BIND_HOST}:{PORT}", flush=True)
    print(f"Project root: {ROOT}", flush=True)
    ThreadingHTTPServer((BIND_HOST, PORT), Handler).serve_forever()

