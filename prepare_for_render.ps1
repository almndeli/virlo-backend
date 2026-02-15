# Virlo Render Preparation Script V1.0
# Prepares the project for deployment on Render.com

Write-Host "--- 🚀 PREPARING VIRLO FOR RENDER ---" -ForegroundColor Cyan

# 0. Check Path
if (-Not (Test-Path "virlo/settings.py")) {
    Write-Host "❌ Error: Please run this inside the 'backend' folder." -ForegroundColor Red
    return
}

# 1. Install Production Libraries
Write-Host "📦 Installing Production Libraries..." -ForegroundColor Yellow
pip install gunicorn dj-database-url psycopg2-binary whitenoise

# 2. Freeze Requirements
Write-Host "📄 Generating requirements.txt..." -ForegroundColor Yellow
pip freeze > requirements.txt

# 3. Create build.sh
Write-Host "🔨 Creating build.sh..." -ForegroundColor Yellow
$buildScript = @'
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
'@
# Save as ASCII/UTF8 without BOM for Linux compatibility
[System.IO.File]::WriteAllLines("build.sh", $buildScript, (New-Object System.Text.UTF8Encoding($False)))

# 4. Update settings.py for Production
Write-Host "⚙️ Configuring settings.py for Render..." -ForegroundColor Yellow
$settingsPath = "virlo/settings.py"
$currentSettings = Get-Content $settingsPath -Raw

# Add WhiteNoise for static files if missing
if ($currentSettings -notlike "*whitenoise*") {
    $currentSettings = $currentSettings -replace "django.middleware.security.SecurityMiddleware", "django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware"
}

# Add Production Config Block at the end
if ($currentSettings -notlike "*RENDER_EXTERNAL_HOSTNAME*") {
    $prodConfig = @'

# --- RENDER PRODUCTION CONFIG ---
import dj_database_url
import os

if 'RENDER' in os.environ:
    DEBUG = False
    ALLOWED_HOSTS = [os.environ.get('RENDER_EXTERNAL_HOSTNAME')]
    
    # Database
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///db.sqlite3',
            conn_max_age=600
        )
    }
    
    # Static Files
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
'@
    $currentSettings += $prodConfig
    $currentSettings | Out-File -FilePath $settingsPath -Encoding utf8 -Force
}

# 5. Create render.yaml (The Blueprint) in the ROOT folder (../)
Write-Host "🗺️ Creating render.yaml..." -ForegroundColor Yellow
$renderYaml = @'
services:
  # 1. The Backend (Django)
  - type: web
    name: virlo-backend
    env: python
    rootCommand: cd backend
    buildCommand: ./build.sh
    startCommand: gunicorn virlo.wsgi:application
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_CONCURRENCY
        value: 4
      - key: DATABASE_URL
        fromDatabase:
          name: virlo-db
          property: connectionString

databases:
  - name: virlo-db
    databaseName: virlo
    user: virlo
    plan: free
'@
$renderYaml | Out-File -FilePath "../render.yaml" -Encoding utf8 -Force

# 6. Update Frontend Trends.jsx to use Environment Variable
Write-Host "🌐 Updating Frontend to accept Live URL..." -ForegroundColor Yellow
$frontendPath = "../frontend/virlo-web/src/pages/Trends.jsx"
if (Test-Path $frontendPath) {
    $feContent = Get-Content $frontendPath -Raw
    # Replace hardcoded localhost with env variable logic
    $feContent = $feContent -replace "http://127.0.0.1:8000", "`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}"
    $feContent | Out-File -FilePath $frontendPath -Encoding utf8 -Force
}

Write-Host "--- ✅ PREPARATION COMPLETE! ---" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Push your code to GitHub."
Write-Host "2. Go to Render.com -> Blueprints -> New Blueprint Instance."
Write-Host "3. Connect your repo and approve."