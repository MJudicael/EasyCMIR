@echo off

REM Minimiser la fenêtre du terminal
if not "%1"=="minimized" (
    start /min cmd /c "%~f0" minimized
    exit /b
)

echo ===========================================
echo   EasyCMIR - Interface Web Autonome
echo ===========================================
echo.

REM Vérifier si Python est disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou disponible
    echo Veuillez installer Python ou utiliser une version portable
    pause
    exit /b 1
)

REM Aller dans le répertoire du script
cd /d "%~dp0"

echo 1. Synchronisation des donnees (SQLite vers JSON)...
python sync_materiel.py export

if errorlevel 1 (
    echo ERREUR lors de la synchronisation
    pause
    exit /b 1
)

echo.
echo 2. Demarrage du serveur web local...
echo.
echo Interface accessible a : http://localhost:8000
echo.

REM Démarrer le serveur HTTP en arrière-plan
start /B python -m http.server 8000

REM Attendre que le serveur soit prêt
echo Demarrage du serveur en cours...
timeout /t 3 /nobreak >nul

REM Ouvrir l'interface dans le navigateur par défaut
echo 3. Ouverture de l'interface web...
start http://localhost:8000

echo.
echo ✅ Interface ouverte dans votre navigateur !
echo.
echo 💡 Cette fenetre est maintenant minimisee
echo    Le serveur fonctionne en arriere-plan
echo    Pour arreter : Clic droit sur l'icone dans la barre des taches ^> Fermer
echo.

REM Attendre indéfiniment (le serveur tourne en arrière-plan)
:loop
timeout /t 30 /nobreak >nul
goto loop
