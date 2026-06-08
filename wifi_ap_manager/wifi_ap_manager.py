import subprocess
import time

skip_connect = False
disabled_ap  = False
result       = ""

try:
    with open("/home/pi/printer_data/config/wifi", "r") as f: 
        for line in f: 
            line = line.strip() 
            if line.startswith("SSID:"): 
                ssid = line[len("SSID:"):].strip() 
            elif line.startswith("PASS:"): 
                password = line[len("PASS:"):].strip()
            elif line.startswith("DISABLE_AP"): 
                disabled_ap = True
            elif line.startswith("AP_NAME"): 
                ap_name = line[len("AP_NAME:"):].strip()
    print("File opened, data:")
    print("SSID \t\t=", ssid) 
    print("PASS \t\t=", password)
    print("AP disable \t=", disabled_ap)
    print("AP NAME \t=", ap_name,"\n")
except:
    print("No wifi file skipping to AP")
    skip_connect = True

# Restart wifi adapter to make sure it is ready to run the next commands
#try:
result = subprocess.run( 'sudo nmcli r wifi off', shell=True, capture_output=True, text=True )
result = subprocess.run( 'sudo nmcli r wifi on', shell=True, capture_output=True, text=True )
print("Wifi restart sucessful waiting for wifi card to be ready and scanning")
while(True):
    print("Scan loop")
    result = subprocess.run( 'sudo nmcli -f SSID dev wifi', shell=True, capture_output=True, text=True )
    result = result.stdout.split("\n")
    #print(len(result))
    if (len(result) > 2):
        break
    time.sleep(1)

    #time.sleep(10)
#except:
#    print("Wifi restart fail. Aborting!")
#    exit()

# Try scanning wifi
#if not skip_connect:
#    print("In wifi scan")
#    try:
#        #result = subprocess.run( 'sudo iw dev wlan0 scan | grep -oP "(?<=SSID:).*"', shell=True, capture_output=True, text=True )
#        #result = subprocess.run( 'sudo nmcli -f SSID dev wifi | grep -oP "(?<=SSID:).*"', shell=True, capture_output=True, text=True )
#        result = subprocess.run( 'sudo nmcli -f SSID dev wifi', shell=True, capture_output=True, text=True )
#        print(result.stdout)
#    except:
#        print("Could not scan for wifi! Skipping to AP generation")
#        skip_connect = True


# Check if wifi is on list and attempt connection
connected = False
is_present = False
if not skip_connect:
    print("In Wifi check list")
    is_present = False
    for line in result:
        print(line)
        if ssid in line:
            is_present = True

if is_present:
    print("Found requested wifi! Attempting connection")
    wifi_connect_string = 'sudo nmcli dev wifi connect \"' + ssid + '\" password \"' + password + '\"'

    try:
        result = subprocess.run( wifi_connect_string, shell=True, capture_output=True, text=True )
        if result.returncode == 0:
            connected = True
        else:
            print("Could not connect to wifi! Retrying")
            wifi_connect_string = 'sudo nmcli dev wifi connect \"' + ssid + '\"'
            result = subprocess.run( wifi_connect_string, shell=True, capture_output=True, text=True )
            if result.returncode == 0:
                connected = True
    except:
        print("Could not connect to wifi! Skipping to AP generation")

    if connected:
        print("Wifi connected!")
        exit()
else:
    print("Could not find requested wifi! Skipping to AP generation")

# If everything else fails create default AP if DISABLE_AP is not set on wifi file
if not disabled_ap:
    connected = False
    try:
        result = subprocess.run( 'sudo nmcli device wifi hotspot ifname wlan0 ssid '+ap_name+' password de-alpha', shell=True, capture_output=True, text=True )
        print(result.stdout)
        if result.returncode == 0:
            connected = True
    except:
        print("Could not connect to wifi! Skipping to AP generation")
    if connected:
        print("AP generated!")
    else:
        print("AP generation failed!")
else:
    print("AP generation disabled!")