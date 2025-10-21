@echo off
echo Activating Python environment...
call env\Scripts\activate

echo Cleaning previous build artifacts...
if exist "dist" (
  echo Deleting dist folder...
  rmdir /s /q "dist"
)
if exist "build" (
  echo Deleting build folder...
  rmdir /s /q "build"
)
echo Running PyInstaller on formclient.py...
pyinstaller --onefile --windowed --name "wowclient" formclient.py

echo.
echo Build complete! Check the 'dist' folder for your executable.
call env\Scripts\deactivate
pause