#!/usr/bin/env python3

# https://aws.amazon.com/blogs/compute/how-to-create-a-custom-scheduler-for-amazon-ecs/

from datetime import datetime, timezone
import boto3
import argparse
import logging
import pprint
import sys
import os
import time

# Set up logger
logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
pp = pprint.PrettyPrinter(indent=4)

# Set up boto client
ecs = boto3.client('ecs')
ec2 = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')


def listServices(clusterName):
    response = ecs.list_services(cluster=clusterName)
    serviceArns = response['serviceArns']

    return serviceArns


def describeServices(clusterName, serviceArns):

    for serviceArn in serviceArns:
        logging.info("Evaluating service ARN: {}".format(serviceArn))

        response = ecs.describe_services(
            cluster=clusterName, services=[serviceArn]
        )

        deployments = response['services'][0]['deployments']
        desiredCount = deployments[0]['desiredCount']
        runningCount = deployments[0]['runningCount']

        if desiredCount > runningCount:
            logging.warn("desiredCount ({}) greater than runningCount ({})!".format(
                desiredCount, runningCount))
            lastEvent = response['services'][0]['events'][0]['message']
            if 'insufficient' in lastEvent:
                logging.warn("Service %s has insufficient resources: \n%s",
                             serviceArn, lastEvent)
                addNode(clusterName)
        elif len(deployments) > 1 and deployments[0]['status'] == 'PRIMARY':
            timedelta = (datetime.now(timezone.utc) -
                         deployments[0]['createdAt']).seconds
            if timedelta > 60:
                logging.warn("Deployment has been waiting for %ds.", timedelta)


def addNode(clusterName):

    logging.info("Adding node to cluster %s.", clusterName)
    # add node to cluster
    instanceArns = getInstanceArns(clusterName)
    instanceArn = instanceArns[0]  # we only need one for this

    response = ecs.describe_container_instances(
        cluster=clusterName,
        containerInstances=[instanceArn]
    )

    instanceId = response['containerInstances'][0]['ec2InstanceId']
    logging.info("instanceId is {}".format(instanceId))
    response = autoscaling.describe_auto_scaling_instances(
        InstanceIds=[instanceId]
    )

    autoScalingGroupName = response['AutoScalingInstances'][0]['AutoScalingGroupName']
    logging.info("AutoScalingGroupName is {}".format(
        autoScalingGroupName))
    response = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[autoScalingGroupName]
    )

    defaultCooldown = response['AutoScalingGroups'][0]['DefaultCooldown']
    desiredCapacity = response['AutoScalingGroups'][0]['DesiredCapacity']
    maxSize = response['AutoScalingGroups'][0]['MaxSize']
    newDesiredCapacity = desiredCapacity + 1
    if newDesiredCapacity > maxSize:
        logging.warn("New DesiredCapacity (%d) is greater than MaxSize (%d)!",
                     newDesiredCapacity, maxSize)
        time.sleep(120)
        return False
    logging.info("AutoScalingGroupName %s - desiredCapacity is %d, maxSize is %d. Increasing desiredCapacity to %d.",
                 autoScalingGroupName, desiredCapacity, maxSize, newDesiredCapacity)
    response = autoscaling.update_auto_scaling_group(
        AutoScalingGroupName=autoScalingGroupName,
        DesiredCapacity=newDesiredCapacity
    )
    logging.info(
        "boto3 doesn't support waits for ASGs, so let's sleep for cooldown period (%ss).", defaultCooldown)
    time.sleep(int(defaultCooldown))


def getInstanceArns(clusterName):
    # Get instances in the cluster
    response = ecs.list_container_instances(cluster=clusterName)
    containerInstancesArns = response['containerInstanceArns']
    # If there are more instances, keep retrieving them
    while response.get('nextToken', None) is not None:
        response = ecs.list_container_instances(
            cluster=clusterName,
            nextToken=response['nextToken']
        )
        containerInstancesArns.extend(response['containerInstanceArns'])

    return containerInstancesArns


def main():
    parser = argparse.ArgumentParser(
        description='ECS monitor that scales container instances if there is not enough capacity.'
    )
    parser.add_argument(
        '-c', '--cluster',
        default='default',
        help='The short name or full Amazon Resource Name (ARN) of the cluster that you want to monitor. If you do not specify a cluster, the default cluster is assumed.'
    )
    args = parser.parse_args()

    sleep = os.getenv('RESOURCE_CHECK_INTERVAL', 60)
    while True:
        serviceArns = listServices(args.cluster)
        describeServices(args.cluster, serviceArns)
        logging.info("Sleeping for {}s...".format(sleep))
        time.sleep(int(sleep))


if __name__ == "__main__":
    main()
