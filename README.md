# dual-boot-mouse

On a dual boot computer, you would find yourself needing to pair your bluetooth device again. To prevent this, you will need to transfer the bluetooth keys between the OSes. This can be done manually, but it's pretty complicated.

This script greatly simplifies the steps required.


## Disclaimer
> This script involves accessing and modifying system files on the Windows / Linux systems and may risk damaging your computer. Proceed with the below steps at your own risk.


## Instructions
1. Pair the mouse in Linux.
2. Reboot your computer and pair the mouse in Windows.
3. Download [PSExec](http://technet.microsoft.com/en-us/sysinternals/bb897553.aspx) to the same folder as `GetBTKeys.bat`.
4. Run `GetBTKeys.bat` in Administator mode. This will create a file `BTKeys.reg` in the same folder.
5. Reboot back to Linux, run `dual-boot-mouse.py` with sudo.


## Links for further reading

### Manual Guides
- Mario Olivio Flores's guide: https://unix.stackexchange.com/questions/255509/bluetooth-pairing-on-dual-boot-of-windows-linux-mint-ubuntu-stop-having-to-p
- Stefan Fabian's answer: https://unix.stackexchange.com/questions/402488/dual-boot-bluetooth-le-low-energy-device-pairing
- https://console.systems/2014/09/how-to-pair-low-energy-le-bluetooth.html

### Similar scripts
- https://gist.github.com/Mygod/f390aabf53cf1406fc71166a47236ebf
- https://github.com/aryklein/dualBootMouse
- https://github.com/LondonAppDev/dual-boot-bluetooth-pair

