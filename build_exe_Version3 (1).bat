@echo off
REM Budowanie exe z katalogami projektu bez widocznego terminala

REM Sprzątanie poprzednich buildów
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Budujemy EXE, uwzględniamy katalogi z kodem i zasobami, tryb windowed (brak terminala)
pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name=Zamowienia ^
  --add-data "models;models" ^
  --add-data "printing;printing" ^
  --add-data "resources;resources" ^
  --add-data "tests;tests" ^
  --add-data "utils;utils" ^
  --add-data "widgets;widgets" ^
  --add-data ".github;.github" ^
  main.py

REM Przenosimy exe do katalogu głównego (opcjonalnie)
if exist dist\Zamowienia.exe move /Y dist\Zamowienia.exe .

echo.
echo ============================================
echo  Gotowe! Plik EXE: Zamowienia.exe (brak konsoli)
echo ============================================
pause