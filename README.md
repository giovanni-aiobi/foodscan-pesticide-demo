# 🌱 Pesticide Compliance Checker - Demo

Interactive Streamlit app to check pesticide residue compliance against EU and Codex Alimentarius MRL standards.

## 🚀 Live Demo

**Deployed on Streamlit Cloud:** [Add URL after deployment]

## ✨ Features

- ✅ Check 2,294+ crop × pesticide combinations
- 🇪🇺 EU MRL compliance validation
- 🌍 Codex Alimentarius standards
- 📊 Residue level vs MRL comparison
- 🔄 Approved alternatives suggestions
- 📖 Good Agricultural Practice (GAP) recommendations

## 🗄️ Database

Powered by **COLEAD Good Agricultural Practices Database** via Supabase:
- 78 crops
- 173 active substances
- 2,294 combinations with MRL limits
- EU approval status tracking
- GAP recommendations (dose, applications, pre-harvest intervals)

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Supabase account (free tier works)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/giovanni-aiobi/foodscan-pesticide-demo.git
   cd foodscan-pesticide-demo
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Supabase:**
   
   Create `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```

4. **Run the app:**
   ```bash
   streamlit run demo_app.py
   ```

   Open http://localhost:8501

## 🌐 Deploy to Streamlit Cloud

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/giovanni-aiobi/foodscan-pesticide-demo.git
git push -u origin main
```

### Step 2: Deploy

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click **"New app"**
4. Configure:
   - **Repository:** `giovanni-aiobi/foodscan-pesticide-demo`
   - **Branch:** `main`
   - **Main file:** `demo_app.py`

5. **Add Secrets** (Advanced settings → Secrets):
   ```toml
   SUPABASE_URL = "https://sjhxhnyusceeciuraros.supabase.co"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```

6. Click **"Deploy"** 🚀

### Step 3: Share
Your app will be live at: `https://[app-name].streamlit.app`

## 📊 How It Works

### Backend: `pesticide_checker.py`
```python
from pesticide_checker import PesticideChecker

checker = PesticideChecker()
result = checker.check_compliance(
    crop="mango",
    substance="Azoxystrobin",
    target_market="EU",
    residue_level=2.0
)

print(result.status)  # "COMPLIANT" | "NON_COMPLIANT" | "WARNING" | "UNKNOWN"
print(result.message)
```

### Database Schema
The app queries the `pesticide_mrl` table in Supabase with 26 columns:
- `crop` - Crop name (e.g., "mango", "tomato")
- `active_substance` - Pesticide name
- `mrl_eu` - EU Maximum Residue Limit (mg/kg)
- `mrl_codex` - Codex MRL
- `eu_status` - "Approuvée" | "Non approuvée"
- `dose`, `max_applications`, `preharvest_eu`, etc. - GAP data

## 🧪 Example Queries

### Compliant Example
- **Crop:** Mango
- **Substance:** Azoxystrobin
- **Residue:** 2.0 mg/kg
- **Result:** ✅ Compliant (MRL: 4.0 mg/kg)

### Non-Compliant Example
- **Crop:** Mango
- **Substance:** Alpha-cypermethrin
- **Result:** ❌ NOT APPROVED in EU

### MRL Exceeded
- **Crop:** Mango
- **Substance:** Azoxystrobin
- **Residue:** 5.0 mg/kg
- **Result:** ❌ Exceeds MRL (4.0 mg/kg)

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ Yes |
| `SUPABASE_KEY` | Supabase anon/public key | ✅ Yes |

## 📝 License

Proprietary - FoodScan Project

## 🤝 Contributing

This is a demo application. For the full FoodScan backend API, see the main repository.

## 📧 Contact

**Project:** FoodScan - Food Certification & Compliance Management  
**Author:** Giovanni Aiobi  
**Repository:** https://github.com/giovanni-aiobi/foodscan.arso

## 🙏 Acknowledgments

- **COLEAD** - Good Agricultural Practices Database
- **Supabase** - Backend database and hosting
- **Streamlit** - Web app framework
