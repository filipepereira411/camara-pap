@echo off
:: Altera a codificação para aceitar acentos em Português
chcp 65001 > nul
title Criador de Aplicação FilipeCams
mode con: cols=80 lines=20
color 0B

echo ====================================================
echo             GERADOR DE APLICAÇÃO FILIPECAMS         
echo ====================================================
echo.
echo Este script vai criar um atalho nativo e isolado para
echo a sua Prova de Aptidão Profissional (PAP).
echo.
echo Opções de Alvo:
echo [1] Usar a versão online (filipecams.vercel.app)
echo [2] Usar o ficheiro HTML local deste computador
echo.
set /p opcao="Escolha uma opção (1 ou 2): "

if "%opcao%"=="1" (
    set "ALVO=https://vercel.app"
) else if "%opcao%"=="2" (
    if not exist "index.html" (
        cls
        color 0C
        echo [ERRO] O ficheiro 'index.html' não foi encontrado nesta pasta!
        echo Certifique-se de que este script está na mesma pasta do seu HTML.
        echo.
        pause
        exit
    )
    set "ALVO=%cd%\index.html"
) else (
    echo Opção inválida. A fechar...
    timeout /t 3 > nul
    exit
)

:: Nome da Aplicação e caminhos do atalho
set "APP_NAME=FilipeCams CCTV"
set "SCRIPT_PATH=%TEMP%\CriarAtalhoFilipeCams.vbs"
set "DESKTOP_PATH=%USERPROFILE%\Desktop"

echo.
echo A gerar a aplicação no Ambiente de Trabalho...

:: Script em VBScript gerado dinamicamente para criar o atalho com janela isolada (App Mode)
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SCRIPT_PATH%"
echo sLinkFile = "%DESKTOP_PATH%\%APP_NAME%.lnk" >> "%SCRIPT_PATH%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT_PATH%"

:: Utiliza o motor do Microsoft Edge/Chrome em modo "App" (esconde a barra de endereços do browser)
echo oLink.TargetPath = "msedge.exe" >> "%SCRIPT_PATH%"
echo oLink.Arguments = "--app=%ALVO% --start-maximized" >> "%SCRIPT_PATH%"
echo oLink.Description = "Painel de Controlo CCTV - FilipeCams" >> "%SCRIPT_PATH%"
echo oLink.IconLocation = "msedge.exe, 0" >> "%SCRIPT_PATH%"
echo oLink.Save >> "%SCRIPT_PATH%"

:: Executa o VBScript e elimina o temporário
cscript //nologo "%SCRIPT_PATH%"
del "%SCRIPT_PATH%"

cls
color 0A
echo ====================================================
echo        SUCESSO! APLICAÇÃO CRIADA COM SUCESSO        
echo ====================================================
echo.
echo Foi adicionado um novo ícone chamado "%APP_NAME%" 
echo ao seu Ambiente de Trabalho.
echo.
echo Quando o abrir, o sistema FilipeCams vai rodar numa
echo janela nativa e limpa (como se fosse um programa .exe).
echo.
pause
exit
