# 🚀 Deploy Pesticide Demo to Streamlit Cloud
# Quick deployment script

Write-Host "🌱 Pesticide Compliance Checker - Deployment Setup" -ForegroundColor Green
Write-Host ""

$deployFolder = "F:\github.com_extension\FOODSCAN\FOODSCAN.ARSO\pesticide-demo-deploy"
$repoName = "foodscan-pesticide-demo"

Write-Host "📦 Deployment package ready at:" -ForegroundColor Cyan
Write-Host "   $deployFolder"
Write-Host ""

Write-Host "📋 Files included:" -ForegroundColor Cyan
Get-ChildItem $deployFolder -Recurse -File | Select-Object -ExpandProperty FullName | ForEach-Object {
    $relativePath = $_.Replace("$deployFolder\", "")
    Write-Host "   ✅ $relativePath" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Create new GitHub repo:" -ForegroundColor White
Write-Host "   👉 https://github.com/new" -ForegroundColor Cyan
Write-Host "   Repository name: $repoName" -ForegroundColor Gray
Write-Host "   Public/Private: Public (for Streamlit Cloud free tier)" -ForegroundColor Gray
Write-Host ""

Write-Host "2️⃣  Initialize and push:" -ForegroundColor White
Write-Host "   cd $deployFolder" -ForegroundColor Gray
Write-Host "   git init" -ForegroundColor Gray
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Initial commit: Pesticide compliance checker demo'" -ForegroundColor Gray
Write-Host "   git branch -M main" -ForegroundColor Gray
Write-Host "   git remote add origin https://github.com/giovanni-aiobi/$repoName.git" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  Deploy to Streamlit Cloud:" -ForegroundColor White
Write-Host "   👉 https://share.streamlit.io/" -ForegroundColor Cyan
Write-Host "   - Sign in with GitHub" -ForegroundColor Gray
Write-Host "   - Click 'New app'" -ForegroundColor Gray
Write-Host "   - Repository: giovanni-aiobi/$repoName" -ForegroundColor Gray
Write-Host "   - Branch: main" -ForegroundColor Gray
Write-Host "   - Main file: demo_app.py" -ForegroundColor Gray
Write-Host ""

Write-Host "4️⃣  Add Secrets in Streamlit Cloud:" -ForegroundColor White
Write-Host "   Click 'Advanced settings' → 'Secrets'" -ForegroundColor Gray
Write-Host "   Copy content from .streamlit/secrets.toml.example" -ForegroundColor Gray
Write-Host ""   

Write-Host "✨ Your app will be live at:" -ForegroundColor Green
Write-Host "   https://[your-custom-url].streamlit.app" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 Tip: Test locally first with 'streamlit run demo_app.py'" -ForegroundColor Yellow
Write-Host ""
