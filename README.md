# ECSpander
Increase ECS cluster ASG size in when short on available resources.

ECS is great in many ways, but it falls short in many others.  While using ECS for production workloads, we found that there were cases in which CloudWatch thresholds would not be met (so no alarms), but the cluster did not have sufficient capacity for a task.  For example, if you have only two nodes in your cluster, each with 1GB of memory free, and you need to run a task that requires 768MB of memory, your task will just sit waiting for resources to show up.  No CloudWatch alarms would trigger, unless you make sure that you always over-provision your cluster (which was AWS' advice when asked about this limitation).

ECSpander runs in a small container in your cluster, and checks the state of each service configured within it.  When it detects that a service fails to start due to lack of memory/CPU, it will look up the ASG of your ECS cluster, and increase it by 1.  It will do this at a frequency (defaults to 60s) to ensure that no container is left behind.

More documention is to come soon, but getting this setup is fairly straightforward.

Variables to set:
`AWS_REGION` (defaults to `us-east-1`)
`ECS_CLUSTER_NAME` (defaults to `default`)
`RESOURCE_CHECK_INTERVAL` (defaults to 60s)
