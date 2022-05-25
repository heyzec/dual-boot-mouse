@echo OFF
if not exist "%~dp0\out" mkdir "%~dp0\out" && echo Created folder %~dp0\out to store bluetooth data.


echo Getting registry entires using psexec.exe and saving to out\BTKeys.reg
"%~dp0\psexec.exe" -s -i regedit /e "%~dp0\out\BTKeys.reg" HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Services\BTHPORT\Parameters\Keys


if %errorlevel% == 0 (
	echo.
	echo Getting device names of available bluetooth devices and saving to out\names.csv
	powershell "Get-PnpDevice -Class 'Bluetooth' | Select-Object FriendlyName,InstanceId | Export-CSV -NoTypeInformation %~dp0\out\names.csv"
	echo.
	echo Script completed successfully. You can now reboot to Linux to continue the pairing process.
) else (
	echo Please rerun this script using "Run with Administrator!"
)


pause