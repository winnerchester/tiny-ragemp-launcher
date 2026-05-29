@echo off
setlocal

REM Locate VS 2022 dev environment
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" set "VSWHERE=%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe"

for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
    set "VS_INSTALL=%%i"
)

if not defined VS_INSTALL (
    echo [!] Visual Studio 2022 with C++ tools not found.
    exit /b 1
)

call "%VS_INSTALL%\VC\Auxiliary\Build\vcvars64.bat" >nul

REM CMake bundled with VS
set "CMAKE=%VS_INSTALL%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if not exist "%CMAKE%" set "CMAKE=cmake"

set "BUILD_DIR=%~dp0build"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

pushd "%BUILD_DIR%"
"%CMAKE%" -G "Ninja" -DCMAKE_BUILD_TYPE=Release .. || (
    echo [!] CMake configure failed
    popd
    exit /b 1
)

"%CMAKE%" --build . --config Release || (
    echo [!] Build failed
    popd
    exit /b 1
)

popd

echo.
echo [+] Build complete: %BUILD_DIR%\tiny-ragemp-launcher.exe
echo.
