@echo off
REM Verificar Python
python --version >nul 2>&1 && set PYTHON_CMD=python && goto :start
py --version >nul 2>&1 && set PYTHON_CMD=py && goto :start
python3 --version >nul 2>&1 && set PYTHON_CMD=python3 && goto :start
echo ERRO: Python nao encontrado! Instale Python 3.8+ e tente novamente.
pause
exit /b 1

:start
if not exist "venv" %PYTHON_CMD% -m venv venv
call venv\Scripts\activate.bat
%PYTHON_CMD% -m pip install -q -r requirements.txt
echo.
echo Servidor iniciado: http://localhost:5000
echo Pressione Ctrl+C para parar
echo.
%PYTHON_CMD% app.py
