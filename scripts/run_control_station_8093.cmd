@echo off
cd /d "%~dp0.."
python -B -m control_station.app --host 0.0.0.0 --port 8093 1>control_station.8093.out.log 2>control_station.8093.err.log
