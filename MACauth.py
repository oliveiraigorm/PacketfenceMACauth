import requests
import csv
import getpass 
import urllib3
import json
import mysql.connector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

macs = []
roles = []
ids = []
categoryid = {}

def main():
    ip = input("\nPlease enter PacketFence's IP address or hostname: ")
    token = login(ip)
    
    count =0 
    while count < 3:
        option = input("\nPlease enter \"1\" to read list from a CSV File or \"2\" to read from Database: ")
        if(option == "1"):
            readFile()
            getCategID(ip, token)
            register(ip, token)
            break;
        if(option == "2"):
            logSQL()
            getCategID(ip, token)
            register(ip, token)
            break;
        else:
            print("Invalid option")
            count += 1   
    if(count == 3):
        print("\nMax attempts, exiting ...")
        exit()

def logSQL():

    ip = input("\nPlease enter SQL Server's IP address or hostname [localhost]: ")
    if(ip == ""):
        ip = "localhost"
    database = input("\nPlease enter SQL database's name: ")
    user = input("\nUsername: ")
    password = getpass.getpass() 
    
    mydb = mysql.connector.connect(
    host=ip,
    user=user,
    password=password,
    database=database
    )
    query = input("\nPlease enter SQL query to select MACs and VLANs [SELECT * FROM macs]:")
    if(query == ""):
        query = "SELECT * FROM macs"
    mycursor = mydb.cursor()

    mycursor.execute(query)

    myresult = mycursor.fetchall()

    for x in myresult:
      macs.append(x[0])
      roles.append(x[1])

    
def Convert(a):
    it = iter(a)
    res_dct = dict(zip(it, it))
    return res_dct
             
def login(ip):

    count=0
    
    url = 'https://' + ip + ':9999/api/v1/login'

    head = {'accept': 'application/json', 'Content-Type': 'application/json'}
    while count < 3:
        user = input("\nUsername: ")
        password = getpass.getpass() 
        payload = "{\n\
        \"username\":\"%s\",\
        \n\"password\": \"%s\"\
        \n}" % (user, password)
        r = requests.post(url, data=payload, headers=head, verify=False)
        if r.status_code == 200:
            print("\nLogin successfull\n")
            return r.json()["token"]
        else:
            print('\nAccess denied. Try again.')
            count += 1
    
    print("\nMax login attempts, exiting ...")
    exit()
        
def readFile():

    count=0
    
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

def getCategID(ip, token):
    
    url = 'https://' + ip + ':9999/api/v1/node_categories'
    head = {'accept': 'application/json', 'Authorization': token}
    r = requests.get(url, headers=head, verify=False)
    response = r.json()
    x = 0
    
    while x < len(response["items"]):
        ids.append(response["items"][x]["name"])
        ids.append(response["items"][x]["category_id"])
        x += 1
    
    
def register(ip, token):

    url2 = 'https://' + ip + ':9999/api/v1/nodes'
    url3 = 'https://' + ip + ':9999/api/v1/node/'
    
    headers2 = {'accept': 'application/json', 'Authorization': token}

    success = 0
    failed = []
    
    categoryid = Convert(ids)
    
    for m,r in zip(macs, roles):
        category_id = categoryid.get(r)
        if category_id:
            payload2 = "{\n\
            \"mac\":\"%s\",\
            \n\"category_id\": \"%s\",\
            \n\"status\": \"reg\"\
            \n}" % (m,category_id)

            r2 = requests.post(url2,data = payload2, headers=headers2, verify=False)
            if r2.status_code == 201:
                print("MAC \"%s\" with VLAN \"%s\" successfully registered"% (m,r)) 
                success += 1
            if r2.status_code == 500:
                print("Internal Server error, MAC \"%s\" with VLAN \"%s\" failed to register"% (m,r))
                failed.append([m,r])
            if r2.status_code == 409:
                print("MAC entry \"%s\" already exists, registering ..." % (m))
                r2 = requests.patch(url3 + m, data=payload2, headers=headers2, verify=False)
                if r2.status_code == 200:
                    print("MAC \"%s\" with VLAN \"%s\" successfully registered"% (m,r))
                    success += 1
                if r2.status_code == 500:
                    print("Internal Server error, MAC \"%s\" with VLAN \"%s\" failed to register"% (m,r))
                    failed.append([m,r])
        else:
            print("Role %s does not exist, create it on PacketFence" % r)
            failed.append([m,r])

    print("\n\n\n\n\tNumber of successfully registered MACs:  %d " % (success))
    if len(failed) > 0:
        print("\n\n\tFailed to register:")
        print("\n\t%s" %failed)

    print("\n")
    

    
if __name__ == "__main__":
    main()
    
