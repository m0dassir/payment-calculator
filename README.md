# Payment Calculator

Small Windows desktop apps for calculating monthly class payments and exam paper earnings.

## Apps

- `payment_calc_desktop.py`: manual monthly calculator.
- `payment_calendar_app.py`: daily calendar tracker that saves class counts and calculates monthly totals.

## Run From Python

```powershell
python payment_calc_desktop.py
python payment_calendar_app.py
```

## Build Windows EXE

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name PaymentCalculator --distpath outputs\dist --workpath work\pyinstaller_build --specpath work payment_calc_desktop.py
python -m PyInstaller --onefile --windowed --name PaymentCalendar --distpath outputs\dist --workpath work\pyinstaller_calendar_build --specpath work payment_calendar_app.py
```

The built apps are saved at:

```text
outputs\dist\PaymentCalculator.exe
outputs\dist\PaymentCalendar.exe
```
