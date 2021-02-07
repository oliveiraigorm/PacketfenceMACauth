import requests
import csv
import getpass 
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

macs = []
roles = []

ip = input("\nPlease enter PacketFence's IP address: ")
url1 = 'https://' + ip + ':9999/api/v1/login'

headers1 = {'accept': 'application/json', 'Content-Type': 'application/json'}

count=0
allowed = 0

while count < 3:
    user = input("\nUsername: ")
    password = getpass.getpass() 
    payload1 = "{\n\
    \"username\":\"%s\",\
    \n\"password\": \"%s\"\
    \n}" % (user, password)
    r1 = requests.post(url1, data=payload1, headers=headers1, verify=False)
    if r1.status_code == 200:
        print("\nLogin successfull")
        allowed = 1
        break
    else:
        print('\nAccess denied. Try again.')
        count += 1
if allowed == 0:
    print("\nMax login attempts, exiting ...")
    exit()
allowed = 0

while count < 3:
    file = input("\nPlease enter CSV filename with MAC addresses and VLANs: ")
    try:
        with open(file) as csvDataFile:
            csvReader = csv.reader(csvDataFile)
            for row in csvReader:
                macs.append(row[0])
                roles.append(row[1])
    except FileNotFoundError:
        print("\n\tWrong file or file path")
        count += 1
        if count == 3:
            print("\nMax file attempts, exiting ...")
            exit()
    else:
        break

token = r1.text[10:-2]
print("\n")
url2 = 'https://' + ip + ':9999/api/v1/nodes'
url3 = 'https://' + ip + ':9999/api/v1/node/'
headers2 = {'accept': 'application/json', 'Authorization': token}

success = 0
failed = []
    
for m,r in zip(macs, roles):
    payload2 = "{\n\
    \"mac\":\"%s\",\
    \n\"pid\": \"%s\",\
    \n\"status\": \"reg\"\
    \n}" % (m,r)

    r2 = requests.post(url2, data=payload2, headers=headers2, verify=False)
    if r2.status_code == 201:
        print("MAC \"%s\" with VLAN \"%s\" successfully registered"% (m,r)) 
        success += 1
    if r2.status_code == 500:
        print("Internal Server error, MAC \"%s\" with VLAN \"%s\" failed to register, check PacketFence's settings"% (m,r))
        failed.append([m,r])
    if r2.status_code == 409:
        print("MAC entry \"%s\" already exists, registering ..." % (m))
        r2 = requests.patch(url3 + m, data=payload2, headers=headers2, verify=False)
        if r2.status_code == 200:
            print("MAC \"%s\" with VLAN \"%s\" successfully registered"% (m,r))
            success += 1
        if r2.status_code == 500:
            print("Internal Server error, MAC \"%s\" with VLAN \"%s\" failed to register, check PacketFence's settings"% (m,r))
            failed.append([m,r])
        

print("\n\n\n\n\tNumber of successfully registered MACs:  %d " % (success))
print("\n\n\tFailed to register:")
print("\n\t%s" %failed)

print("\n")
