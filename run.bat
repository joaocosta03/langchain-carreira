@echo off
REM Script de execução rápida para Windows

echo ======================================
echo Agente Consultor de Carreira em TI
echo ======================================
echo.

REM Ativa ambiente virtual se existir
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] Ambiente virtual ativado
) else (
    echo [AVISO] Ambiente virtual nao encontrado
    echo Execute: python -m venv .venv
    pause
    exit /b 1
)

REM Verifica se .env existe
if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado
    echo Execute: python setup.py
    pause
    exit /b 1
)

echo.
echo Executando agente...
echo.

python main.py

pause

