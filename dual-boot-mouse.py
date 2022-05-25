#!/usr/bin/env python3
import codecs
import configparser
import csv
import glob
import sys
import os

LINUX_PAIRINGS_DIR = '/var/lib/bluetooth'
BTKEYS_REG_PATH = 'out/BTKeys.reg'
NAMES_CSV_PATH = 'out/names.csv'

INSTRUCTIONS = """Please ensure these steps have been done before running this script.
Step 1: Pair device in Linux
Step 2: Pair device in Windows
Step 3: Download PSExec.
Step 4: Run GetBTKeys.bat as Adminstrator in Windows
"""

print(INSTRUCTIONS)

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


def ask_user(d, prompt):
    for i, item in enumerate(d.items()):
        device_mac, name = item
        print(f"{i+1}) {device_mac} - {name}")
    while True:
        userinput = input(prompt)
        try:
            i = int(userinput) - 1
            assert i < len(available_devices)
        except (ValueError, AssertionError):
            print("Invalid input.")
            continue
        print()
        break
    return i


def procedure_load_files():
    # Load Windows bluetooth regfile into a ConfigParser object
    try:
        with codecs.open('out/BTKeys.reg', 'r', 'utf-16-le') as f:
            data = f.read()
    except FileNotFoundError:
        print("ERROR: BTKeys.reg not found. Have you done step 3?")
        sys.exit(1)
    data = data.replace('"', '')
    data = (line.strip() for line in data.split('\r\n')[1:])
    config = configparser.ConfigParser()
    config.read_file(data)
    
    # Load names.csv
    csvreader = csv.reader(open(NAMES_CSV_PATH))
    
    return config, csvreader


def procedure_user_select(csvreader, sections_map, available_devices):
    names = {}
    for row in csvreader:
        for mac in sections_map:
            if f"DEV_{mac.replace(':', '')}" in row[1]:
                names[mac] = row[0]

    d = {}
    for i, device in enumerate(available_devices):
        controller_mac, device_mac = device
        with open(f"{LINUX_PAIRINGS_DIR}/{controller_mac}/{device_mac}/info") as f:
            name = f.read().splitlines()[1]
        d[device_mac] = name
    win_num = ask_user(names, prompt="Select Windows device:")
    linux_num = ask_user(d, prompt="Select Linux device:")

    linux_controller_mac, linux_device_mac = available_devices[linux_num]
    win_device_mac = list(names.keys())[win_num]
    return linux_controller_mac, linux_device_mac, win_device_mac





config, csvreader = procedure_load_files()

sections_map = {}
for section in config.sections():
    # Skip those front short sections
    if len(section) < 98:
        continue
    sections_map[process_hex(section.split('\\')[-1], joiner=':')] = section

available_devices = [e for e in map(lambda x: x.split('/')[-2:], glob.glob(f"{LINUX_PAIRINGS_DIR}/*/*")) if len(e[1]) == 17]

linux_controller_mac, linux_device_mac, win_device_mac = procedure_user_select(csvreader, sections_map, available_devices)


# Extract relevant data from regfile
section = sections_map[win_device_mac]
ltk = process_hex(config[section]['LTK'])
ediv = str(int(config[section]['EDIV'].split(':')[1], 16))
rand = str(int(process_hex(config[section]['ERand'], reverse=True), 16))
changes = [
    ('LongTermKey', 'Key', ltk),
    ('LongTermKey', 'EDiv', ediv),
    ('LongTermKey', 'Rand', rand),
]


# Load Linux bluetooth info file into a ConfigParser object
LINUX_DEVICE_INFO_PATH = f"{LINUX_PAIRINGS_DIR}/{linux_controller_mac}/{win_device_mac}/info"
config = configparser.ConfigParser()
config.optionxform = str  # To preserve case
with open(LINUX_DEVICE_INFO_PATH) as f:
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
print("These are the list of changes to be made:")
if linux_device_mac != win_device_mac:
    cmd = f"mv {LINUX_PAIRINGS_DIR}/{linux_controller_mac}/{linux_device_mac} {LINUX_PAIRINGS_DIR}/{linux_controller_mac}/{win_device_mac}"
    print("- Spoof Windows MAC by moving file")
    print(">", cmd)
else:
    cmd = ''
print("- Edit config file of device")
print(f"\nChanges to be made to {LINUX_DEVICE_INFO_PATH}")
print('-' * 50)
print(output.strip())
print('-' * 50)


# Write out to file upon user confirmation
input("Press enter to accept these changes")
if cmd:
    os.system(cmd)
for s, k, new_value in changes:
    config[s][k] = new_value
with open(LINUX_DEVICE_INFO_PATH, 'w') as f:
    config.write(f, False)

# Reload bluetooth module
cmd = "systemctl restart bluetooth"
input(f"\nPress enter to reload bluetooth module ({cmd})")
print('>', cmd)
os.system(cmd)

print("Script completed successfully. Your device should now be paired.")
