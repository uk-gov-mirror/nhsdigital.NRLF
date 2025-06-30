# NRLF Account Wide Infrastructure

This directory contains terraform for resources which are global to a given account instead of a workspace. Resources can include but not limited to: User assume IAM roles, Route 53 DNS setup and API gateway cloudwatch roles etc.

Each subdirectory corresponds to each AWS account (`mgmt`, `prod`, `test` and `dev`).

**Account wide resources should be deployed manually and not be run as part of CI.**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initialise shell environment](#initialise-shell-environment)
3. [Deploy account wide resources](#deploy-account-wide-resources)
4. [Tear down account wide resources](#tear-down-account-wide-resources)

## Prerequisites

Before deploying the NRLF account-wide infrastructure, you will need:

- AWS accounts that have already been bootstrapped, as described in [bootstrap/README.md](../bootstrap/README.md). This is a one-time account setup step.
- The required packages to build NRLF, see [the Setup section in README.md](../../README.md#setup).

## Deploy mgmt resources

To deploy resources into the mgmt account, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace with:

```shell
cd mgmt
terraform init && terraform workspace select mgmt
```

Once you have your workspace, you can plan your change with:

```shell
terraform plan
```

Once you're happy with your planned changes, you can apply them with:

```shell
terraform apply
```

### If you get "Error: creating CodeBuild Webhook"

If you see this erro:

```
│ Error: creating CodeBuild Webhook (nhsd-nrlf-ci-build-project): operation error CodeBuild: CreateWebhook, https response error StatusCode: 400, RequestID: , ResourceNotFoundException: Access token not found in CodeBuild project for server type github
│
│   with aws_codebuild_webhook.github_workflow,
│   on codebuild.tf line 113, in resource "aws_codebuild_webhook" "github_workflow":
│  113: resource "aws_codebuild_webhook" "github_workflow" {
```

You will need to add the Github PAT credential for codebuild to connect to Github. To fix this:

1. Go to the AWS console and find the Codebuild service
2. Select the created nhsd-nrlf-ci-build-project project
3. Press the "Edit" button (in the top-bar)
4. Where it says "You have not connected to Github", press the "Manage account credentials" link
5. At the "Manage default source credential" page, choose "Personal Access Token" type, "Secrets Manager" service, and "Existing Secret" secret.
6. In the "Connection" drop-down, choose the "nhsd-nrlf--codebuild-github-pat" secret
7. Press the "Save" button

If that has worked, you should see: "Your account is successfully connected through Secrets Manager secret"

### Build and publish the container image for CI build

Once all the mgmt infra has been deployed, you need to build and publish the CI image to the ECR repo.

To do this, first build the image as follows:

```
make build-ci-image
```

and then login to ECR:

```
make ecr-login
```

and push the image:

```
make publish-ci-image
```

## Deploy account wide resources

To deploy the account wide resources, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace with:

```shell
$ cd ACCOUNT_NAME
$ terraform init && ( \
    terraform workspace new ACCOUNT_NAME || \
    terraform workspace select ACCOUNT_NAME )
```

Replacing ACCOUNT_NAME with the name of your account, e.g `dev`, `test` etc.

Once you have your workspace, you can plan your changes with:

```shell
$ terraform plan \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing AWS_ACCOUNT_ID with the AWS account number of your account.

Once you're happy with your planned changes, you can apply them with:

```shell
$ terraform apply \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing AWS_ACCOUNT_ID with the AWS account number of your account.

### Reporting Resources

To enable reporting resources for the account, do the following:

1. Set the `enable_reporting` variable to `true` in `./ACCOUNT_NAME/vars.tf`
2. Deploy the account-wide infrastructure to the account

To disable reporting resources for the account, do the following:

1. Set the `enable_reporting` variable to `true` in `./ACCOUNT_NAME/vars.tf`
2. Deploy the account-wide infrastructure to the account

#### Deploying the PowerBI Gateway

The first time you deploy the PowerBI Gateway set up to a new account, these steps need to be followed:

1. Set the `enable_powerbi_auto_push` variable to `true` in `./ACCOUNT_NAME/vars.tf`
2. Set the `use_powerbi_gw_custom_ami` variable to `false` in `./ACCOUNT_NAME/vars.tf`
3. Deploy the account-wide infrastructure for the account
4. Run the below CLI command, and RDP into the newly created EC2 instance (localhost:13389)

```
aws ssm start-session --target <AMI> --document-name AWS-StartPortForwardingSession --parameters "localPortNumber=13389,portNumber=3389"
```

5. Install Athena ODBC driver and Power BI standard on premises gateway
6. Configure ODBC driver to connect to relevant Athena instance
7. Log in to the gateway using NHS email, name the cluster to nhsd-nrlf-{env}--reporting-gw
8. Log on to power bi, navigate to Manage Connections and Gateways in settings and set up Athena connector with authentication method: Anonymous and privacy level: Private
9. Set dataset to point to this gateway, define schedule as needed
10. In the AWS Console, create an AMI from the instance called `PowerBI_GW`
11. Set the `use_powerbi_gw_custom_ami` variable to `true`
12. Deploy the account-wide infrastructure for the account
13. Run the below CLI command, and RDP into the newly created EC2 instance (localhost:13389)

```
aws ssm start-session --target <AMI> --document-name AWS-StartPortForwardingSession --parameters "localPortNumber=13389,portNumber=3389"
```

14. Start the PowerBI Gateway service on the instance

To disable the PowerBI Gateway from the account:

1. Set the `enable_powerbi_auto_push` variable to `false` in `./ACCOUNT_NAME/vars.tf`
2. Deploy the account-wide infrastructure to the account

## Tear down account wide resources

WARNING - This action will destroy all account-wide resources from the AWS account. This should
only be done if you are sure that this is safe and are sure that you are signed into the correct
AWS account.

To tear down account-wide resources, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace with:

```shell
$ cd ACCOUNT_NAME
$ terraform init && ( \
    terraform workspace new ACCOUNT_NAME || \
    terraform workspace select ACCOUNT_NAME )
```

And then, to tear down:

```shell
$ terraform destroy \
    -var 'assume_account=AWS_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```
