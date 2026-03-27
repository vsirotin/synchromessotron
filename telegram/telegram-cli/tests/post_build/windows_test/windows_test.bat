@echo off
setlocal enabledelayedexpansion
:: =============================================================================
:: Windows platform test for telegram-cli
:: Calls the native binary directly — no Python required.
::
:: Scenarios (exit code + line count, no JSON parsing):
::   1. version
::   2. get-dialogs --limit=50 --outdir  (file created)
::   3. backup February 2026 — all media types
::   4. help
::   5. download-media (known voice message, msg 42389, Jan 7 2026)
::   6. send / edit / delete flow
::
:: Usage (from dist\ — config.yaml must be present there):
::   cd telegram\telegram-cli\dist
::   ..\tests\post_build\windows_test\windows_test.bat
::
:: Or pass an explicit CLI path as the first argument:
::   ..\tests\post_build\windows_test\windows_test.bat C:\path\to\telegram-cli.exe
:: =============================================================================

set "SCRIPT_DIR=%~dp0"
if "%~1"=="" (
    set "CLI=%SCRIPT_DIR%..\..\..\dist\telegram-cli.exe"
) else (
    set "CLI=%~1"
)

set "DIALOG=-4821106881"
set /a PASS=0
set /a FAIL=0
set "SEP=============================================================="

:: Work directory for temp files
set "WORK=%TEMP%\tg_win_%RANDOM%"
mkdir "%WORK%" 2>nul

echo %SEP%
echo telegram-cli Windows platform tests
echo CLI: %CLI%
echo %SEP%
echo.

goto :main

:: ─── helpers ─────────────────────────────────────────────────────────────────

:pass
    echo [PASS] %~1
    set /a PASS+=1
    goto :eof

:fail
    echo [FAIL] %~1
    set /a FAIL+=1
    goto :eof

:: :count_lines FILEPATH  →  sets LINE_COUNT
:count_lines
    set LINE_COUNT=0
    for /f "usebackq delims=" %%x in ("%~1") do set /a LINE_COUNT+=1
    goto :eof

:: :run_test LABEL
:: Uses LAST_RC and OUT_FILE set by the caller.
:run_test
    call :count_lines "%OUT_FILE%"
    if !LAST_RC! EQU 0 if !LINE_COUNT! GTR 0 (
        call :pass "%~1  (!LINE_COUNT! lines)"
    ) else (
        call :fail "%~1  (rc=!LAST_RC!, !LINE_COUNT! lines)"
    )
    goto :eof

:main

:: ─── Test 1: version ─────────────────────────────────────────────────────────
echo [Test 1] version
set "OUT_FILE=%WORK%\out.txt"
"%CLI%" version > "%OUT_FILE%" 2>&1
set LAST_RC=!ERRORLEVEL!
call :run_test "version"
echo.

:: ─── Test 2: get-dialogs to file ─────────────────────────────────────────────
echo [Test 2] get-dialogs --outdir
set "DLDIR=%WORK%\dialogs"
set "OUT_FILE=%WORK%\out.txt"
"%CLI%" get-dialogs --limit=50 "--outdir=%DLDIR%" > "%OUT_FILE%" 2>&1
set LAST_RC=!ERRORLEVEL!
call :run_test "get-dialogs --limit=50 --outdir"

if exist "%DLDIR%\dialogs.json" (
    call :count_lines "%DLDIR%\dialogs.json"
    call :pass "dialogs.json created  (!LINE_COUNT! lines)"
) else (
    call :fail "dialogs.json not found"
)
echo.

:: ─── Test 3: backup February 2026 — all media types ─────────────────────────
echo [Test 3] backup February 2026 -- all media
set "BKDIR=%WORK%\backup_feb"
set "OUT_FILE=%WORK%\out.txt"
"%CLI%" backup %DIALOG% --limit=500 ^
    --since=2026-02-01T00:00:00+00:00 ^
    --upto=2026-02-28T23:59:59+00:00 ^
    --media --files --music --voice --links ^
    "--outdir=%BKDIR%" > "%OUT_FILE%" 2>&1
set LAST_RC=!ERRORLEVEL!
call :run_test "backup Feb 2026 (--media --files --music --voice --links)"

:: Confirm at least one subdirectory was created under backup output dir
set "BKFOUND="
for /d %%d in ("%BKDIR%\*") do if not defined BKFOUND set "BKFOUND=%%d"
if defined BKFOUND (
    call :pass "backup dialog directory created"
) else (
    call :fail "backup dialog directory not found under %BKDIR%"
)
echo.

:: ─── Test 4: help ────────────────────────────────────────────────────────────
echo [Test 4] help
set "OUT_FILE=%WORK%\out.txt"
"%CLI%" help > "%OUT_FILE%" 2>&1
set LAST_RC=!ERRORLEVEL!
call :run_test "help"
echo.

:: ─── Test 5: download-media ──────────────────────────────────────────────────
echo [Test 5] download-media
set "DLMDIR=%WORK%\dl"
mkdir "%DLMDIR%" 2>nul
set "OUT_FILE=%WORK%\out.txt"
:: Message 42389 = voice_2026-01-07_13-09-39.ogg  (dialog -4821106881)
"%CLI%" download-media %DIALOG% 42389 "--dest=%DLMDIR%" > "%OUT_FILE%" 2>&1
set LAST_RC=!ERRORLEVEL!
call :run_test "download-media msg 42389"
echo.

:: ─── Test 6: send / edit / delete ────────────────────────────────────────────
echo [Test 6] send / edit / delete
set "SEND_FILE=%WORK%\send_out.txt"
"%CLI%" send %DIALOG% --text="Windows platform test - please ignore" > "%SEND_FILE%" 2>&1
set SEND_RC=!ERRORLEVEL!
call :count_lines "%SEND_FILE%"
set SEND_LINES=!LINE_COUNT!

if !SEND_RC! EQU 0 if !SEND_LINES! GTR 0 (
    call :pass "send  (!SEND_LINES! lines)"

    :: Extract message ID with PowerShell (minimal JSON parse)
    set "MSG_ID="
    for /f "usebackq" %%i in (`powershell -noprofile -command "(gc '%SEND_FILE%' -Raw | ConvertFrom-Json).id" 2^>nul`) do set MSG_ID=%%i

    if defined MSG_ID (
        set "OUT_FILE=%WORK%\out.txt"
        "%CLI%" edit %DIALOG% !MSG_ID! --text="Windows platform test - EDITED" > "%OUT_FILE%" 2>&1
        set LAST_RC=!ERRORLEVEL!
        call :run_test "edit  (id=!MSG_ID!)"

        set "OUT_FILE=%WORK%\out.txt"
        "%CLI%" delete %DIALOG% !MSG_ID! > "%OUT_FILE%" 2>&1
        set LAST_RC=!ERRORLEVEL!
        call :run_test "delete  (id=!MSG_ID!)"
    ) else (
        call :fail "edit  (message id not found in send output)"
        call :fail "delete  (skipped -- no message id)"
    )
) else (
    call :fail "send  (rc=!SEND_RC!, !SEND_LINES! lines)"
    call :fail "edit  (skipped -- send failed)"
    call :fail "delete  (skipped -- send failed)"
)

:: ─── cleanup ─────────────────────────────────────────────────────────────────
rmdir /s /q "%WORK%" 2>nul

:: ─── summary ─────────────────────────────────────────────────────────────────
echo.
echo %SEP%
echo Results:  PASS=%PASS%  FAIL=%FAIL%
echo %SEP%

if %FAIL% EQU 0 (
    exit /b 0
) else (
    exit /b 1
)
