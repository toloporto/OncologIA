Write-Host "⬇️  Descargando FFMPEG (esto puede tardar unos segundos)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"

Write-Host "📦 Descomprimiendo..." -ForegroundColor Cyan
Expand-Archive -Path "ffmpeg.zip" -DestinationPath ".\ffmpeg_temp" -Force

Write-Host "🚀 Instalando en venv\Scripts..." -ForegroundColor Cyan
# Encontrar ffmpeg.exe dentro de las subcarpetas
$ffmpegBin = Get-ChildItem -Path ".\ffmpeg_temp" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1

if ($ffmpegBin) {
    Move-Item -Path $ffmpegBin.FullName -Destination ".\venv\Scripts\ffmpeg.exe" -Force
    Write-Host "✅ FFMPEG instalado correctamente en el entorno virtual." -ForegroundColor Green
}
else {
    Write-Host "❌ Error: No se encontró ffmpeg.exe en el archivo descargado." -ForegroundColor Red
}

# Limpieza
Write-Host "🧹 Limpiando archivos temporales..." -ForegroundColor Gray
Remove-Item "ffmpeg.zip" -Force
Remove-Item ".\ffmpeg_temp" -Recurse -Force

Write-Host "✅ Verificando instalación..." -ForegroundColor Cyan
& ".\venv\Scripts\ffmpeg.exe" -version
if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 TODO LISTO. Ahora puedes probar el reconocimiento de voz." -ForegroundColor Green
}
