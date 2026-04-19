# AWS CLI Integration

Manage cloud infrastructure, inspect resources, and deploy from any LLM agent.

---

## Install

- **macOS:** `brew install awscli`
- **Windows:** `winget install --id Amazon.AWSCLI`
- **Linux:** See [docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

Verify: `aws --version`

## Configure

```bash
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Default region, Output format (json)
```

Or use SSO:
```bash
aws configure sso
aws sso login --profile <profile-name>
```

### Multiple Profiles

```bash
# Set up named profiles
aws configure --profile staging
aws configure --profile production

# Use a profile
aws s3 ls --profile staging

# Or set as default for the session
export AWS_PROFILE=staging
```

---

## Common Commands by Service

### EC2 (Compute)

```bash
# List instances
aws ec2 describe-instances --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,Type:InstanceType,Name:Tags[?Key=='Name']|[0].Value}" --output table

# Start/stop instance
aws ec2 start-instances --instance-ids i-1234567890abcdef0
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
```

### S3 (Storage)

```bash
# List buckets
aws s3 ls

# List objects in a bucket
aws s3 ls s3://bucket-name/prefix/

# Copy files
aws s3 cp local-file.txt s3://bucket-name/path/
aws s3 sync ./local-dir s3://bucket-name/path/
```

### ECS / EKS (Containers)

```bash
# List ECS clusters
aws ecs list-clusters

# List services in a cluster
aws ecs list-services --cluster my-cluster

# Describe a service
aws ecs describe-services --cluster my-cluster --services my-service

# List EKS clusters
aws eks list-clusters

# Get kubeconfig
aws eks update-kubeconfig --name my-cluster --region us-east-1
```

### CloudWatch (Logs & Monitoring)

```bash
# List log groups
aws logs describe-log-groups --query "logGroups[].logGroupName"

# Tail logs
aws logs tail /ecs/my-service --follow --since 1h

# Get recent log events
aws logs get-log-events --log-group-name /ecs/my-service --log-stream-name <stream>
```

### Secrets Manager

```bash
# List secrets
aws secretsmanager list-secrets --query "SecretList[].Name"

# Get a secret value
aws secretsmanager get-secret-value --secret-id my-secret --query SecretString --output text
```

### RDS (Databases)

```bash
# List DB instances
aws rds describe-db-instances --query "DBInstances[].{ID:DBInstanceIdentifier,Engine:Engine,Status:DBInstanceStatus}" --output table

# Get connection endpoint
aws rds describe-db-instances --db-instance-identifier my-db --query "DBInstances[0].Endpoint"
```

### Lambda (Serverless)

```bash
# List functions
aws lambda list-functions --query "Functions[].FunctionName"

# Invoke a function
aws lambda invoke --function-name my-function --payload '{"key": "value"}' output.json

# View recent invocations
aws logs tail /aws/lambda/my-function --since 1h
```

---

## Safety Rules

- **Never run destructive commands automatically** — deleting resources, modifying security groups, changing IAM policies.
- **Always use `--dry-run`** when available for destructive operations.
- **Use `--output json`** for structured output the agent can parse.
- **Use `--query`** (JMESPath) to filter output and reduce context size.
- **Never expose AWS credentials** — use environment variables, profiles, or IAM roles.
- **Production operations require explicit user approval.**

---

## How Workflows Use AWS

- **infra-deployment** — inspect and manage infrastructure
- **project-discovery** — understand the deployment architecture
- **troubleshooting** — read logs, check service health, inspect resources

---

## Tips

- **Use `--output table`** for human-readable output, `--output json` for agent parsing.
- **Use `--query`** to filter large responses down to relevant fields.
- **Named profiles** keep environments separated and prevent accidental production changes.
- **SSO** is preferred over long-lived access keys.
