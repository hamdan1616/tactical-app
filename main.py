from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import Optional
import os
import random
import base64

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
    name = Column(String)
    email = Column(String)
    mobile = Column(String)
    badge_number = Column(String, unique=True, index=True)
    profile_photo = Column(String, nullable=True) # Base64 profile photo representation
    status = Column(String, default="ACTIVE")     # 'ACTIVE' or 'PENDING APPROVAL'

class Blockade(Base):
    __tablename__ = "blockades"
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    severity = Column(String)
    status = Column(String, default="ACTIVE")     # ACTIVE, ASSIGNED, ARRIVED, RESOLVED
    notes = Column(String, nullable=True)
    image_url = Column(String, nullable=True)       # AI Hazard snapshot or Base64 URI
    clearance_photo = Column(String, nullable=True) # Live officer clearance photo
    resolved_by = Column(String, nullable=True)     # Badge ID of officer who cleared it
    officer_lat = Column(Float, nullable=True)      # Live tracking telemetry latitude
    officer_lng = Column(Float, nullable=True)      # Live tracking telemetry longitude

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    image_thumb = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="நான்காம் காவல் நண்பன் | Naangham Kaaval Nanban - TN Police", version="32.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
EDGE_API_KEY = "BLU-GUARD-2026"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterRequest(BaseModel):
    name: str
    email: str
    mobile: str
    badge_number: str
    password: str

class EdgeModelTrigger(BaseModel):
    api_key: str
    location_name: str
    latitude: float
    longitude: float
    severity: str = "CRITICAL"
    notes: str
    image_base64: Optional[str] = None

class TelemetryUpdate(BaseModel):
    latitude: float
    longitude: float

@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "TN-ADMIN-01").first():
        db.add(User(
            username="TN-ADMIN-01",
            password="Admin@123",
            name="Central Command Admin",
            email="admin@tnpolice.gov.in",
            mobile="9999999999",
            badge_number="TN-ADMIN-01",
            status="ACTIVE"
        ))
    if not db.query(User).filter(User.username == "test1").first():
        db.add(User(
            username="test1",
            password="password",
            name="Inspector Test Officer",
            email="tnpolice007@tn.gov.in",
            mobile="9876543210",
            badge_number="TN-POLICE-007",
            status="ACTIVE"
        ))
    
    # Ensure there is always at least one active hazard
    if db.query(Blockade).filter(Blockade.status == "ACTIVE").count() == 0 and db.query(Blockade).count() == 0:
        db.add(Blockade(
            location_name="Kumbakonam Bypass Junction - Sector 2",
            latitude=10.9601,
            longitude=79.3845,
            severity="CRITICAL",
            status="ACTIVE",
            notes="Multi-vehicle collision blocking north lane",
            image_url="https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=400&q=80"
        ))
    db.commit()
    db.close()

@app.get("/logo.png", include_in_schema=False)
def get_logo():
    if os.path.exists("logo.png"):
        return FileResponse("logo.png")
    raise HTTPException(status_code=404, detail="Logo not found")

@app.get("/", response_class=HTMLResponse, tags=["Frontend UI"])
def serve_frontend():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>நான்காம் காவல் நண்பன் | Naangham Kaaval Nanban - Tamil Nadu Police</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            .leaflet-layer, .leaflet-control-zoom-in, .leaflet-control-zoom-out, .leaflet-control-attribution {
                filter: invert(100%) hue-rotate(190deg) brightness(95%) contrast(92%);
            }
            .leaflet-container { background: #070d19; }
            .tn-police-stripe {
                background: linear-gradient(90deg, #b91c1c 0%, #b91c1c 50%, #1e3a8a 50%, #1e3a8a 100%);
            }
            .gold-glow { box-shadow: 0 0 35px rgba(217, 119, 6, 0.35); }
        </style>
    </head>
    <body class="bg-[#081021] text-slate-100 min-h-screen font-sans overflow-y-auto">

        <div class="h-1.5 w-full tn-police-stripe"></div>

        <!-- LOGIN / REGISTER MODAL -->
        <div id="login-modal" class="fixed inset-0 bg-[#050b16]/92 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div class="bg-[#0d182e] border-2 border-amber-500/40 rounded-2xl w-full max-w-md p-7 gold-glow relative overflow-hidden">
                <div class="absolute top-0 left-0 right-0 h-1.5 tn-police-stripe"></div>

                <div class="text-center mb-5">
                    <div class="inline-flex items-center justify-center w-28 h-28 mb-2 rounded-full bg-[#070e1c] border-2 border-amber-400 p-1 shadow-2xl relative overflow-hidden">
                        <img src="/logo.png" alt="TN Police Logo" class="w-full h-full object-contain rounded-full">
                    </div>
                    <div class="text-[11px] font-bold uppercase tracking-widest text-amber-400">தமிழ்நாடு காவல்துறை • Tamil Nadu Police</div>
                    <h1 class="text-xl font-extrabold tracking-tight text-white mt-0.5">நான்காம் காவல் நண்பன்</h1>
                    <p class="text-xs font-semibold text-amber-300/90">NAANGHAM KAAVAL NANBAN</p>
                </div>

                <div class="grid grid-cols-2 gap-1 bg-[#070e1c] p-1 rounded-xl mb-5 border border-amber-500/20">
                    <button onclick="switchTab('login')" id="tab-login" class="py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer">Officer Login</button>
                    <button onclick="switchTab('register')" id="tab-register" class="py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer">New Registration</button>
                </div>

                <form id="form-login" onsubmit="handleLogin(event)" class="space-y-3.5">
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Badge ID / Username</label>
                        <input type="text" id="login-username" required placeholder="Enter Badge ID (e.g. TN-ADMIN-01)" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Password</label>
                        <input type="password" id="login-password" required placeholder="Enter Password" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-red-700 to-blue-800 hover:from-red-600 hover:to-blue-700 border border-amber-400/50 text-white font-bold py-2.5 rounded-lg transition text-sm cursor-pointer shadow-md">
                        <i class="fa-solid fa-shield-halved mr-1 text-amber-300"></i> Secure Login
                    </button>
                    <div id="login-error" class="text-center text-xs text-red-400 hidden"></div>
                </form>

                <div id="form-register" class="hidden space-y-3">
                    <div id="reg-step-1" class="space-y-3">
                        <div>
                            <label class="block text-[11px] font-semibold text-amber-400 uppercase mb-0.5">Officer Full Name</label>
                            <input type="text" id="reg-name" placeholder="e.g. Inspector K. Murugan" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3 py-1.5 text-xs text-white">
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <label class="block text-[11px] font-semibold text-amber-400 uppercase mb-0.5">Badge ID</label>
                                <input type="text" id="reg-badge" placeholder="TN-POLICE-99" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3 py-1.5 text-xs text-white">
                            </div>
                            <div>
                                <label class="block text-[11px] font-semibold text-amber-400 uppercase mb-0.5">Mobile Number</label>
                                <input type="tel" id="reg-mobile" placeholder="9876543210" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3 py-1.5 text-xs text-white">
                            </div>
                        </div>
                        <div>
                            <label class="block text-[11px] font-semibold text-amber-400 uppercase mb-0.5">Official Email</label>
                            <input type="email" id="reg-email" placeholder="officer@tn.gov.in" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3 py-1.5 text-xs text-white">
                        </div>
                        <div>
                            <label class="block text-[11px] font-semibold text-amber-400 uppercase mb-0.5">Set Password</label>
                            <input type="password" id="reg-password" placeholder="••••••••" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3 py-1.5 text-xs text-white">
                        </div>
                        <button onclick="requestOTP()" class="w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-2 rounded-lg transition text-xs cursor-pointer shadow">
                            <i class="fa-solid fa-paper-plane mr-1"></i> Send Verification OTP (Mail/SMS)
                        </button>
                    </div>

                    <div id="reg-step-2" class="hidden space-y-3">
                        <div class="bg-blue-950/40 border border-blue-500/30 p-2.5 rounded-lg text-center">
                            <p class="text-xs text-blue-300">OTP dispatched to registered mobile & email.</p>
                            <p id="otp-hint" class="text-[11px] text-amber-400 font-mono mt-1 font-bold"></p>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-amber-400 uppercase mb-1 text-center">Enter 6-Digit OTP Code</label>
                            <input type="text" id="reg-otp" maxlength="6" placeholder="123456" class="w-full text-center tracking-widest font-mono bg-[#070e1c] border border-amber-500/50 rounded-lg px-3 py-2 text-base text-amber-300">
                        </div>
                        <button onclick="verifyAndRegister()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-lg transition text-xs cursor-pointer shadow">
                            <i class="fa-solid fa-check-circle mr-1"></i> Verify OTP & Create Account
                        </button>
                    </div>
                    <div id="reg-error" class="text-center text-xs text-red-400 hidden"></div>
                </div>
            </div>
        </div>

        <!-- DASHBOARD -->
        <div id="dashboard" class="hidden flex flex-col min-h-screen">
            <header class="bg-[#0d182e] border-b-2 border-amber-500/40 px-6 py-2.5 flex justify-between items-center shadow-md">
                <div class="flex items-center space-x-3.5">
                    <img src="/logo.png" class="w-10 h-10 object-contain rounded-full border border-amber-500/40 bg-slate-900" alt="Emblem">
                    <div>
                        <div class="flex items-center space-x-2">
                            <h2 class="font-extrabold text-base tracking-wide text-white">நான்காம் காவல் நண்பன்</h2>
                            <span class="text-xs font-bold text-amber-300 bg-amber-500/15 border border-amber-400/30 px-2 py-0.5 rounded">COMMAND CENTER</span>
                            <span id="grid-status-badge" class="text-[11px] font-semibold px-2 py-0.5 rounded flex items-center gap-1">
                                <span id="grid-dot" class="w-2 h-2 rounded-full"></span> <span id="grid-text">CONNECTING...</span>
                            </span>
                        </div>
                        <p class="text-[11px] text-slate-400">Tamil Nadu Police Integrated Tactical Command • सत्यमेव जयते</p>
                    </div>
                </div>

                <div class="flex items-center space-x-3">
                    <button onclick="resetDatabase()" class="bg-blue-700/30 hover:bg-blue-700/50 border border-blue-400/40 text-blue-300 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1.5">
                        <i class="fa-solid fa-rotate-right"></i> Reset & Spawn Active
                    </button>
                    <button onclick="simulateAITrigger()" class="bg-red-700/30 hover:bg-red-700/50 border border-amber-400/40 text-amber-300 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1.5">
                        <i class="fa-solid fa-satellite-dish text-red-400"></i> Simulate AI Hazard
                    </button>
                    <a href="/docs" target="_blank" class="text-xs text-amber-400 hover:underline px-2 font-medium">API /docs ↗</a>
                    
                    <div class="relative">
                        <button onclick="toggleProfileMenu()" class="bg-slate-800 hover:bg-slate-700 border border-amber-500/40 text-amber-300 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-2">
                            <i class="fa-solid fa-user-shield"></i> <span id="user-badge">Officer</span> <i class="fa-solid fa-caret-down text-[10px]"></i>
                        </button>
                        <div id="profile-dropdown" class="hidden absolute right-0 mt-2 w-48 bg-[#0d182e] border border-amber-500/40 rounded-xl shadow-2xl z-50 overflow-hidden py-1">
                            <button onclick="openProfileModal()" class="w-full text-left px-4 py-2.5 text-xs text-slate-200 hover:bg-amber-500/20 hover:text-amber-300 transition flex items-center gap-2 cursor-pointer">
                                <i class="fa-solid fa-id-card text-amber-400"></i> View & Edit Profile
                            </button>
                            <button onclick="openClearancesModal()" class="w-full text-left px-4 py-2.5 text-xs text-slate-200 hover:bg-amber-500/20 hover:text-amber-300 transition flex items-center gap-2 cursor-pointer">
                                <i class="fa-solid fa-clipboard-check text-emerald-400"></i> My Clearances
                            </button>
                            <div class="border-t border-slate-700 my-1"></div>
                            <button onclick="logout()" class="w-full text-left px-4 py-2.5 text-xs text-red-400 hover:bg-red-950/40 transition flex items-center gap-2 cursor-pointer">
                                <i class="fa-solid fa-right-from-bracket"></i> Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <!-- ADMIN PANEL -->
            <div id="admin-panel" class="hidden bg-[#0d182e] border-b-2 border-amber-500/30 p-4 px-6">
                <div class="flex justify-between items-center mb-3">
                    <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400 flex items-center gap-2">
                        <i class="fa-solid fa-shield-cat text-amber-300"></i> Central Command Supervisor: Officer Approvals & Department Oversight
                    </h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-60 overflow-y-auto">
                    <div class="bg-[#070e1c] border border-amber-500/20 rounded-lg p-3">
                        <h4 class="text-xs font-bold text-slate-300 mb-2">Registered Officer Accounts & Approvals</h4>
                        <div id="admin-officers-list" class="space-y-2 text-xs text-slate-300"></div>
                    </div>
                    <div class="bg-[#070e1c] border border-emerald-500/20 rounded-lg p-3">
                        <h4 class="text-xs font-bold text-emerald-400 mb-2">Verified Department Clearances</h4>
                        <div id="admin-clearances-list" class="space-y-2 text-xs text-slate-300"></div>
                    </div>
                </div>
            </div>

            <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 p-5">
                <div class="lg:col-span-4 bg-[#0d182e] border border-amber-500/30 rounded-xl p-4 flex flex-col space-y-4 shadow-lg">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400">Active Field Incidents</h3>
                        <button onclick="loadBlockades()" class="text-amber-400 hover:text-amber-300 text-xs cursor-pointer"><i class="fa-solid fa-rotate"></i></button>
                    </div>
                    <div id="blockade-list" class="space-y-2.5 pr-1"></div>
                </div>

                <div class="lg:col-span-8 flex flex-col gap-5">
                    <div class="bg-[#0d182e] border border-amber-500/30 rounded-xl p-3 flex flex-col relative min-h-[400px] shadow-lg">
                        <div class="flex justify-between items-center mb-2 px-1">
                            <span class="text-xs font-bold uppercase tracking-wider text-amber-400"><i class="fa-solid fa-map-location-dot text-red-500 mr-1.5"></i>TN Police Geo-Radar Grid (Live Tracking)</span>
                            <div class="flex items-center gap-3 text-[11px]">
                                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span> Hazard</span>
                                <span class="flex items-center gap-1"><i class="fa-solid fa-user-shield text-blue-400"></i> Officer Unit</span>
                            </div>
                        </div>
                        <div id="map" class="w-full h-[400px] rounded-lg border border-amber-500/20 z-10"></div>
                    </div>

                    <div class="bg-[#0d182e] border border-amber-500/30 rounded-xl p-4 flex flex-col shadow-lg">
                        <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400 mb-2"><i class="fa-solid fa-walkie-talkie text-red-400 mr-1.5"></i>TN Police Control Room Wireless Log</h3>
                        <div id="notification-box" class="h-48 bg-[#070e1c] border border-slate-800 rounded-lg p-3 overflow-y-auto space-y-2 font-mono text-xs text-slate-200"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let authToken = localStorage.getItem('token_8002') || '';
            let map, markersLayer;
            let generatedOTP = '';
            let tempRegData = {};

            setInterval(async () => {
                if (authToken && !document.getElementById('dashboard').classList.contains('hidden')) {
                    loadBlockades();
                    loadNotifications();
                    if (authToken.toUpperCase() === 'TN-ADMIN-01') loadAdminPanelData();
                }
            }, 2000);

            async function resetDatabase() {
                await fetch('/blockades/reset-all', { method: 'POST' });
                loadBlockades();
                alert('Database reset! Fresh active incident spawned.');
            }

            function toggleProfileMenu() {
                document.getElementById('profile-dropdown').classList.toggle('hidden');
            }

            function switchTab(tab) {
                const loginTab = document.getElementById('tab-login');
                const regTab = document.getElementById('tab-register');
                const loginForm = document.getElementById('form-login');
                const regForm = document.getElementById('form-register');
                if (tab === 'login') {
                    loginTab.className = 'py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer';
                    regTab.className = 'py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer';
                    loginForm.classList.remove('hidden'); regForm.classList.add('hidden');
                } else {
                    regTab.className = 'py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer';
                    loginTab.className = 'py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer';
                    regForm.classList.remove('hidden'); loginForm.classList.add('hidden');
                }
            }

            async function requestOTP() {
                const name = document.getElementById('reg-name').value;
                const badge = document.getElementById('reg-badge').value;
                const mobile = document.getElementById('reg-mobile').value;
                const email = document.getElementById('reg-email').value;
                const password = document.getElementById('reg-password').value;
                const errDiv = document.getElementById('reg-error');
                if (!name || !badge || !mobile || !email || !password) {
                    errDiv.innerText = 'Fill in all fields.'; errDiv.classList.remove('hidden'); return;
                }
                errDiv.classList.add('hidden');
                tempRegData = { name, badge_number: badge, mobile, email, password };
                generatedOTP = Math.floor(100000 + Math.random() * 900000).toString();
                document.getElementById('reg-step-1').classList.add('hidden');
                document.getElementById('reg-step-2').classList.remove('hidden');
                document.getElementById('otp-hint').innerText = `[SIMULATED OTP]: ${generatedOTP}`;
            }

            async function verifyAndRegister() {
                const otp = document.getElementById('reg-otp').value;
                const errDiv = document.getElementById('reg-error');
                if (otp !== generatedOTP) { errDiv.innerText = 'Invalid OTP.'; errDiv.classList.remove('hidden'); return; }
                const res = await fetch('/auth/register', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(tempRegData)
                });
                if (!res.ok) { errDiv.innerText = 'Registration failed.'; errDiv.classList.remove('hidden'); return; }
                alert('Registered successfully! Awaiting Admin approval.');
                switchTab('login'); document.getElementById('login-username').value = tempRegData.badge_number;
            }

            function initMap() {
                if (map) return;
                map = L.map('map').setView([10.9601, 79.3845], 11);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
                markersLayer = L.layerGroup().addTo(map);
            }

            if (authToken) { showDashboard(); }

            function showDashboard() {
                document.getElementById('login-modal').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                document.getElementById('user-badge').innerText = authToken;
                if (authToken.toUpperCase() === 'TN-ADMIN-01') {
                    document.getElementById('admin-panel').classList.remove('hidden');
                    loadAdminPanelData();
                }
                setTimeout(() => { initMap(); loadBlockades(); loadNotifications(); }, 100);
            }

            async function loadAdminPanelData() {
                try {
                    const offRes = await fetch('/admin/officers', { headers: { 'Authorization': 'Bearer ' + authToken } });
                    if (offRes.ok) {
                        const officers = await offRes.json();
                        const offContainer = document.getElementById('admin-officers-list');
                        offContainer.innerHTML = '';
                        officers.forEach(o => {
                            offContainer.innerHTML += `
                                <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
                                    <div><strong>${o.name}</strong> (${o.badge_number})</div>
                                    <div class="flex items-center gap-2">
                                        <span class="text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-400">${o.status}</span>
                                        ${o.status === 'PENDING APPROVAL' ? `<button onclick="approveOfficer('${o.badge_number}')" class="bg-emerald-600 text-white text-[10px] px-2 py-1 rounded cursor-pointer">Approve</button>` : ''}
                                    </div>
                                </div>`;
                        });
                    }
                } catch (e) { console.error(e); }
            }

            async function approveOfficer(badge) {
                await fetch(`/admin/officers/${badge}/approve`, { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken } });
                loadAdminPanelData();
            }

            async function handleLogin(e) {
                e.preventDefault();
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                const formData = new URLSearchParams({ username, password });
                try {
                    const res = await fetch('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData });
                    if (!res.ok) throw new Error();
                    const data = await res.json();
                    authToken = data.access_token;
                    localStorage.setItem('token_8002', authToken);
                    showDashboard();
                } catch (err) {
                    document.getElementById('login-error').innerText = 'Incorrect credentials.';
                    document.getElementById('login-error').classList.remove('hidden');
                }
            }

            async function simulateAITrigger() {
                await fetch('/blockades/simulate-ai', { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken } });
                loadBlockades(); loadNotifications();
            }

            async function loadBlockades() {
                const res = await fetch('/blockades/');
                const data = await res.json();
                const container = document.getElementById('blockade-list');
                if (!container) return;
                container.innerHTML = '';
                if (markersLayer) markersLayer.clearLayers();

                data.slice().reverse().forEach(b => {
                    const isResolved = b.status === 'RESOLVED';
                    const isAssignedOrArrived = b.status === 'ASSIGNED' || b.status === 'ARRIVED';
                    
                    container.innerHTML += `
                        <div class="bg-[#070e1c] border ${isResolved ? 'border-emerald-500/40' : 'border-amber-500/25'} p-3 rounded-lg space-y-2">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="font-bold text-xs text-white">${b.location_name}</h4>
                                    <p class="text-[11px] text-slate-400">${b.notes || ''}</p>
                                </div>
                                <span class="text-[10px] font-bold px-2 py-0.5 border rounded bg-red-600/25 text-red-300">${b.severity}</span>
                            </div>
                            <div class="flex justify-between items-center pt-1 border-t border-slate-800/80">
                                <span class="text-[11px] text-slate-400">Status: <strong class="${isResolved ? 'text-emerald-400' : 'text-amber-300'}">${b.status}</strong></span>
                                <span class="text-[10px] text-blue-400 font-mono">${isAssignedOrArrived ? 'Unit Dispatched 🛡️' : ''}</span>
                            </div>
                        </div>`;

                    if (markersLayer) {
                        const markerColor = isResolved ? '#10b981' : '#ef4444';
                        markersLayer.addLayer(L.circleMarker([b.latitude, b.longitude], {
                            radius: 10, fillColor: markerColor, color: '#fbbf24', weight: 2, fillOpacity: 0.9
                        }));

                        if (isAssignedOrArrived && b.officer_lat && b.officer_lng) {
                            const officerIcon = L.divIcon({
                                className: 'custom-officer-marker',
                                html: '<div style="background: #1d4ed8; border: 2px solid #fbbf24; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(59,130,246,0.9);"><i class="fa-solid fa-user-shield text-amber-300 text-xs"></i></div>',
                                iconSize: [32, 32], iconAnchor: [16, 16]
                            });
                            markersLayer.addLayer(L.marker([b.officer_lat, b.officer_lng], { icon: officerIcon }));
                        }
                    }
                });
            }

            async function loadNotifications() {
                const res = await fetch('/notifications/', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const data = await res.json();
                const box = document.getElementById('notification-box');
                if (!box) return;
                box.innerHTML = '';
                data.slice().reverse().forEach(n => {
                    box.innerHTML += `<div class="border-b border-slate-800/50 pb-1"><span class="text-amber-400/80">[${new Date(n.created_at).toLocaleTimeString()}]</span> ${n.message}</div>`;
                });
            }

            function logout() { localStorage.removeItem('token_8002'); location.reload(); }
        </script>
    </body>
    </html>
    """

@app.post("/auth/register", tags=["Authentication"])
def register_officer(reg: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.badge_number == reg.badge_number).first()
    if existing: raise HTTPException(status_code=400, detail="Officer already registered.")
    db.add(User(username=reg.badge_number, password=reg.password, name=reg.name, email=reg.email, mobile=reg.mobile, badge_number=reg.badge_number, status="PENDING APPROVAL"))
    db.commit()
    return {"message": "Success"}

@app.post("/auth/request-otp", tags=["Authentication"])
def request_otp(data: dict): return {"message": "OTP dispatched"}

@app.post("/auth/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or user.password != form_data.password: raise HTTPException(status_code=401)
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/admin/officers", tags=["Admin Control"])
def get_admin_officers(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token != "TN-ADMIN-01": raise HTTPException(status_code=403)
    return db.query(User).all()

@app.post("/admin/officers/{badge_number}/approve", tags=["Admin Control"])
def approve_officer(badge_number: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token != "TN-ADMIN-01": raise HTTPException(status_code=403)
    officer = db.query(User).filter(User.badge_number == badge_number).first()
    if not officer: raise HTTPException(status_code=404)
    officer.status = "ACTIVE"
    db.commit()
    return {"message": f"Officer {badge_number} approved"}

@app.get("/api/profile", tags=["Officer Profile"])
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token).first()
    if not user: raise HTTPException(status_code=404)
    return {"name": user.name, "email": user.email, "mobile": user.mobile, "badge_number": user.badge_number, "profile_photo": user.profile_photo, "status": user.status}

@app.put("/api/profile", tags=["Officer Profile"])
async def update_profile(name: str = Form(...), email: str = Form(...), mobile: str = Form(...), password: Optional[str] = Form(None), file: Optional[UploadFile] = File(None), token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token).first()
    if not user: raise HTTPException(status_code=404)
    user.name = name; user.email = email; user.mobile = mobile
    if password: user.password = password
    if file:
        file_bytes = await file.read()
        user.profile_photo = f"data:{file.content_type or 'image/jpeg'};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
    db.commit()
    return {"message": "Profile updated"}

@app.get("/api/my-clearances", tags=["Officer Profile"])
def get_my_clearances(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return db.query(Blockade).filter(Blockade.status == "RESOLVED", Blockade.resolved_by == token).order_by(Blockade.id.desc()).limit(10).all()

@app.head("/blockades/", tags=["Tactical Blockades"])
@app.get("/blockades/", tags=["Tactical Blockades"])
def get_blockades(db: Session = Depends(get_db)): return db.query(Blockade).all()

@app.post("/blockades/reset-all", tags=["Tactical Blockades"])
def reset_all_blockades(db: Session = Depends(get_db)):
    db.query(Blockade).delete()
    db.add(Blockade(
        location_name="Kumbakonam Bypass Junction - Sector 2",
        latitude=10.9601,
        longitude=79.3845,
        severity="CRITICAL",
        status="ACTIVE",
        notes="Multi-vehicle collision blocking north lane",
        image_url="https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=400&q=80"
    ))
    db.commit()
    return {"message": "Database reset successfully. Fresh active incident spawned."}

@app.post("/api-edge-trigger", tags=["Live Project Model Integration"])
def trigger_from_project_model(payload: EdgeModelTrigger, db: Session = Depends(get_db)):
    if payload.api_key != EDGE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Edge API Key")
    
    img_data = payload.image_base64
    if img_data and not img_data.startswith("data:image"):
        img_data = f"data:image/jpeg;base64,{img_data}"

    new_b = Blockade(
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        severity=payload.severity,
        status="ACTIVE",
        notes=payload.notes,
        image_url=img_data
    )
    db.add(new_b)
    db.add(Notification(
        message=f"[YOLO EDGE AI] {payload.notes} @ {payload.location_name}",
        image_thumb=img_data
    ))
    db.commit()
    db.refresh(new_b)
    return {"status": "success", "incident_id": new_b.id}

@app.post("/blockades/simulate-ai", tags=["Edge-AI Simulation"])
def simulate_ai_trigger(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    samples = [
        ("Mahamaham Tank West Gate", 10.9576, 79.3789, "CRITICAL", "YOLO-v8 Edge Cam: Crowd surge & road obstruction detected", "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=400&q=80"),
        ("Mayiladuthurai State Highway", 11.1018, 79.6524, "HIGH", "Acoustic Sensor: Emergency vehicle bottleneck", "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?w=400&q=80")
    ]
    loc, lat, lng, sev, note, img = random.choice(samples)
    new_b = Blockade(location_name=loc, latitude=lat, longitude=lng, severity=sev, status="ACTIVE", notes=note, image_url=img)
    db.add(new_b)
    db.add(Notification(message=f"[EDGE-AI YOLO] {note} @ {loc}", image_thumb=img))
    db.commit()
    return new_b

@app.post("/blockades/{blockade_id}/assign", tags=["Tactical Blockades"])
def assign_blockade(blockade_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b: raise HTTPException(status_code=404)
    b.status = "ASSIGNED"
    b.officer_lat = b.latitude + 0.012
    b.officer_lng = b.longitude + 0.012
    db.add(Notification(message=f"[DISPATCH] Unit assigned to {b.location_name}", image_thumb=b.image_url))
    db.commit()
    return {"status": b.status}

@app.post("/blockades/{blockade_id}/arrived", tags=["Tactical Blockades"])
def mark_arrived(blockade_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b: raise HTTPException(status_code=404)
    b.status = "ARRIVED"
    db.commit()
    return {"status": b.status}

@app.post("/blockades/{blockade_id}/telemetry", tags=["Officer Tracking"])
def update_officer_telemetry(blockade_id: int, data: TelemetryUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b: raise HTTPException(status_code=404)
    b.officer_lat = data.latitude
    b.officer_lng = data.longitude
    db.commit()
    return {"status": "telemetry updated"}

@app.post("/blockades/{blockade_id}/resolve-photo-base64", tags=["Tactical Blockades"])
def resolve_with_photo_base64(blockade_id: int, payload: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    b = db.query(Blockade).filter(Blockade.id == blockade_id).first()
    if not b: raise HTTPException(status_code=404)
    img_data = payload.get("image_data")
    b.status = "RESOLVED"
    b.clearance_photo = img_data
    b.resolved_by = token
    db.add(Notification(message=f"[RESOLVED & VERIFIED] Live camera proof submitted for {b.location_name} by officer {token}", image_thumb=img_data))
    db.commit()
    return {"message": "Resolved via base64 photo"}

@app.delete("/blockades/clear-resolved", tags=["Tactical Blockades"])
def clear_resolved(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    deleted = db.query(Blockade).filter(Blockade.status == "RESOLVED").delete()
    db.commit()
    return {"deleted": deleted}

@app.get("/notifications/", tags=["Notifications"])
def get_notifications(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return db.query(Notification).all()