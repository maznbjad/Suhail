@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Suhail API

set "PYEXE="
where python >nul 2>nul
if not errorlevel 1 set "PYEXE=python"
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYEXE (
  echo [خطأ] لم يتم العثور على Python.
  pause
  exit /b 1
)

"%PYEXE%" -c "import flask, flask_cors, waitress" >nul 2>nul
if errorlevel 1 (
  echo تثبيت متطلبات API...
  "%PYEXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [خطأ] فشل تثبيت المتطلبات.
    pause
    exit /b 1
  )
)

"%PYEXE%" scripts\build_learning_db.py
if errorlevel 1 (
  echo [خطأ] فشل بناء قاعدة البيانات.
  pause
  exit /b 1
)

if not defined SUHAIL_ADMIN_TOKEN (
  echo.
  echo [تنبيه] SUHAIL_ADMIN_TOKEN غير مضبوط.
  echo API سيعمل، لكن نشر إعدادات الأدمن سيبقى مقفلاً حتى تضبطه.
  echo مثال قبل التشغيل: set SUHAIL_ADMIN_TOKEN=ضع-رمزا-طويلا-هنا
  echo.
)

echo Suhail API Sprint 54: http://127.0.0.1:5000
echo Health: http://127.0.0.1:5000/health
"%PYEXE%" -m waitress.runner --host=0.0.0.0 --port=5000 src.api.server:app
if errorlevel 1 pause
endlocal
