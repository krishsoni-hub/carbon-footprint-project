# ⚡ EcoPulse - Carbon Footprint Awareness Web Application

EcoPulse is a premium, state-of-the-art **Cyber-Eco Dark Mode** web application designed to track, calculate, and raise awareness of personal carbon footprints. Combining Flask backends, standard carbon conversion algorithms, and Google's official Gemini AI parsing modules, EcoPulse enables users to log activities in natural language and receive an automated carbon footprint analysis.

---

## 🎨 Theme & Design Aesthetics

- **Background**: Pitch Dark Cyber-Eco theme (`#090D16`) with ambient radial emerald glows.
- **Primary Text**: Crisp Slate White (`#F3F4F6`).
- **Accents**: High-contrast Emerald Green (`#10B981`) and Soft Sage muted green (`#34D399`).
- **Layouts**: Premium glassmorphic stat readouts (`backdrop-blur-md bg-[#0F1626]/60 border border-white/10`) and dynamic, responsive components fully compliant with **WCAG 2.1 AA** web accessibility standard.

---

## 🚀 Key Features

1. **Cyber-Eco Dashboard**: Modern asymmetrical executive layout displaying total emissions, weekly targets, remaining allowance progress bars, and localized AI context warning alerts.
2. **Interactive AI Assistant**: Natural language conversational chat panel translating human statements (e.g., *"Drove my petrol car 15km to the grocery store"*) directly into structured carbon metrics.
3. **Operational Database**: SQLite persistence utilizing Flask-SQLAlchemy, supporting structural schemas for `User`, `CarbonLog`, `UserGoal`, and database-level column indexing on filtering (`timestamp`, `user_id`).
4. **Algorithmic Calculator**: Rigorous calculations based on global carbon constants (Petrol, Diesel, EV travel emissions, active appliance hours, and dietary footprint configurations).
5. **Deterministic Parser**: Driven by `gemini-2.5-flash` model with schema parameters to guarantee standardized JSON outputs.
6. **Recommendations Engine**: Dynamic advice algorithm compile targeted tips (e.g. for high transport, high diet, or high energy) based on daily emission logs.

---

## 🔒 SecOps: Production Security Protocols

EcoPulse implements strict defensive systems to ensure secure application hosting:
1. **Production Security Headers Middleware**:
   Injects robust custom headers on every outgoing HTTP response to block cross-site scripting (XSS), clickjacking, and MIME sniffing:
   - `Content-Security-Policy (CSP)` set to: `"default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data:;"`.
   - `X-Frame-Options` set to `DENY` (blocks clickjacking/framing).
   - `X-Content-Type-Options` set to `nosniff` (prevents MIME sniffing).
   - `Referrer-Policy` set to `strict-origin-when-cross-origin`.
2. **Advanced Input Sanitization Utility**:
   Utilizes native `re` and `html` modules to filter incoming messages, actively stripping dynamic scripting elements (`<script>`), HTML tags, and escaping characters.
3. **Cryptographic Protection**:
   Uses `werkzeug.security` (hashing algorithms) to secure password fields inside the database, alongside SQL-parameterized variable binding across all query statements.

---

## ⚡ Performance Optimization & Memory Tuning

- **Paginated Generator Streaming**: Retrieves historical carbon log arrays using a python generator with limit-offset chunking to avoid loading heavy arrays into application memory.
- **Selective Column Query Loading**: Implements SQLAlchemy's `.options(load_only(...))` configurations to fetch only the necessary columns, bypassing SQLAlchemy ORM instantiation overhead.

---

## 🧪 Testing & Quality Assurance (94% Coverage)

EcoPulse features a robust automated testing script [`tests/test_app.py`](tests/test_app.py) containing **22 production-grade test cases** verifying all API endpoints, database operations, security configurations, math calculations, and exception paths.

### Run tests locally:
```powershell
python tests/test_app.py
```

### Check code coverage:
```powershell
coverage run tests/test_app.py ; coverage report
```
*Result: **94% total code coverage** achieved.*

```text
Name                             Stmts   Miss  Cover
----------------------------------------------------
app.py                             156     18    88%
config.py                            8      0   100%
controllers\ai_assistant.py         30      1    97%
controllers\calculator.py           39      0   100%
controllers\recommendations.py      21      0   100%
models\database.py                  87     14    84%
tests\test_app.py                  225      0   100%
----------------------------------------------------
TOTAL                              566     33    94%
```

---

## 🛠️ Project Structure

```text
├── controllers/
│   ├── ai_assistant.py     # Gemini AI text metric extraction engine
│   ├── calculator.py       # Algorithmic carbon footprint calculator (Fully Typed)
│   └── recommendations.py  # Contextual advice engine (Fully Typed)
├── models/
│   └── database.py         # SQLAlchemy schemas with index & Werkzeug hash support
├── templates/
│   ├── base.html           # Core responsive HTML5 accessible layout skeleton
│   ├── index.html          # Main executive dashboard
│   └── chat.html           # Real-time AI chat assistant view
├── static/
│   └── js/
│       └── charts.js       # Chart.js curved line rendering configurations
├── tests/
│   └── test_app.py         # 22-unit/integration test suite (94% coverage)
├── app.py                  # Secure Flask application, endpoints, and middleware
├── config.py               # Environmental configuration manager
├── requirements.txt        # Backend dependencies list
└── README.md               # Project documentation manual
```

---

## 💻 Installation & Setup

### 1. Clone the repository
Navigate to your project folder:
```powershell
cd "d:\MAIN PROJECTS\Carbon Footprint Awareness"
```

### 2. Install Dependencies
Ensure you have Python installed, then run the installer:
```powershell
pip install -r requirements.txt
```

### 3. Set Environment Variables
Add your secrets to your local configuration:
Create a `.env` file in the root folder with:
```text
SECRET_KEY="your_secure_session_key_secret"
GEMINI_API_KEY="your_google_gemini_api_key"
```

### 4. Run the Dev Server
Launch the Flask development server:
```powershell
python app.py
```
Visit the local dashboard at: `http://127.0.0.1:5000/`

---

## 🧪 Mathematical Conversion Coefficients

Our calculation algorithms enforce the following standards:

- **Petrol vehicle travel**: `0.192 kg CO₂` / km
- **Diesel vehicle travel**: `0.171 kg CO₂` / km
- **EV electric travel**: `0.047 kg CO₂` / km
- **Grid Electricity (active appliance state)**: `0.45 kg CO₂` / hour
- **High Meat Diet**: `3.3 kg CO₂` / day
- **Vegetarian Diet**: `1.7 kg CO₂` / day