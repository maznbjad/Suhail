@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Suhail - تشغيل تطبيق سهيل
set SUHAIL_ENABLE_DEV_ACCOUNTS=1

set "PYEXE="
set "PYARGS="
if exist ".venv\Scripts\python.exe" set "PYEXE=%CD%\.venv\Scripts\python.exe"
if not defined PYEXE (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PYEXE=py"
    set "PYARGS=-3"
  )
)
if not defined PYEXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYEXE if exist "C:\ProgramData\anaconda3\python.exe" set "PYEXE=C:\ProgramData\anaconda3\python.exe"
if not defined PYEXE if exist "C:\ProgramData\miniconda3\python.exe" set "PYEXE=C:\ProgramData\miniconda3\python.exe"

if not defined PYEXE (
  echo.
  echo [خطأ] لم يتم العثور على Python.
  echo ثبّت Python 3 ثم شغّل هذا الملف مرة أخرى.
  echo.
  pause
  exit /b 1
)

echo ==========================================
echo              تشغيل سهيل
echo ==========================================
echo Python: "%PYEXE%" %PYARGS%
echo المجلد: %CD%
echo.

"%PYEXE%" %PYARGS% -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo تثبيت متطلبات سهيل لأول مرة...
  "%PYEXE%" %PYARGS% -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [خطأ] فشل تثبيت المتطلبات. تحقق من اتصال الإنترنت ثم أعد المحاولة.
    echo.
    pause
    exit /b 1
  )
)

"%PYEXE%" %PYARGS% scripts\preflight.py
if errorlevel 1 (
  echo.
  echo [خطأ] فشل فحص التشغيل الموضح أعلاه.
  echo.
  pause
  exit /b 1
)

set /a PORT=8501
:CHECK_PORT
netstat -ano | findstr /R /C:":!PORT! .*LISTENING" >nul 2>nul
if not errorlevel 1 (
  set /a PORT+=1
  if !PORT! LEQ 8510 goto CHECK_PORT
  echo [خطأ] المنافذ من 8501 إلى 8510 مستخدمة. أغلق نسخة سهيل القديمة ثم حاول مجددًا.
  pause
  exit /b 1
)

set "LOCAL_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip=(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object {$_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown'} ^| Select-Object -First 1 -ExpandProperty IPAddress); if($ip){$ip}" 2^>nul`) do set "LOCAL_IP=%%I"

echo.
echo افتح سهيل على الكمبيوتر:
echo http://127.0.0.1:!PORT!
if defined LOCAL_IP (
  echo.
  echo ومن الجوال على نفس شبكة الواي فاي:
  echo http://!LOCAL_IP!:!PORT!
)
echo.
echo اترك هذه النافذة مفتوحة. للإيقاف اضغط Ctrl+C.
echo إذا ظهر تنبيه جدار الحماية اختر السماح للشبكات الخاصة فقط.
echo.

rem Sprint 114: start the social/challenge API automatically when port 5000 is free.
netstat -ano | findstr /R /C:":5000 .*LISTENING" >nul 2>nul
if errorlevel 1 (
  echo تشغيل خادم الأصدقاء والتحديات على المنفذ 5000...
  "%PYEXE%" %PYARGS% scriptsuild_learning_db.py >nul 2>nul
  start "Suhail API" /min "%PYEXE%" %PYARGS% -m waitress.runner --host=0.0.0.0 --port=5000 src.api.server:app
  timeout /t 2 /nobreak >nul
)

"%PYEXE%" %PYARGS% -m streamlit run app.py ^
  --server.address 0.0.0.0 ^
  --server.port !PORT! ^
  --server.headless false ^
  --server.fileWatcherType none ^
  --browser.gatherUsageStats false

if errorlevel 1 (
  echo.
  echo [خطأ] توقف سهيل. انسخ آخر رسالة خطأ ظاهرة في هذه النافذة.
  echo.
  pause
)
endlocal
