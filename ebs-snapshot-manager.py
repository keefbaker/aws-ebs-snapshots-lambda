"""
Deletes snapshots with todays date tagged
"""
import datetime
import boto3

ec = boto3.client('ec2')

def lambda_handler(event, context):
    delete_on = datetime.date.today().strftime('%Y-%m-%d')

    filters = [
        {'Name': 'tag:DeleteOn', 'Values': [delete_on]},
        {'Name': 'tag:Type', 'Values': ['Automated']},
    ]

    snapshot_response = ec.describe_snapshots(Filters=filters)

    for snap in snapshot_response['Snapshots']:
        print "Deleting snapshot %s" % snap['SnapshotId']

        ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
