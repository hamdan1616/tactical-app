from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import Optional
import random

# --- SQLite Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./tactical_8002.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    badge_number = Column(String, unique=True, index=True)

class Blockade(Base):
    __tablename__ = "blockades"
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    severity = Column(String)  # CRITICAL, HIGH, MEDIUM
    status = Column(String, default="ACTIVE")  # ACTIVE, ASSIGNED, RESOLVED
    notes = Column(String, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="நாங்கம் காவல் நண்பன் | Naangham Kaaval Nanban - TN Police Tactical Grid", version="11.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BlockadeCreate(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    severity: str
    status: str = "ACTIVE"
    notes: Optional[str] = None

@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "test1").first():
        db.add(User(username="test1", password="password", badge_number="TN-POLICE-007"))
    if db.query(Blockade).count() == 0:
        db.add(Blockade(
            location_name="Kumbakonam Bypass Junction - Sector 2",
            latitude=10.9601,
            longitude=79.3845,
            severity="CRITICAL",
            status="ACTIVE",
            notes="Multi-vehicle collision blocking north lane"
        ))
        db.add(Blockade(
            location_name="NH-36 Thanjavur Toll Plaza",
            latitude=10.7870,
            longitude=79.1378,
            severity="HIGH",
            status="ACTIVE",
            notes="High-density congestion detected via Edge-AI"
        ))
        db.add(Notification(message="TN POLICE CONTROL ROOM: Naangham Kaaval Nanban Grid Online"))
    db.commit()
    db.close()

@app.get("/", response_class=HTMLResponse, tags=["Frontend UI"])
def serve_frontend():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>நாங்கம் காவல் நண்பன் | Naangham Kaaval Nanban - Tamil Nadu Police</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            .leaflet-layer,
            .leaflet-control-zoom-in,
            .leaflet-control-zoom-out,
            .leaflet-control-attribution {
                filter: invert(100%) hue-rotate(190deg) brightness(95%) contrast(92%);
            }
            .leaflet-container { background: #070d19; }
            .tn-police-stripe {
                background: linear-gradient(90deg, #b91c1c 0%, #b91c1c 50%, #1e3a8a 50%, #1e3a8a 100%);
            }
            .gold-glow {
                box-shadow: 0 0 25px rgba(217, 119, 6, 0.25);
            }
        </style>
    </head>
    <body class="bg-[#081021] text-slate-100 min-h-screen font-sans selection:bg-amber-500 selection:text-slate-950">

        <!-- TOP OFFICIAL TN POLICE RIBBON -->
        <div class="h-1.5 w-full tn-police-stripe"></div>

        <!-- LOGIN MODAL -->
        <div id="login-modal" class="fixed inset-0 bg-[#050b16]/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div class="bg-[#0d182e] border-2 border-amber-500/40 rounded-2xl w-full max-w-md p-8 gold-glow relative overflow-hidden">
                <div class="absolute top-0 left-0 right-0 h-1.5 tn-police-stripe"></div>

                <div class="text-center mb-6">
                    <!-- TAMIL NADU POLICE CREST SVG -->
                    <div class="inline-flex items-center justify-center w-24 h-24 mb-3 relative">
                        <svg viewBox="0 0 120 140" class="w-full h-full drop-shadow-[0_4px_10px_rgba(245,158,11,0.4)]">
                            <!-- Outer Gold Shield -->
                            <path d="M60 5 L110 25 L110 65 C110 100 60 130 60 135 C60 130 10 100 10 65 L10 25 Z" fill="#1e3a8a" stroke="#f59e0b" stroke-width="4"/>
                            <!-- Inner Crimson & Navy Split -->
                            <path d="M60 12 L103 29 L103 65 C103 95 60 122 60 127 Z" fill="#991b1b"/>
                            <path d="M60 12 L17 29 L17 65 C17 95 60 122 60 127 Z" fill="#172554"/>
                            <!-- Gopuram / Lion Pillar Gold Emblem Center -->
                            <polygon points="60,24 72,58 48,58" fill="#fbbf24"/>
                            <rect x="46" y="60" width="28" height="6" rx="2" fill="#f59e0b"/>
                            <circle cx="60" cy="75" r="7" fill="none" stroke="#fbbf24" stroke-width="2.5"/>
                            <!-- Bottom Ribbon -->
                            <path d="M25 102 Q60 116 95 102 L99 112 Q60 126 21 112 Z" fill="#fbbf24"/>
                            <text x="60" y="112" font-size="7.5" font-weight="bold" fill="#0f172a" text-anchor="middle">வாய்மையே வெல்லும்</text>
                        </svg>
                    </div>

                    <div class="text-xs font-bold uppercase tracking-widest text-amber-400 mb-1">தமிழ்நாடு காவல்துறை • Tamil Nadu Police</div>
                    <h1 class="text-2xl font-extrabold tracking-tight text-white">நாங்கம் காவல் நண்பன்</h1>
                    <p class="text-sm font-semibold text-amber-300/90 mt-0.5">NAANGHAM KAAVAL NANBAN</p>
                    <p class="text-xs text-slate-400 mt-1">State Tactical Command & AI Traffic Grid</p>
                </div>

                <form onsubmit="handleLogin(event)" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Officer Badge ID / Username</label>
                        <input type="text" id="username" required value="test1" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Control Room Password</label>
                        <input type="password" id="password" required value="password" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-red-700 via-red-600 to-blue-800 hover:from-red-600 hover:to-blue-700 border border-amber-400/50 text-white font-bold py-2.5 rounded-lg transition text-sm cursor-pointer shadow-lg">
                        <i class="fa-solid fa-unlock-keyhole mr-1.5 text-amber-300"></i> Authenticate & Enter Command Grid
                    </button>
                </form>
                <div id="login-error" class="mt-4 text-center text-sm text-red-400 hidden"></div>
            </div>
        </div>

        <!-- MAIN DASHBOARD -->
        <div id="dashboard" class="hidden flex flex-col h-[calc(100vh-6px)]">
            <header class="bg-[#0d182e] border-b-2 border-amber-500/40 px-6 py-2.5 flex justify-between items-center shadow-md">
                <div class="flex items-center space-x-3.5">
                    <!-- Mini TN Police Crest in Header -->
                    <svg viewBox="0 0 120 140" class="w-11 h-11 shrink-0">
                        <path d="M60 5 L110 25 L110 65 C110 100 60 130 60 135 C60 130 10 100 10 65 L10 25 Z" fill="#1e3a8a" stroke="#f59e0b" stroke-width="6"/>
                        <path d="M60 12 L103 29 L103 65 C103 95 60 122 60 127 Z" fill="#991b1b"/>
                        <path d="M60 12 L17 29 L17 65 C17 95 60 122 60 127 Z" fill="#172554"/>
                        <polygon points="60,26 74,62 46,62" fill="#fbbf24"/>
                        <circle cx="60" cy="78" r="8" fill="#fbbf24"/>
                    </svg>
                    <div>
                        <div class="flex items-center space-x-2">
                            <h2 class="font-extrabold text-lg tracking-wide text-white">நாங்கம் காவல் நண்பன்</h2>
                            <span class="text-xs font-bold text-amber-300 bg-amber-500/15 border border-amber-400/30 px-2 py-0.5 rounded">NAANGHAM KAAVAL NANBAN</span>
                            <span class="text-[11px] text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded flex items-center gap-1">
                                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-ping"></span> TN POLICE GRID LIVE
                            </span>
                        </div>
                        <p class="text-[11px] text-slate-400">Tamil Nadu Police Integrated Tactical & Edge-AI Traffic Command System • सत्यमेव जयते</p>
                    </div>
                </div>

                <div class="flex items-center space-x-3">
                    <button onclick="simulateAITrigger()" class="bg-red-700/30 hover:bg-red-700/50 border border-amber-400/40 text-amber-300 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1.5">
                        <i class="fa-solid fa-satellite-dish text-red-400"></i> Simulate AI Hazard
                    </button>
                    <a href="/docs" target="_blank" class="text-xs text-amber-400 hover:underline px-2 font-medium">API /docs ↗</a>
                    <span id="user-badge" class="text-xs font-semibold text-amber-200 bg-slate-900/90 border border-amber-500/30 px-2.5 py-1 rounded"></span>
                    <button onclick="logout()" class="bg-red-900/40 hover:bg-red-800/60 border border-red-500/30 text-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer">Logout</button>
                </div>
            </header>

            <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 p-5 overflow-hidden">
                <!-- Left Column: Broadcast & Active Checkpoints -->
                <div class="lg:col-span-4 bg-[#0d182e] border border-amber-500/30 rounded-xl p-4 flex flex-col overflow-hidden space-y-4 shadow-lg">
                    <form onsubmit="createBlockade(event)" class="bg-[#070e1c] border border-amber-500/25 p-3.5 rounded-lg space-y-2.5">
                        <div class="flex justify-between items-center">
                            <h4 class="text-xs font-bold uppercase text-amber-400 tracking-wider"><i class="fa-solid fa-bullhorn mr-1 text-red-500"></i>Broadcast Tactical Blockade</h4>
                            <span class="text-[10px] text-slate-400">Click map for Lat/Lng</span>
                        </div>
                        <input type="text" id="loc_name" required placeholder="Checkpost / Location (e.g. Kumbakonam Bus Stand)" class="w-full bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white focus:border-amber-400 focus:outline-none">
                        <div class="grid grid-cols-2 gap-2">
                            <input type="number" step="any" id="lat" required value="10.9601" placeholder="Latitude" class="bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
                            <input type="number" step="any" id="lng" required value="79.3845" placeholder="Longitude" class="bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
                        </div>
                        <input type="text" id="notes" placeholder="Control room directive / patrol notes" class="w-full bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
                        <div class="grid grid-cols-2 gap-2">
                            <select id="severity" class="bg-[#0d182e] border border-slate-700 rounded px-2 py-1.5 text-xs text-amber-300 font-semibold">
                                <option value="CRITICAL">CRITICAL (Red Alert)</option>
                                <option value="HIGH">HIGH (Amber Alert)</option>
                                <option value="MEDIUM">MEDIUM (Patrol Check)</option>
                            </select>
                            <button type="submit" class="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 border border-amber-400/40 text-white text-xs font-bold rounded py-1.5 transition cursor-pointer">
                                + Deploy Alert
                            </button>
                        </div>
                    </form>

                    <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400">Active Police Checkposts & Alerts</h3>
                        <div class="flex items-center space-x-2">
                            <button onclick="clearResolved()" class="text-[11px] text-slate-400 hover:text-red-400 cursor-pointer">Clear Resolved</button>
                            <button onclick="loadBlockades()" class="text-amber-400 hover:text-amber-300 text-xs cursor-pointer"><i class="fa-solid fa-rotate"></i></button>
                        </div>
                    </div>
                    <div id="blockade-list" class="flex-1 overflow-y-auto space-y-2.5 pr-1"></div>
                </div>

                <!-- Right Column: Map & Control Room Wireless Log -->
                <div class="lg:col-span-8 flex flex-col gap-5 overflow-hidden">
                    <div class="flex-1 bg-[#0d182e] border border-amber-500/30 rounded-xl p-3 flex flex-col relative overflow-hidden min-h-[300px] shadow-lg">
                        <div class="flex justify-between items-center mb-2 px-1">
                            <span class="text-xs font-bold uppercase tracking-wider text-amber-400"><i class="fa-solid fa-map-location-dot text-red-500 mr-1.5"></i>Tamil Nadu Police Geo-Radar Grid (Click Map to Select Sector Coordinates)</span>
                            <div class="flex items-center gap-3 text-[11px]">
                                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span> Critical</span>
                                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span> High</span>
                                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> Cleared</span>
                            </div>
                        </div>
                        <div id="map" class="flex-1 rounded-lg border border-amber-500/20 z-10"></div>
                    </div>

                    <div class="h-48 bg-[#0d182e] border border-amber-500/30 rounded-xl p-4 flex flex-col overflow-hidden shadow-lg">
                        <div class="flex justify-between items-center mb-2">
                            <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400"><i class="fa-solid fa-walkie-talkie text-red-400 mr-1.5"></i>TN Police Control Room Wireless & Telemetry Log</h3>
                            <span class="text-[11px] text-amber-300 bg-amber-500/10 border border-amber-400/30 px-2 py-0.5 rounded">100 Emergency Grid Synced</span>
                        </div>
                        <div id="notification-box" class="flex-1 bg-[#070e1c] border border-slate-800 rounded-lg p-3 overflow-y-auto space-y-1.5 font-mono text-xs text-slate-200"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let authToken = localStorage.getItem('token_8002') || '';
            let map, markersLayer;

            function initMap() {
                if (map) return;
                map = L.map('map').setView([10.9601, 79.3845], 10);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap | நாங்கம் காவல் நண்பன் - TN Police'
                }).addTo(map);
                markersLayer = L.layerGroup().addTo(map);

                map.on('click', function(e) {
                    document.getElementById('lat').value = e.latlng.lat.toFixed(4);
                    document.getElementById('lng').value = e.latlng.lng.toFixed(4);
                });
            }

            if (authToken) {
                showDashboard();
            }

            function showDashboard() {
                document.getElementById('login-modal').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                document.getElementById('user-badge').innerText = 'TN-POLICE-007 (Inspector)';
                setTimeout(() => {
                    initMap();
                    loadBlockades();
                    loadNotifications();
                }, 100);
            }

            async function handleLogin(e) {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const formData = new URLSearchParams({ username, password });

                try {
                    const res = await fetch('/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    });
                    if (!res.ok) throw new Error('Invalid credentials');
                    const data = await res.json();
                    authToken = data.access_token;
                    localStorage.setItem('token_8002', authToken);
                    showDashboard();
                } catch (err) {
                    const errDiv = document.getElementById('login-error');
                    errDiv.innerText = 'Incorrect username or password.';
                    errDiv.classList.remove('hidden');
                }
            }

            async function createBlockade(e) {
                e.preventDefault();
                const payload = {
                    location_name: document.getElementById('loc_name').value,
                    latitude: parseFloat(document.getElementById('lat').value),
                    longitude: parseFloat(document.getElementById('lng').value),
                    severity: document.getElementById('severity').value,
                    notes: document.getElementById('notes').value || "TN Police Control Room Directive",
                    status: "ACTIVE"
                };
                await fetch('/blockades/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify(payload)
                });
                document.getElementById('loc_name').value = '';
                document.getElementById('notes').value = '';
                loadBlockades();
                loadNotifications();
            }

            async function simulateAITrigger() {
                await fetch('/blockades/simulate-ai', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                loadBlockades();
                loadNotifications();
            }

            async function loadBlockades() {
                const res = await fetch('/blockades/');
                const data = await res.json();
                const container = document.getElementById('blockade-list');
                container.innerHTML = '';

                if (markersLayer) markersLayer.clearLayers();

                data.forEach(b => {
                    const isResolved = b.status === 'RESOLVED';
                    const badgeColor = b.severity === 'CRITICAL' ? 'bg-red-600/25 text-red-300 border-red-500/40' :
                                       b.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
                                       'bg-blue-600/25 text-blue-300 border-blue-500/40';

                    container.innerHTML += `
                        <div class="bg-[#070e1c] border ${isResolved ? 'border-slate-800/40 opacity-60' : 'border-amber-500/25'} p-3 rounded-lg space-y-2">
                            <div class="flex justify-between items-start">
                                <div onclick="focusMap(${b.latitude}, ${b.longitude})" class="cursor-pointer">
                                    <h4 class="font-bold text-xs text-white hover:text-amber-400 transition">${b.location_name}</h4>
                                    <p class="text-[11px] text-slate-400">${b.notes || ''}</p>
                                </div>
                                <span class="text-[10px] font-bold px-2 py-0.5 border rounded ${badgeColor}">${b.severity}</span>
                            </div>
                            <div class="flex justify-between items-center pt-1 border-t border-slate-800/80">
                                <span class="text-[11px] text-slate-400">Status: <strong class="text-amber-300">${b.status}</strong></span>
                                <div class="space-x-1.5">
                                    ${b.status === 'ACTIVE' ? `<button onclick="assignUnit(${b.id})" class="bg-blue-700/40 hover:bg-blue-700/60 border border-blue-400/30 text-blue-200 text-[11px] px-2.5 py-0.5 rounded transition cursor-pointer">Dispatch Patrol</button>` : ''}
                                    ${b.status !== 'RESOLVED' ? `<button onclick="resolveBlockade(${b.id})" class="bg-emerald-700/30 hover:bg-emerald-700/50 border border-emerald-400/30 text-emerald-300 text-[11px] px-2.5 py-0.5 rounded transition cursor-pointer">Mark Cleared</button>` : ''}
                                </div>
                            </div>
                        </div>`;

                    if (markersLayer && b.latitude && b.longitude) {
                        const markerColor = isResolved ? '#10b981' : (b.severity === 'CRITICAL' ? '#ef4444' : (b.severity === 'HIGH' ? '#f59e0b' : '#3b82f6'));
                        const circle = L.circleMarker([b.latitude, b.longitude], {
                            radius: 9,
                            fillColor: markerColor,
                            color: '#fbbf24',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9
                        }).bindPopup(`<b>${b.location_name}</b><br>Severity: ${b.severity}<br>Status: ${b.status}<br><small>${b.notes || ''}</small>`);
                        markersLayer.addLayer(circle);
                    }
                });
            }

            function focusMap(lat, lng) {
                if (map) map.setView([lat, lng], 14);
            }

            async function loadNotifications() {
                const res = await fetch('/notifications/', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const data = await res.json();
                const box = document.getElementById('notification-box');
                box.innerHTML = '';
                data.slice().reverse().forEach(n => {
                    box.innerHTML += `<div><span class="text-amber-400/80">[${new Date(n.created_at).toLocaleTimeString()}]</span> ${n.message}</div>`;
                });
            }

            async function assignUnit(id) {
                await fetch('/blockades/' + id + '/assign', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                loadBlockades();
                loadNotifications();
            }

            async function resolveBlockade(id) {
                await fetch('/blockades/' + id + '/resolve', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                loadBlockades();
                loadNotifications();
            }

            async function clearResolved() {
                await fetch('/blockades/clear-resolved', {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                loadBlockades();
                loadNotifications();
            }

            function logout() {
                localStorage.removeItem('token_8002');
                location.reload();
            }
        </script>
    </body>
    </html>
    """

@app.post("/auth/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or user.password != form_data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/blockades/", tags=["Tactical Blockades"])
def get_blockades(db: Session = Depends(get_db)):
    return db.query(Blockade).all()

@app.post("/blockades/", tags=["Tactical Blockades"])
def create_blockade(blockade: BlockadeCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    new_b = Blockade(**blockade.model_dump())
    db.add(new_b)
    db.add(Notification(message=f"[TN-POLICE ALERT] {blockade.severity} checkpost active at {blockade.location_name}"))
    db.commit()
    db.refresh(new_b)
    return new_b

@app.post("/blockades/simulate-ai", tags=["Edge-AI Simulation"])
def simulate_ai_trigger(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    samples = [
        ("Mahamaham Tank West Gate", 10.9576, 79.3789, "CRITICAL", "YOLO-v8 Edge Cam: Crowd surge & road obstruction detected"),
        ("Mayiladuthurai State Highway", 11.1018, 79.6524, "HIGH", "AI Acoustic/Flame Sensor: Emergency vehicle bottleneck"),
        ("Trichy-Chennai NH-45 Sector 9", 10.8254, 78.6921, "MEDIUM", "Automated Speed Radar: Sudden traffic halt detected"),
        ("Darasuram Airavatesvara Crossroad", 10.9482, 79.3567, "HIGH", "Edge Crosswalk Node: Pedestrian hazard alert")
    ]
    loc, lat, lng, sev, note = random.choice(samples)
    new_b = Blockade(location_name=loc, latitude=lat, longitude=lng, severity=sev, status="ACTIVE", notes=note)
    db.add(new_b)
    db.add(Notification(message=f"[EDGE-AI WIRELESS] {note} @ {loc}"))
    db.commit()
    return new_b

@app.post("/blockades/{blockade_id}/assign", tags=["Tactical Blockades"])
def assign_blockade(blockade_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Blockade not found")
    b.status = "ASSIGNED"
    db.add(Notification(message=f"[PATROL DISPATCHED] Highway mobile unit assigned to {b.location_name}"))
    db.commit()
    return {"message": "Unit assigned", "status": b.status}

@app.post("/blockades/{blockade_id}/resolve", tags=["Tactical Blockades"])
def resolve_blockade(blockade_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Blockade not found")
    b.status = "RESOLVED"
    db.add(Notification(message=f"[SECTOR CLEARED] Traffic restored at {b.location_name}"))
    db.commit()
    return {"message": "Blockade resolved", "status": b.status}

@app.delete("/blockades/clear-resolved", tags=["Tactical Blockades"])
def clear_resolved(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    deleted = db.query(Blockade).filter(Blockade.status == "RESOLVED").delete()
    db.add(Notification(message=f"[CONTROL LOG] Archived {deleted} cleared checkposts"))
    db.commit()
    return {"deleted": deleted}

@app.get("/notifications/", tags=["Notifications"])
def get_notifications(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return db.query(Notification).all()
