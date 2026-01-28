@echo off
REM Script para detener Flask, eliminar BD y reiniciar

echo Deteniendo Flask...
taskkill /F /IM python.exe 2>nul

echo Esperando...
timeout /t 2

echo Eliminando BD antigua...
del "C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean\instance\tut0hub.db" 2>nul

echo Recreando BD...
cd "C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean"
python recreate_db.py

echo Iniciando servidor...
set YOUTUBE_API_KEY=AIzaSyBDxvMwbKwBdx-UkbtFywAICI-43OtEnbY
python run.py
