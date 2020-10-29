# ECSpander
Increase ECS cluster ASG size in when short on available resources.

ECS is great in many ways, but it falls short in many others.  While using ECS for production workloads, we found that there were cases in which CloudWatch thresholds would not be met (so no alarms), but the cluster did not have sufficient capacity for a task.  For example, if you have only two nodes in your cluster, each with 1GB of memory free, and you need to run a task that requires 768MB of memory, your task will just sit waiting for resources to show up.  No CloudWatch alarms would trigger, unless you make sure that you always over-provision your cluster (which was AWS' advice when asked about this limitation).

ECSpander runs in a small container in your cluster, and checks the state of each service configured within it.  When it detects that a service fails to start due to lack of memory/CPU, it will look up the ASG of your ECS cluster, and increase it by 1.  It will do this at a frequency (defaults to 60s) to ensure that no container is left behind.

More documention is to come soon, but getting this setup is fairly straightforward.

## Variables to set

|Variable|Description|Default|
|---|---|---|
|`AWS_REGION`|AWS region where ECS cluster resides|`us-east-1`|
|`ECS_CLUSTER_NAME`|Name of ECS cluster to poll|`default`|
|`RESOURCE_CHECK_INTERVAL`|How often to poll ECS cluster (in seconds)|`60`|

## Sample CloudFormation template

```
  EcspanderIamRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
        - Effect: Allow
          Principal:
            Service:
            - ecs-tasks.amazonaws.com
          Action:
          - sts:AssumeRole
      Policies:
      - PolicyName: ClusterInstancePolicy
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
          - Effect: Allow
            Action:
            - ec2:List*
            - ec2:Describe*
            - ecs:List*
            - ecs:Describe*
            - autoscaling:List*
            - autoscaling:Describe*
            Resource: "*"
          - Effect: Allow
            Action:
            - autoscaling:Update*
            Resource: !Sub arn:aws:autoscaling:${AWS::Region}:${AWS::AccountId}:autoScalingGroup:*:autoScalingGroupName/${AutoScalingGroup}

  EcspanderTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      TaskRoleArn: !Ref EcspanderIamRole
      ContainerDefinitions:
      - Name: ecspander-ecs-cluster-production
        Image: ameir/ecspander:latest
        Cpu: '64'
        Memory: '128'
        Environment:
        - Name: AWS_REGION
          Value: !Ref AWS::Region
        - Name: ECS_CLUSTER_NAME
          Value: !Ref EcsCluster
        Essential: true
        LogConfiguration:
          LogDriver: awslogs
          Options:
            awslogs-region: !Ref AWS::Region
            awslogs-group: !Ref LogGroup
            awslogs-stream-prefix: !Ref AWS::StackName

  EcspanderEcsService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref EcsCluster
      TaskDefinition: !Ref EcspanderTaskDefinition
      DesiredCount: 1
      DeploymentConfiguration:
        MaximumPercent: 100
        MinimumHealthyPercent: 0

```

## Contributions and issues
Nothing special to it; submit a pull request or file a GitHub issue and I'll check it out when I can.
