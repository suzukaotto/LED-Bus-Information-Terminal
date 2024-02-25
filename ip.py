import subprocess
import re

def get_ip_address(interface):
    try:
        result = subprocess.run(["ifconfig", interface], capture_output=True, text=True)
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
        if match:
            return match.group(1)
        else:
            return None
    except Exception as e:
        print("Error getting IP address:", e)
        return None

interface = "wlan0"
ip_address = get_ip_address(interface)

if ip_address:
    print("IP Address:", ip_address)
else:
    print("IP address not found.")
