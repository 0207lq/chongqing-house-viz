@echo off
REM ============================================
REM 重庆二手房数据可视化平台 - 启动脚本
REM ============================================
echo ============================================
echo  🏠 重庆二手房数据可视化平台
echo ============================================
echo.
echo [信息] 正在启动 Streamlit 应用...
echo [信息] 启动后请在浏览器中访问显示的地址
echo [信息] 默认地址: http://localhost:8501
echo.

cd /d "D:\my-project\visualization"

"C:\Users\李琦\AppData\Local\Programs\Python\Python38\python.exe" -m streamlit run app.py

pause
