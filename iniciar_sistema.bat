@echo off
title Sistema CR-NOVACAP
cls

echo =====================================================
echo       INICIANDO O SISTEMA CR DA NOVACAP
echo =====================================================
echo.

:: 1. Entrar na pasta do projeto
cd /d "%~dp0"

:: 2. Ativar Ambiente Virtual Python (venv)
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else (
    echo [AVISO] Pasta venv nao encontrada! Tentando rodar sem venv...
)
echo.

:: 3. Definir variaveis de ambiente do Flask
set FLASK_APP=run.py
set FLASK_ENV=development

:: 4. Verificar dependencias do requirements.txt
echo [INFO] Verificando dependencias...
pip install -r requirements.txt --quiet
echo.

echo =====================================================
echo  SISTEMA PRONTO PARA INICIAR!
echo =====================================================
echo.
echo Acesse no seu navegador:
echo    http://localhost:5000
echo.
echo (Mantenha esta janela aberta enquanto usar o sistema)
echo =====================================================
echo.

:: 5. Executar a aplicacao Flask
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [TENTATIVA 2] Executando via "flask run"...
    flask run --host=0.0.0.0 --port=5000
)

echo.
echo =====================================================
echo  O SERVIDOR FOI FINALIZADO OU OCORREU UM ERRO.
echo =====================================================
pause