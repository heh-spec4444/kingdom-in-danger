@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ====================================================
echo        Королевство в опасности — Запуск игры
echo ====================================================
echo.

rem Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 goto :no_python

rem Проверка наличия библиотеки pygame
python -c "import pygame" >nul 2>&1
if errorlevel 1 goto :install_deps

:run_game
echo [INFO] Запуск игры...
python main.py %*
if errorlevel 1 goto :game_error
goto :eof

:install_deps
echo [INFO] Библиотека pygame не найдена. Установка зависимостей...
python -m pip install -r requirements.txt
if errorlevel 1 goto :install_error
echo [INFO] Зависимости успешно установлены.
echo.
goto :run_game

:no_python
echo [ERROR] Python не найден в системе!
echo Установите Python с https://www.python.org/ и отметьте "Add python.exe to PATH".
echo.
pause
exit /b 1

:install_error
echo.
echo [ERROR] Не удалось установить зависимости из requirements.txt.
pause
exit /b 1

:game_error
echo.
echo ====================================================
echo [ERROR] Игра завершилась с ошибкой. Текст ошибки выше.
echo ====================================================
pause
exit /b 1
