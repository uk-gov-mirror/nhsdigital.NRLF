# NRLF AWS Bastion Infrastructure

This directory contains the infrastructure for the NRLF AWS Bastion. This is a host that is deployed into the NRLF AWS accounts and can be used to run operations tasks against the resources in that account. For example, to run a report that reads from the DynamoDB pointers table.

## Prerequisites

Before deploying a bastion, you will need:

- An AWS account that has already been bootstrapped, as described in [bootstrap/README.md](../bootstrap/README.md) and has the account-wide infrastructure deployed as described in [account-wide-infrastructure/README.md](../account-wide-infrastructure/README.md). This is a one-time account setup step.
- Your CLI configured to allow authentication to your AWS account

## Deploying a bastion

The bastions are emphemeral resources that should be deploy when you need them.

To deploy a bastion, you will first need to login to the AWS mgmt account on the CLI.

Then, initialise the Terraform workspace with:

```
terraform init
```

If you want a read-only bastion (can only READ from the pointers table), plan the deployment like this:

```
make plan-ro
```

If you want a read-write bastion (can READ and WRITE from the pointers table), plan the deployment like this:

```
make plan-rw
```

Once you're happy with your planned changes, you can apply them with:

```
terraform apply ./bastion.tfplan
```

## Using the bastion

Once the bastion is deployed, you can connect to it via SSH with:

```
make ssh-connection
```
