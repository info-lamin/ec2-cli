import os
import sys
import boto3
import pyperclip

final_instances = list()


def retrieve_ec2_instances():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.all()
    print(f'{"ID":<2} {"Instance ID":<20} {"Name":<25} {"State":<15} {"Instance Type":<15} {"Public IPv4":<20}')
    final_instances.clear()
    for key, instance in enumerate(instances):
        name = ''
        for tag in instance.tags or []:
            if tag['Key'] == 'Name':
                name = tag['Value']
        final_instances.append(
            (instance.id, name, instance.public_ip_address or ""))
        print(
            f'{key:<2} {instance.id:<20} {name[:25]:<25} {instance.state["Name"]:<15} {instance.instance_type:<15} {instance.public_ip_address or "N/A":<20}')


def create_ec2_instance():
    ec2 = boto3.resource('ec2')
    instance_name = input("Enter Instance Name: ")
    instance_type = input(
        "Enter Instance Type (default: t2.micro): ") or 't2.micro'
    key_pairs_client = boto3.client('ec2')
    key_pairs_response = key_pairs_client.describe_key_pairs()
    key_pairs = key_pairs_response['KeyPairs']

    print("Key Pairs Available:")
    for i, key_pair in enumerate(key_pairs):
        print(f"{i}. {key_pair['KeyName']}")
    key_pair_index = int(input("Enter your Key Pair (index): "))
    key_name = key_pairs[key_pair_index]['KeyName']

    security_groups = [
        ('Production Website Group', 'sg-090235eb6bc9b2a0e'),
        ('Allow All', 'sg-04496392c2efa7f7f'),
    ]

    print("Select Firewall:")
    for index, (name, sg_id) in enumerate(security_groups):
        print(f"{index}. {name} - {sg_id}")
    security_group_index = int(
        input("Enter your Firewall selection (index): "))
    security_group_ids = security_groups[security_group_index][1]

    storage_size = input("Storage Size (default 8GB): ") or 8
    no_of_instances = input("No Of Instances (default 1): ") or 1

    instance = ec2.create_instances(
        ImageId='ami-0866a3c8686eaeeba',  # Ubuntu Latest
        MinCount=int(no_of_instances),
        MaxCount=int(no_of_instances),
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=[security_group_ids],
        BlockDeviceMappings=[{
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': int(storage_size),
                'DeleteOnTermination': True
            }
        }]
    )

    print(f'{"ID":<2} {"Instance ID":<20} {"Name":<20} {"State":<15} {"Instance Type":<15} {"Public IPv4":<20}')
    for key, inst in enumerate(instance):
        inst.create_tags(Tags=[{'Key': 'Name', 'Value': instance_name}])
        inst.reload()
        public_ipv4 = inst.public_ip_address if inst.public_ip_address else "N/A"
        print(
            f'{key:<2} {inst.id:<20} {instance_name:<20} {inst.state["Name"]:<15} {inst.instance_type:<15} {public_ipv4:<20}')


def copy_ec2_instance_ip():
    retrieve_ec2_instances()
    choice = int(input("Enter instance ID to copy its ip address: "))
    ip = final_instances[choice][2]
    pyperclip.copy(ip)
    print(f"\n Address: {ip} copied to clipboard successfully")


def stop_ec2_instance():
    retrieve_ec2_instances()
    instances = [final_instances[i][0] for i in map(int, input(
        "\nEnter the instance ID(s) to Stop: ").replace(',', ' ').split()) if final_instances[i][0]]
    ec2 = boto3.client('ec2')
    ec2.stop_instances(InstanceIds=instances)
    print(f'\nStopped EC2 Instance(s): {", ".join(instances)}')


def start_ec2_instance():
    retrieve_ec2_instances()
    instances = [final_instances[i][0] for i in map(int, input(
        "\nEnter the instance ID(s) to Start: ").replace(',', ' ').split()) if final_instances[i][0]]
    ec2 = boto3.client('ec2')
    ec2.start_instances(InstanceIds=instances)
    print(f'\nStarted EC2 Instance(s): {", ".join(instances)}')


def delete_ec2_instance():
    retrieve_ec2_instances()
    instances = [final_instances[i][0] for i in map(int, input(
        "\nEnter the instance ID(s) to Delete: ").replace(',', ' ').split()) if final_instances[i][0]]
    ec2 = boto3.client('ec2')
    ec2.terminate_instances(InstanceIds=instances)
    print(f'\nDeleted EC2 Instance(s): {", ".join(instances)}')


def ssh_ec2_instance():
    retrieve_ec2_instances()
    choice = int(input("Enter instance ID to create ssh: "))
    ip = final_instances[choice][2]
    os.system(f"ssh ubuntu@{ip}")


# Instruction Message
message = """
EC2 Management Script Usage:
----------------------------
Commands:
- show, list, retrieve, all   : List all EC2 instances with details (ID, Name, State, Instance Type, Public IP)
- copy                        : Copy the public IP of a specific EC2 instance to the clipboard
- create, make                : Create a new EC2 instance with custom configurations (Name, Instance Type, Key Pair, Firewall, etc.)
- stop                        : Stop one or more EC2 instances by ID (comma/space separated)
- start                       : Start one or more EC2 instances by ID (comma/space separated)
- delete, del                 : Terminate one or more EC2 instances by ID (comma/space separated)
- ssh                         : Connects ssh to the instance

Usage:
- ec2 <command>
"""

if len(sys.argv) == 1:
    print(message)
elif len(sys.argv) == 2:
    command = sys.argv[1].lower()
    if command in ['show', 'list', 'retrieve', 'all']:
        retrieve_ec2_instances()
    elif command == 'copy':
        copy_ec2_instance_ip()
    elif command in ['create', 'make']:
        create_ec2_instance()
    elif command == 'stop':
        stop_ec2_instance()
    elif command == 'start':
        start_ec2_instance()
    elif command in ['delete', 'del']:
        delete_ec2_instance()
    elif command in ['ssh', 'shell']:
        ssh_ec2_instance()
    else:
        print('Invalid command given. Please refer to the instructions below:')
        print(message)
else:
    print("Invalid number of arguments. Please refer to the instructions below:")
    print(message)
