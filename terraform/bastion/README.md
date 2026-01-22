# NRLF AWS Bastion Infrastructure

This directory contains the infrastructure for the NRLF AWS Bastion. This is a host that is deployed into the NRLF AWS accounts and can be used to run operations tasks against the resources in that account. For example, to run a report that reads from the DynamoDB pointers table.

## Prerequisites

Before deploying a bastion, you will need:

- An AWS account that has already been bootstrapped, as described in [bootstrap/README.md](../bootstrap/README.md) and has the account-wide infrastructure deployed as described in [account-wide-infrastructure/README.md](../account-wide-infrastructure/README.md). This is a one-time account setup step.
- Your CLI configured to allow authentication to your AWS account
- Install the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

## Deploying a bastion

The bastions are emphemeral resources that should be deploy when you need them.

To deploy a bastion, you will first need to login to the AWS mgmt account on the CLI.

Then, initialise the Terraform workspace with:

```sh
assume nhsd-nrlf-mgmt
terraform init
```

If you want a read-only bastion (can only READ from the pointers table), plan the deployment like this:

```sh
make plan-ro
```

If you want a read-write bastion (can READ and WRITE from the pointers table), plan the deployment like this:

```sh
make plan-rw
```

Once you're happy with your planned changes, you can apply them with:

```sh
terraform apply ./bastion.tfplan
```

## Using the bastion

Once the bastion is deployed, you can connect to it via SSH with:

```sh
assume nhsd-nrlf-test
make ssh-connection ENV={env}
```

Once connected successfully, you will be at the SSM `$` prompt. To switch to the `nrlf_ops` user, run this command:

```sh
sudo su - nrlf_ops
```

Once switched to the `nrlf_ops` user, you can use the bastion and the installed tooling:

- `cd ./NRLF` - the NRLF repo (cloned from Github `develop`)
- `aws`
- `git`
- `python` and `poetry`

see [user-data.sh](./scripts/user-data.sh) for exactly what's installed on there.

### Troubleshooting the bastion

#### I cannot connect to the bastion

If you're running the `make ssh-connection` and are seeing this error:

```sh
$ make ssh-connection
....
An error occurred (TargetNotConnected) when calling the StartSession operation: i-06ff25164f004bee4 is not connected.
make: *** [Makefile:54: ssh-connection] Error 254
$
```

If you've just created a new bastion, it may be that it hasn't started yet. Log in to the AWS console to see the state of the EC2 instance. Press the "Connect" button in the console and choose the SSM tab to see if things are working ok.

If there is a warning in the Session Manager tab "SSM Agent is not online" when you attempt to connect then it's likely the SSM agent has crashed. Reboot the EC2 instance and the SSM agent should start up with previous cli history preserved. To reboot via the CLI, find your EC2 instance > Instance state > Reboot instance. Beware: rebooting the EC2 instance will terminate any ongoing processes.

If the EC2 instance is running and the console looks ok, check you have defined the correct ENV param for the installed bastion.

#### The `nrlf_ops` using is missing

If you're getting this error:

```sh
$ sudo su - nrlf_ops
su: user some_other does not exist or the user entry does not contain all the required fields
$
```

If you've just created a new bastion, you may need to wait a little until the cloud-init script has finished. You can check the status of this process with:

```sh
sudo tail -f /var/log/cloud-init-output.log
```

#### The bastion cannot access an AWS resource that I want to use

If you're trying to access an AWS resource from the bastion and are getting an access denied error, it may be that the bastion's IAM role does not have the required permissions.

You can check the role in the AWS console to work out if things are missing and can edit it there too for immediate access to the resources you need.

If you want to permanently grant new access to the bastion, you can add a policy and attach it to the EC2 instance in [iam.tf](iam.tf)

#### A tool I need is missing

If there's a tool missing from the instance, you can add it using `apt` or via `asdf` as/when you need it.

If you want a new tool to be deployed onto all bastions in the future too, add it to the [user-data.sh](./scripts/user-data.sh) script.
