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
    name = Column(String)
    email = Column(String)
    mobile = Column(String)
    badge_number = Column(String, unique=True, index=True)

class Blockade(Base):
    __tablename__ = "blockades"
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    severity = Column(String)
    status = Column(String, default="ACTIVE")
    notes = Column(String, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="நாங்கம் காவல் நண்பன் | Naangham Kaaval Nanban - TN Police", version="13.0")

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

class RegisterRequest(BaseModel):
    name: str
    email: str
    mobile: str
    badge_number: str
    password: str

active_otps = {}

@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "test1").first():
        db.add(User(
            username="test1",
            password="password",
            name="Inspector Test Officer",
            email="tnpolice007@tn.gov.in",
            mobile="9876543210",
            badge_number="TN-POLICE-007"
        ))
    if db.query(Blockade).count() == 0:
        db.add(Blockade(
            location_name="Kumbakonam Bypass Junction - Sector 2",
            latitude=10.9601,
            longitude=79.3845,
            severity="CRITICAL",
            status="ACTIVE",
            notes="Multi-vehicle collision blocking north lane"
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
            .leaflet-layer, .leaflet-control-zoom-in, .leaflet-control-zoom-out, .leaflet-control-attribution {
                filter: invert(100%) hue-rotate(190deg) brightness(95%) contrast(92%);
            }
            .leaflet-container { background: #070d19; }
            .tn-police-stripe {
                background: linear-gradient(90deg, #b91c1c 0%, #b91c1c 50%, #1e3a8a 50%, #1e3a8a 100%);
            }
            .gold-glow {
                box-shadow: 0 0 35px rgba(217, 119, 6, 0.35);
            }
        </style>
    </head>
    <body class="bg-[#081021] text-slate-100 min-h-screen font-sans">

        <!-- TOP POLICE RIBBON -->
        <div class="h-1.5 w-full tn-police-stripe"></div>

        <!-- AUTH MODAL (LOGIN / REGISTER WITH OTP) -->
        <div id="login-modal" class="fixed inset-0 bg-[#050b16]/92 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div class="bg-[#0d182e] border-2 border-amber-500/40 rounded-2xl w-full max-w-md p-7 gold-glow relative overflow-hidden">
                <div class="absolute top-0 left-0 right-0 h-1.5 tn-police-stripe"></div>

                <!-- OFFICIAL TAMIL NADU POLICE CREST -->
                <div class="text-center mb-5">
                    <div class="inline-flex items-center justify-center w-26 h-26 mb-2 rounded-full bg-[#1e3a8a] border-2 border-amber-400 p-1 shadow-2xl relative overflow-hidden">
                        <!-- Precise SVG Recreation of TN Police Emblem matching user uploaded badge -->
                        <svg viewBox="0 0 200 200" class="w-full h-full">
                            <circle cx="100" cy="100" r="96" fill="#172554" stroke="#fbbf24" stroke-width="4"/>
                            <!-- Outer Ring Text Path simulation -->
                            <path id="ring" d="M 30,100 a 70,70 0 1,1 140,0" fill="none"/>
                            <text font-size="14.5" font-weight="bold" fill="#ffffff" letter-spacing="2.5"><textPath href="#ring" startOffset="50%" text-anchor="middle">TAMIL NADU POLICE</textPath></text>
                            <!-- Gopuram Temple Tower Center -->
                            <polygon points="100,50 125,120 75,120" fill="#fbbf24" stroke="#d97706" stroke-width="2"/>
                            <line x1="85" y1="70" x2="115" y2="70" stroke="#172554" stroke-width="2"/>
                            <line x1="80" y1="90" x2="120" y2="90" stroke="#172554" stroke-width="2"/>
                            <line x1="77" y1="110" x2="123" y2="110" stroke="#172554" stroke-width="2"/>
                            <!-- Lion Capital Emblem at Bottom -->
                            <rect x="85" y="125" width="30" height="22" rx="3" fill="#facc15"/>
                            <rect x="75" y="148" width="50" height="14" fill="#ffffff"/>
                            <rect x="80" y="148" width="10" height="14" fill="#ff9933"/>
                            <rect x="110" y="148" width="10" height="14" fill="#138808"/>
                            <!-- Truth Alone Triumphs Ribbon -->
                            <path d="M 40,172 Q 100,192 160,172 L 150,188 Q 100,205 50,188 Z" fill="#b91c1c" stroke="#fbbf24" stroke-width="1.5"/>
                            <text x="100" y="184" font-size="9" font-weight="bold" fill="#ffffff" text-anchor="middle">TRUTH ALONE TRIUMPHS</text>
                        </svg>
                    </div>
                    <div class="text-[11px] font-bold uppercase tracking-widest text-amber-400">தமிழ்நாடு காவல்துறை • Tamil Nadu Police</div>
                    <h1 class="text-xl font-extrabold tracking-tight text-white mt-0.5">நாங்கம் காவல் நண்பன்</h1>
                    <p class="text-xs font-semibold text-amber-300/90">NAANGHAM KAAVAL NANBAN</p>
                </div>

                <!-- TABS -->
                <div class="grid grid-cols-2 gap-1 bg-[#070e1c] p-1 rounded-xl mb-5 border border-amber-500/20">
                    <button onclick="switchTab('login')" id="tab-login" class="py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer">Officer Login</button>
                    <button onclick="switchTab('register')" id="tab-register" class="py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer">New Registration</button>
                </div>

                <!-- LOGIN FORM -->
                <form id="form-login" onsubmit="handleLogin(event)" class="space-y-3.5">
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Badge ID / Username</label>
                        <input type="text" id="login-username" required value="test1" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-amber-400/90 uppercase mb-1">Password</label>
                        <input type="password" id="login-password" required value="password" class="w-full bg-[#070e1c] border border-amber-500/30 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-amber-400">
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-red-700 to-blue-800 hover:from-red-600 hover:to-blue-700 border border-amber-400/50 text-white font-bold py-2.5 rounded-lg transition text-sm cursor-pointer shadow-md">
                        <i class="fa-solid fa-shield-halved mr-1 text-amber-300"></i> Secure Login
                    </button>
                    <div id="login-error" class="text-center text-xs text-red-400 hidden"></div>
                </form>

                <!-- REGISTRATION FORM -->
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
        <div id="dashboard" class="hidden flex flex-col h-[calc(100vh-6px)]">
            <header class="bg-[#0d182e] border-b-2 border-amber-500/40 px-6 py-2.5 flex justify-between items-center shadow-md">
                <div class="flex items-center space-x-3.5">
                    <div class="w-10 h-10 rounded-full bg-[#1e3a8a] border border-amber-400 flex items-center justify-center p-0.5 shrink-0">
                        <svg viewBox="0 0 200 200" class="w-full h-full">
                            <circle cx="100" cy="100" r="96" fill="#172554" stroke="#fbbf24" stroke-width="6"/>
                            <polygon points="100,50 125,120 75,120" fill="#fbbf24"/>
                            <rect x="85" y="125" width="30" height="22" rx="3" fill="#facc15"/>
                        </svg>
                    </div>
                    <div>
                        <div class="flex items-center space-x-2">
                            <h2 class="font-extrabold text-base tracking-wide text-white">நாங்கம் காவல் நண்பன்</h2>
                            <span class="text-xs font-bold text-amber-300 bg-amber-500/15 border border-amber-400/30 px-2 py-0.5 rounded">NAANGHAM KAAVAL NANBAN</span>
                            <span class="text-[11px] text-emerald-400 font-semibold px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded flex items-center gap-1">
                                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-ping"></span> SECURE GRID LIVE
                            </span>
                        </div>
                        <p class="text-[11px] text-slate-400">Tamil Nadu Police Integrated Tactical Command • सत्यमेव जयते</p>
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
                <div class="lg:col-span-4 bg-[#0d182e] border border-amber-500/30 rounded-xl p-4 flex flex-col overflow-hidden space-y-4 shadow-lg">
                    <form onsubmit="createBlockade(event)" class="bg-[#070e1c] border border-amber-500/25 p-3.5 rounded-lg space-y-2.5">
                        <div class="flex justify-between items-center">
                            <h4 class="text-xs font-bold uppercase text-amber-400 tracking-wider"><i class="fa-solid fa-bullhorn mr-1 text-red-500"></i>Broadcast Blockade</h4>
                            <span class="text-[10px] text-slate-400">Click map for coordinates</span>
                        </div>
                        <input type="text" id="loc_name" required placeholder="Location (e.g. Kumbakonam Bus Stand)" class="w-full bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white focus:border-amber-400 focus:outline-none">
                        <div class="grid grid-cols-2 gap-2">
                            <input type="number" step="any" id="lat" required value="10.9601" placeholder="Latitude" class="bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
                            <input type="number" step="any" id="lng" required value="79.3845" placeholder="Longitude" class="bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
                        </div>
                        <input type="text" id="notes" placeholder="Patrol directive / sensor details" class="w-full bg-[#0d182e] border border-slate-700 rounded px-3 py-1.5 text-xs text-white">
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
                        <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400">Active Checkposts & Alerts</h3>
                        <div class="flex items-center space-x-2">
                            <button onclick="clearResolved()" class="text-[11px] text-slate-400 hover:text-red-400 cursor-pointer">Clear Cleared</button>
                            <button onclick="loadBlockades()" class="text-amber-400 hover:text-amber-300 text-xs cursor-pointer"><i class="fa-solid fa-rotate"></i></button>
                        </div>
                    </div>
                    <div id="blockade-list" class="flex-1 overflow-y-auto space-y-2.5 pr-1"></div>
                </div>

                <div class="lg:col-span-8 flex flex-col gap-5 overflow-hidden">
                    <div class="flex-1 bg-[#0d182e] border border-amber-500/30 rounded-xl p-3 flex flex-col relative overflow-hidden min-h-[300px] shadow-lg">
                        <div class="flex justify-between items-center mb-2 px-1">
                            <span class="text-xs font-bold uppercase tracking-wider text-amber-400"><i class="fa-solid fa-map-location-dot text-red-500 mr-1.5"></i>TN Police Geo-Radar Grid (Click Map to Select Coordinates)</span>
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
            let generatedOTP = '';
            let tempRegData = {};

            function switchTab(tab) {
                const loginTab = document.getElementById('tab-login');
                const regTab = document.getElementById('tab-register');
                const loginForm = document.getElementById('form-login');
                const regForm = document.getElementById('form-register');

                if (tab === 'login') {
                    loginTab.className = 'py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer';
                    regTab.className = 'py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer';
                    loginForm.classList.remove('hidden');
                    regForm.classList.add('hidden');
                } else {
                    regTab.className = 'py-2 text-xs font-bold rounded-lg bg-amber-500 text-slate-950 transition cursor-pointer';
                    loginTab.className = 'py-2 text-xs font-bold rounded-lg text-slate-300 hover:text-white transition cursor-pointer';
                    regForm.classList.remove('hidden');
                    loginForm.classList.add('hidden');
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
                    errDiv.innerText = 'Please fill in all officer registration fields.';
                    errDiv.classList.remove('hidden');
                    return;
                }
                errDiv.classList.add('hidden');

                tempRegData = { name, badge_number: badge, mobile, email, password };
                generatedOTP = Math.floor(100000 + Math.random() * 900000).toString();

                await fetch('/auth/request-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, mobile, otp: generatedOTP })
                });

                document.getElementById('reg-step-1').classList.add('hidden');
                document.getElementById('reg-step-2').classList.remove('hidden');
                document.getElementById('otp-hint').innerText = `[SIMULATED SMS/MAIL OTP]: ${generatedOTP}`;
            }

            async function verifyAndRegister() {
                const enteredOTP = document.getElementById('reg-otp').value;
                const errDiv = document.getElementById('reg-error');

                if (enteredOTP !== generatedOTP) {
                    errDiv.innerText = 'Invalid OTP code. Please check simulation hint.';
                    errDiv.classList.remove('hidden');
                    return;
                }

                const res = await fetch('/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(tempRegData)
                });

                if (!res.ok) {
                    const err = await res.json();
                    errDiv.innerText = err.detail || 'Registration failed.';
                    errDiv.classList.remove('hidden');
                    return;
                }

                alert('Officer account registered successfully! Please log in.');
                switchTab('login');
                document.getElementById('login-username').value = tempRegData.badge_number;
                document.getElementById('login-password').value = tempRegData.password;
            }

            function initMap() {
                if (map) return;
                map = L.map('map').setView([10.9601, 79.3845], 10);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap | நாங்கம் காவல் நண்பன்'
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
                setTimeout(() => {
                    initMap();
                    loadBlockades();
                    loadNotifications();
                }, 100);
            }

            async function handleLogin(e) {
                e.preventDefault();
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
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
                    document.getElementById('user-badge').innerText = 'Officer: ' + username;
                    showDashboard();
                } catch (err) {
                    const errDiv = document.getElementById('login-error');
                    errDiv.innerText = 'Incorrect badge ID or password.';
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
                                    ${b.status === 'ACTIVE' ? `<button onclick="assignUnit(${b.id})" class="bg-blue-700/40 hover:bg-blue-700/60 border border-blue-400/30 text-blue-200 text-[11px] px-2.5 py-0.5 rounded transition cursor-pointer">Dispatch</button>` : ''}
                                    ${b.status !== 'RESOLVED' ? `<button onclick="resolveBlockade(${b.id})" class="bg-emerald-700/30 hover:bg-emerald-700/50 border border-emerald-400/30 text-emerald-300 text-[11px] px-2.5 py-0.5 rounded transition cursor-pointer">Clear</button>` : ''}
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
                        }).bindPopup(`<b>${b.location_name}</b><br>Severity: ${b.severity}<br>Status: ${b.status}`);
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

@app.post("/auth/register", tags=["Authentication"])
def register_officer(reg: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.badge_number == reg.badge_number) | (User.username == reg.badge_number)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Officer with this Badge ID already registered.")
    
    new_user = User(
        username=reg.badge_number,
        password=reg.password,
        name=reg.name,
        email=reg.email,
        mobile=reg.mobile,
        badge_number=reg.badge_number
    )
    db.add(new_user)
    db.add(Notification(message=f"[OFFICER REGISTRATION] New officer {reg.name} (Badge: {reg.badge_number}) registered."))
    db.commit()
    return {"message": "Officer registered successfully"}

@app.post("/auth/request-otp", tags=["Authentication"])
def request_otp(data: dict):
    print(f"\n[TN POLICE OTP DISPATCH] Sent to Email: {data.get('email')} & Mobile: {data.get('mobile')} -> OTP: {data.get('otp')}\n")
    return {"message": "OTP dispatched successfully"}

@app.post("/auth/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or user.password != form_data.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect badge ID or password")
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
        ("Trichy-Chennai NH-45 Sector 9", 10.8254, 78.6921, "MEDIUM", "Automated Speed Radar: Sudden traffic halt detected")
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
    db.add(Notification(message=f"[PATROL DISPATCHED] Unit assigned to {b.location_name}"))
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