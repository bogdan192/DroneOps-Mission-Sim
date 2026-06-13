@echo off
cd /d "%~dp0.."
python -B -m control_station.app 1>control_station.out.log 2>control_station.err.log
