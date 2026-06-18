# ⚡ EcoPulse - Carbon Footprint Awareness Web Application

EcoPulse is a premium, state-of-the-art **Cyber-Eco Dark Mode** web application designed to track, calculate, and raise awareness of personal carbon footprints. Combining Flask backends, standard carbon conversion algorithms, and Google's official Gemini AI parsing modules, EcoPulse enables users to log activities in natural language and receive an automated carbon footprint analysis.

---

## 🎨 Theme & Design Aesthetics

- **Background**: Pitch Dark Cyber-Eco theme (`#090D16`) with ambient radial emerald glows.
- **Primary Text**: Crisp Slate White (`#F3F4F6`).
- **Accents**: High-contrast Emerald Green (`#10B981`) and Soft Sage muted green (`#34D399`).
- **Layouts**: Premium glassmorphic stat readouts (`backdrop-blur-md bg-[#0F1626]/60 border border-white/10`) and dynamic, responsive components.

---

## 🚀 Key Features

1. **Cyber-Eco Dashboard**: Modern asymmetrical executive layout displaying total emissions, weekly targets, remaining allowance progress bars, and localized AI context warning alerts.
2. **Interactive AI Assistant**: Natural language conversational chat panel translating human statements (e.g., *"Drove my petrol car 15km to the grocery store"*) directly into structured carbon metrics.
3. **Operational Database**: SQLite persistence utilizing Flask-SQLAlchemy, supporting structural schemas for `User`, `CarbonLog`, `UserGoal`, and dashboard parameters.
4. **Algorithmic Calculator**: Rigorous calculations based on global carbon constants (Petrol, Diesel, EV travel emissions, active appliance hours, and dietary footprint configurations).
5. **Deterministic Parser**: Driven by `gemini-2.5-flash` model with schema parameters to guarantee standardized JSON outputs.

---

## 🛠️ Project Structure

```text
├── controllers/
│   ├── ai_assistant.py     # Gemini AI text metric extraction engine
│   └── calculator.py       # Algorithmic carbon footprint calculator
├── models/
│   └── database.py         # SQLAlchemy schemas (User, CarbonLog, UserGoal, CarbonMetric)
├── templates/
│   ├── base.html           # Core responsive HTML5 layout skeleton
│   ├── index.html          # Asymmetrical main executive dashboard (Pending)
│   └── chat.html           # Real-time AI chat stream interface (Pending)
├── static/
│   └── js/
│       └── charts.js       # Chart.js curved line rendering configurations (Pending)
├── app.py                  # Flask application orchestrator & API endpoints
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
Add your secrets to your environment:
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your_google_gemini_api_key"
$env:SECRET_KEY="your_secure_session_key_secret"
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