#!/usr/bin/env python3
import os
import sys
import configparser
import codecs

print("""Please ensure these steps have been done before running this script.
Step 1: Pair device in Linux
Step 2: Pair device in Windows
Step 3: Download PSExec.
Step 4: Run GetBTKeys.bat as Adminstrator in Windows
""")

if os.getuid() != 0:
    print("This script requires root privileges. Please rerun using sudo.")
    sys.exit(1)

def process_hex(hex_str, reverse=False, joiner=''):
    """Converts Windows MAC format to Linux eg. a1b2c3d4e5f6 -> A1:B2:C3:D4:E5:F6"""
    if ':' in hex_str:
        hex_str = hex_str.split(':')[1]
    hex_str = hex_str.replace(',', '')
    hexes = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
    if reverse:
        hexes = hexes[::-1]
    return joiner.join(hexes).upper()



# Load Windows bluetooth regfile into a ConfigParser object
try:
    with codecs.open('BTKeys.reg', 'r', 'utf-16-le') as f:
        data = f.read()
except FileNotFoundError:
    print("ERROR: BTKeys.reg not found. Have you done step 3?")
    exit()
data = data.replace('"', '')
data = (line.strip() for line in data.split('\r\n')[1:])
config = configparser.ConfigParser()
config.read_file(data)

# Skip those front short sections
for section in config.sections():
    if len(section) > 98:
        break

# Extract relevant data from regfile
hardware_mac, mouse_mac = [process_hex(e, joiner=':') for e in section.split('\\')[-2:]]
ltk = process_hex(config[section]['LTK'])
ediv = str(int(config[section]['EDIV'].split(':')[1], 16))
rand = str(int(process_hex(config[section]['ERand'], reverse=True), 16))
changes = [('LongTermKey', 'Key', ltk),
            ('LongTermKey', 'EDiv', ediv),
            ('LongTermKey', 'Rand', rand)
            ]


assert hardware_mac in os.listdir("/var/lib/bluetooth")

# Get user to select device to change
available_macs = list(filter(lambda x: len(x) == 17, os.listdir("/var/lib/bluetooth/" + hardware_mac)))
for i, mac in enumerate(available_macs):
    with open("/var/lib/bluetooth/" + hardware_mac + '/' + mac + '/info') as f:
        name = f.read().splitlines()[1]
    print(f"{i+1}) {mac} - {name}")
while True:
    userinput = input("Select device: ")
    try:
        i = int(userinput) - 1
        assert i < len(available_macs)
    except Exception as e:
        print("Invalid input")
    else:
        print()
        break
if mouse_mac != available_macs[i]:
    cmd = f"mv /var/lib/bluetooth/{hardware_mac}/{available_macs[i]} /var/lib/bluetooth/{hardware_mac}/{mouse_mac}"
    print(">", cmd)
    os.system(cmd)

# Load Linux bluetooth info file into a ConfigParser object
linux_file = f"/var/lib/bluetooth/{hardware_mac}/{mouse_mac}/info"
config = configparser.ConfigParser()
config.optionxform = str  # To preserve case
with open(linux_file) as f:
    config.read_string(f.read())

# Show user what changes will be made
output = ''
for section in config.sections():
    output += f"[{section}]\n"
    for key in config[section]:
        output += f"{key}={config[section][key]}"
        for s, k, new_value in changes:
            if section == s and key == k:
                output += f" --> {new_value}"
                break
        output += '\n'
    output += '\n'
print(f"Changes to be made to {linux_file}")
print('-' * 50)
print(output.strip())
print('-' * 50)

# Write out to file upon user confirmation
input("Press enter to accept changes")
for s, k, new_value in changes:
    config[s][k] = new_value
with open(linux_file, 'w') as f:
    config.write(f, False)

# Reload bluetooth module
cmd = "systemctl restart bluetooth"
input(f"Press enter to reload bluetooth module ({cmd})")
print('>', cmd)
os.system(cmd)
