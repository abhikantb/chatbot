@echo off
title Launching Chatbot App
cls

echo ===================================================
echo     Starting LangGraph AI Chatbot Assistant...
echo ===================================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call myenv\Scripts\activate

echo Launching Streamlit interface in browser...
echo.

streamlit run frontend\app.py
pause