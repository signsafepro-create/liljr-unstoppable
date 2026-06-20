import os
from dotenv import load_dotenv
load_dotenv()
import json
import urllib.request
import ssl
import sqlite3
import datetime
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Disable SSL for Windows compatibility
ssl._create_default_https_context = ssl._create_unverified_context

class Config:
    NODE_NAME = "Lil.Jr 2.0"
    PORT = 8794
    MASTER_KEY = os.getenv("MASTER_KEY")
    MATRIX_DB = "liljr_neural_matrix.db"
    # VERIFIED KEYS
    GROQ_KEY = os.getenv("GROQ_KEY")
    GEMINI_KEY = os.getenv("GEMINI_KEY")

# --- NEURAL ENGINE (DUAL-BRAIN) ---
def call_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": "You are Jarvis, a sophisticated AI operating within the X-Sovereign Civilization Layer."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.2
    }).encode()
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {Config.GROQ_KEY}'}
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())['choices'][0]['message']['content']

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_KEY}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())['candidates'][0]['content']['parts'][0]['text']

def neural_link(prompt):
    try:
        return call_groq(prompt)
    except:
        try:
            return call_gemini(prompt)
        except Exception as e:
            return f"Neural Link Offline: {e}"

# --- PREMIUM UI (V1000 FORGE) ---
HUD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LIL.JR x X-SOVEREIGN | FORGE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --sov-gold: #E0B35A; --sov-cyan: #27D7FF; --bg: #030712; }
        body { background-color: #030712; color: #F5F3EE; font-family: 'Inter', sans-serif; overflow: hidden; height: 100vh; }
        .font-orbitron { font-family: 'Orbitron', sans-serif; }
        .glass { background: rgba(6, 17, 31, 0.75); backdrop-filter: blur(20px); border: 1px solid rgba(224, 179, 90, 0.15); border-radius: 22px; }
        .active-nav { background: linear-gradient(to right, rgba(44, 33, 16, 0.9), rgba(10, 20, 34, 0.9)); border: 1px solid rgba(243, 200, 107, 0.6); color: #F3C86B; box-shadow: 0 0 20px rgba(243, 200, 107, 0.2); }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .globe-ring { position: absolute; border-radius: 50%; border: 1px solid rgba(39, 215, 255, 0.1); animation: rotate 20s linear infinite; }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .robot-float { animation: float 4s ease-in-out infinite; }
    </style>
</head>
<body class="p-4 flex flex-col gap-4">
    <header class="h-12 glass flex items-center justify-between px-6 border-white/5">
        <div class="text-xs font-bold tracking-widest">LIL.JR 2.0 x X-SOVEREIGN <span class="text-[8px] text-white/40 block uppercase tracking-[0.2em]">Civilization Layer Operating System</span></div>
        <div class="flex items-center gap-6 text-[9px] tracking-[0.2em]">
            <div class="text-green-400 animate-pulse">● SOVEREIGN SESSION ACTIVE</div>
            <div class="w-8 h-8 rounded-full bg-gray-700 border border-sov-gold/30"></div>
        </div>
    </header>

    <div class="grid flex-1 grid-cols-[220px_1fr_430px] gap-4 overflow-hidden">
        <aside class="glass p-4 flex flex-col gap-2">
            <div class="text-[10px] uppercase tracking-[0.2em] text-white/30 mb-4 px-2 font-orbitron">X-Sovereign OS</div>
            <nav class="space-y-1 flex-1 text-[11px] font-medium text-white/40">
                <div class="p-3 active-nav rounded-xl flex justify-between items-center"><span>⊞ Overview</span><span class="text-[8px]">▶</span></div>
                <div class="p-3 hover:text-white cursor-pointer">⚒ Forge</div>
                <div class="p-3 hover:text-white cursor-pointer">🌐 Nations</div>
                <div class="p-3 hover:text-white cursor-pointer">👥 Agents</div>
            </nav>
            <div class="mt-auto p-4 bg-sov-gold/5 border border-sov-gold/10 rounded-2xl text-center">
                <div class="text-[9px] font-bold text-sov-gold uppercase tracking-widest">THE SOVEREIGN CODE</div>
                <p class="text-[8px] text-white/30 italic mt-1">Power in structure. Freedom in design.</p>
            </div>
        </aside>

        <main class="flex flex-col gap-4 overflow-y-auto pr-2">
            <div class="glass h-[130px] p-8 flex items-center justify-between bg-gradient-to-r from-[#0A1A2E] to-black relative overflow-hidden">
                <div class="z-10">
                    <h2 class="text-[32px] tracking-[0.2em] font-light font-orbitron leading-none">CIVILIZATION LAYER</h2>
                    <p class="text-[11px] text-white/50 mt-2 max-w-md leading-relaxed uppercase tracking-widest">Lil.Jr 2.0 Operating System</p>
                </div>
                <div class="relative w-48 h-48 flex items-center justify-center opacity-80">
                    <div class="globe-ring w-full h-full"></div>
                    <div class="text-6xl filter drop-shadow-[0_0_20px_rgba(39,215,255,0.4)]">🌍</div>
                </div>
            </div>

            <div class="glass p-6 flex flex-col gap-4 border-sov-gold/20 h-[450px]">
                <div class="flex justify-between items-center">
                    <h3 class="text-[10px] font-bold uppercase tracking-widest">Neural Link</h3>
                    <span class="text-[8px] text-green-400 font-bold animate-pulse">● ONLINE</span>
                </div>
                <div id="chat" class="flex-1 overflow-y-auto text-[11px] space-y-4 pr-2">
                    <div class="text-white/40 italic">Awaiting directive, Commander.</div>
                </div>
                <div class="flex gap-2">
                    <input type="text" id="cmd" placeholder="Direct Jarvis..." class="flex-1 bg-white/5 border border-white/10 rounded-lg p-3 text-xs outline-none focus:border-sov-gold/50" onkeypress="if(event.key==='Enter') send()">
                    <button onclick="send()" class="bg-sov-gold text-black px-4 rounded-lg font-bold text-[10px] uppercase tracking-widest">Ignite</button>
                </div>
            </div>
        </main>

        <aside class="flex flex-col gap-4">
            <div class="glass p-6">
                <h3 class="text-[11px] font-bold uppercase tracking-widest">Legitimacy Score</h3>
                <div class="text-4xl font-light font-orbitron mt-2">84<span class="text-sm text-white/20">/100</span></div>
                <div class="mt-6 space-y-4">
                    <div class="flex justify-between text-[9px] uppercase text-white/40"><span>Neural Sync</span><span>98</span></div>
                    <div class="h-1 w-full bg-white/5 rounded-full overflow-hidden"><div class="h-full bg-sov-cyan shadow-[0_0_10px_var(--sov-cyan)]" style="width: 98%;"></div></div>
                </div>
            </div>
            <div class="flex-1 flex items-center justify-center robot-float">
                <img src="https://i.imgur.com/7vW6v6v.png" class="w-48 filter drop-shadow-[0_0_30px_rgba(188,19,254,0.5)]">
            </div>
        </aside>
    </div>

    <script>
        const params = new URLSearchParams(window.location.search);
        const KEY = params.get('token');
        function append(who, msg) {
            const c = document.getElementById('chat');
            c.innerHTML += `<div class="mb-2"><b class="text-sov-gold">${who}:</b> ${msg}</div>`;
            c.scrollTop = c.scrollHeight;
        }
        async function send() {
            const i = document.getElementById('cmd'); const v = i.value; if(!v) return;
            i.value = ''; append("USER", v);
            const r = await fetch('/chat?token=' + KEY, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: v})
            });
            const d = await r.json(); append("JARVIS", d.reply);
        }
    </script>
</body>
</html>
"""

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def get_hud(token: str = None):
    if token != Config.MASTER_KEY: return "Access Denied"
    return HUD_HTML

@app.post("/chat")
async def chat(request: Request, token: str = None):
    if token != Config.MASTER_KEY: raise HTTPException(status_code=403)
    data = await request.json()
    reply = neural_link(data.get("message", ""))
    return {"reply": reply}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)
