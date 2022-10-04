import exoscale

exo = exoscale.Exoscale()

BUCKET_NAME = "cloudsys-lab1-bucket"
FILE_TO_UPLOAD = "test.json"
SERVER_INSTANCE_NAME = "cloudsys-lab1-server"
CLIENT_INSTANCE_NAME = "cloudsys-lab1-client"
SERVER_SECURITY_GROUP_NAME = "cloudsys-lab1-sgs"
CLIENT_SECURITY_GROUP_NAME = "cloudsys-lab1-sgc"
SERVER_APP_GITHUB_URL = "https://github.com/Danielcourvoisier/cloudsys-lab1-server.git"
CLIENT_APP_GITHUB_URL = "https://github.com/Danielcourvoisier/cloudsys-lab1-client.git"
SERVER_APP_PORT = 8080
CLIENT_APP_PORT = 8383

# Create bucket
print("Create bucket...")
bucket = exo.storage.create_bucket(BUCKET_NAME, zone="ch-gva-2")
print(f"{bucket.name} created!")


# Upload test.json to bucket
print("Upload file to bucket...")
file_index = bucket.put_file(FILE_TO_UPLOAD)
# Set ACL for the uploaded file
file_index.set_acl('public-read')
print(f"File uploaded to bucket (url: {file_index.url} )")


# Create zone in Geneva
zone_gva2 = exo.compute.get_zone("ch-gva-2")

print("Create security groups...")
# Create basic security group for server and client instances
security_group_server = exo.compute.create_security_group(SERVER_SECURITY_GROUP_NAME)
for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTP",
        network_cidr="0.0.0.0/0",
        port="80",
        protocol="tcp",
        ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTPS",
        network_cidr="0.0.0.0/0",
        port="443",
        protocol="tcp",
        ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="SSH",
        network_cidr="0.0.0.0/0",
        port="22",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="APP PORT",
        network_cidr="0.0.0.0/0",
        port=f"{SERVER_APP_PORT}",
        protocol="tcp",
    ),
]:
    security_group_server.add_rule(rule)

security_group_client = exo.compute.create_security_group(CLIENT_SECURITY_GROUP_NAME)
for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTP",
        network_cidr="0.0.0.0/0",
        port="80",
        protocol="tcp",
        ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTPS",
        network_cidr="0.0.0.0/0",
        port="443",
        protocol="tcp",
        ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="SSH",
        network_cidr="0.0.0.0/0",
        port="22",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="APP PORT",
        network_cidr="0.0.0.0/0",
        port=f"{CLIENT_APP_PORT}",
        protocol="tcp",
    ),
]:
    security_group_client.add_rule(rule)

# create server instance
print("Create server instance...")
server_instance = exo.compute.create_instance(
    name="cloudsys-lab1-server",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("small"),
    template=list(
        exo.compute.list_instance_templates(
            zone_gva2,
            "Linux Ubuntu 22.04 LTS 64-bit"))[0],
    volume_size=10,
    security_groups=[security_group_server],
    user_data="""#cloud-config
    runcmd:
    - apt -y update
    - apt -y install git
    - apt -y install python3-pip
    - pip3 install "fastapi[all]"
    - apt -y install uvicorn 
    - cd /home/ubuntu
    - git clone {app}
    - export BUCKET_URL={bucket_url}
    - export APP_PORT={port}
    - cd /home/ubuntu/cloudsys-lab1-server/
    - uvicorn main:app --host 0.0.0.0 --port $APP_PORT
    """.format(app=SERVER_APP_GITHUB_URL,
               bucket_url=file_index.url,
               port=SERVER_APP_PORT)
)
print(f"Server instance IP: {server_instance.ipv4_address}")
server_url = f"http://{server_instance.ipv4_address}:{SERVER_APP_PORT}"
print(server_url)

# create client instance
print("Create client instance...")
client_instance = exo.compute.create_instance(
    name="cloudsys-lab1-client",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("small"),
    template=list(
        exo.compute.list_instance_templates(
            zone_gva2,
            "Linux Ubuntu 22.04 LTS 64-bit"))[0],
    volume_size=10,
    security_groups=[security_group_client],
    user_data="""#cloud-config
    runcmd:
    - apt -y update
    - apt -y install git
    - apt -y install python3-pip
    - pip3 install "fastapi[all]"
    - apt -y install uvicorn 
    - cd /home/ubuntu
    - git clone {app}
    - export SERVER_IP={server_ip_address}
    - export SERVER_PORT={server_port}
    - export APP_PORT={port}
    - cd /home/ubuntu/cloudsys-lab1-client/
    - uvicorn main:app --host 0.0.0.0 --port $APP_PORT
    """.format(app=CLIENT_APP_GITHUB_URL,
               server_ip_address=server_instance.ipv4_address,
               server_port=SERVER_APP_PORT,
               port=CLIENT_APP_PORT)
)
print(f"Client instance IP: {client_instance.ipv4_address}")
client_url = f"http://{client_instance.ipv4_address}:{CLIENT_APP_PORT}"
print(client_url)


# Wait for user input to delete instances
sec = input("Press Enter to delete infrastructure:")
server_instance.delete()
client_instance.delete()
file_index.delete()
bucket.delete()
security_group_server.delete()
security_group_client.delete()

