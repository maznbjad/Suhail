@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Suhail - تشغيل تطبيق سهيل

set "PYEXE="

rem Prefer the active Python command when available.
where python >nul 2>nul
if not errorlevel 1 set "PYEXE=python"

rem Common Anaconda / Miniconda locations on Windows.
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYEXE if exist "C:\ProgramData\anaconda3\python.exe" set "PYEXE=C:\ProgramData\anaconda3\python.exe"
if not defined PYEXE if exist "C:\ProgramData\miniconda3\python.exe" set "PYEXE=C:\ProgramData\miniconda3\python.exe"

if not defined PYEXE (
  echo.
  echo [خطأ] لم يتم العثور على Python أو Anaconda.
  echo افتح Anaconda Prompt وشغّل الملف مرة أخرى، أو ثبّت Python أولاً.
  echo.
  pause
  exit /b 1
)

echo ==========================================
echo        تشغيل تطبيق سهيل
 echo ==========================================
echo Python: %PYEXE%
echo المجلد: %CD%
echo.

"%PYEXE%" -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo Streamlit غير مثبت. سيتم تثبيت المتطلبات الآن...
  "%PYEXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [خطأ] فشل تثبيت المتطلبات.
    echo صوّر هذه النافذة وأرسلها لي.
    echo.
    pause
    exit /b 1
  )
)

echo.
echo سيتم فتح سهيل على:
echo http://127.0.0.1:8501
echo.
echo اترك هذه النافذة مفتوحة أثناء استخدام التطبيق.
echo للإيقاف اضغط Ctrl+C ثم Y.
echo.

"%PYEXE%" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501

if errorlevel 1 (
  echo.
  echo [خطأ] توقف التطبيق. صوّر رسالة الخطأ الموجودة أعلاه وأرسلها لي.
  echo.
  pause
)
endlocal
