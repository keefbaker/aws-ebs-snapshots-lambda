"""
To use tag instances with Backup: true

To change region,
"""
from __future__ import print_function
import os
import collections
import datetime
import boto3

#region = os.environ.get("AWS_REGION", "eu-west-1")

ec = boto3.client('ec2')

def instance_names(instance):
    for tag in instance['Tags']:
        if tag['Key'] == 'Name':
            i_name = tag['Value']
            break
    else:
        i_name = ""
    return i_name


def device_process(dev, to_tag, instance, retention_days):
    if dev.get('Ebs', None) is None:
        return to_tag
    vol_id = dev['Ebs']['VolumeId']
    dev_name = dev['DeviceName']
    instance_name = instance_names(instance)
    description = '%s - %s (%s)' % (instance_name, vol_id, dev_name)

    snap = ec.create_snapshot(
        VolumeId=vol_id,
        Description=description
        )

    if snap:
        print("Snapshot {} of [{}]".format(snap['SnapshotId'], description))
    to_tag[retention_days].append(snap['SnapshotId'])
    return to_tag

def instance_process(instance, to_tag):
    try:
        retention_days = [
            int(tag.get('Value')) \
            for tag in instance['Tags']
            if tag['Key'] == 'Retention'
            ][0]
    except IndexError:
        retention_days = 7

    for dev in instance['BlockDeviceMappings']:
        to_tag = device_process(dev, to_tag, instance, retention_days)
    return to_tag

def instance_loop(instances):
    to_tag = collections.defaultdict(list)

    for instance in instances:
        to_tag = instance_process(instance, to_tag)
    return to_tag

def tag_snapshots(retention_days, to_tag):
    delete_date = datetime.date.today() + datetime.timedelta(
        days=retention_days
        )
    delete_fmt = delete_date.strftime('%Y-%m-%d')
    print("Will delete {} snapshots on {}".format(
        len(to_tag[retention_days]),
        delete_fmt))
    ec.create_tags(
        Resources=to_tag[retention_days],
        Tags=[
            {'Key': 'DeleteOn', 'Value': delete_fmt},
            {'Key': 'Type', 'Value': 'Automated'},
        ]
    )

def lambda_handler(*args):
    reservations = ec.describe_instances(
        Filters=[
            {
                'Name': 'tag:Backup',
                'Values': ['true']
            },
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [instance for instance in reservation['Instances']]
            for reservation in reservations
        ], [])
    print("Found {} instances that need backing up".format(len(instances)))

    to_tag = instance_loop(instances)
    for retention_days in to_tag.keys():
        tag_snapshots(retention_days, to_tag)


if __name__ == "__main__":
    lambda_handler("hello", "world")
