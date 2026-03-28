@echo off
set app_name=DETEQX

echo Cleaning previous build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%app_name%.spec" del "%app_name%.spec"

echo Installing dependencies...
pip install -r requirements.txt

echo Building with PyInstaller...
pyinstaller build.spec --noconfirm

echo Build completed!
echo Executable is in the dist folder
pause