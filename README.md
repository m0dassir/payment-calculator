# Payment Calculator

A small Windows desktop app for calculating monthly class payments and exam paper earnings.

## Run From Python

```powershell
python payment_calc_desktop.py
```

## Build Windows EXE

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name PaymentCalculator --distpath outputs\dist --workpath work\pyinstaller_build --specpath work payment_calc_desktop.py
```

The built app is saved at:

```text
outputs\dist\PaymentCalculator.exe
```
