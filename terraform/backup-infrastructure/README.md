# NRLF Backup Infrastructure

This directory contains AWS backup terraform resources which are global to a given account.

Each subdirectory corresponds to each AWS account (`prod` and `test`).

**Backup infrastructure is deployed manually and not run as part of CI.**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backup account pairings](#backup-account-pairings)
3. [Deploy backup resources](#deploy-backup-resources)
4. [Tear down backup resources](#tear-down-backup-resources)

## Prerequisites

Before deploying the NRLF backup infrastructure, you will need:

- An AWS backup account that have already been bootstrapped, as described in [bootstrap/README.md](../bootstrap/README.md). This is a one-time account setup step.

## Backup account pairings

Each account sends immutable copies of its backups to a corresponding backup account

| SOURCE_ACCOUNT | BACKUP_ACCOUNT |
| -------------- | -------------- |
| TEST           | TEST BACKUP    |
| PROD           | PROD BACKUP    |

where SOURCE_ACCOUNT is the account that will be sending backups and BACKUP_ACCOUNT is the corresponding backup account.

We might use SOURCE_ACCOUNT=DEV BACKUP_ACCOUNT=TEST BACKUP to prove out changes in development, but always set it back to the above.

## Deploy backup resources

To deploy the backup resources, first login to the AWS mgmt account on the CLI.

Then, initialise the terraform backup workspace. For the test account:

```shell
$ cd test
$ terraform init && ( \
    terraform workspace new test || \
    terraform workspace select test )
```

If you want to apply changes to prod, use the `prod` directory and the `prod` terraform workspace and assume the admin role on the mgmt account.

Once you have your workspace set, you can plan your changes with:

```shell
$ terraform plan \
    -var 'source_account_id=SOURCE_ACCOUNT_ID' \
    -var 'assume_account=BACKUP_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing SOURCE_ACCOUNT_ID with the account id that will be sending backups and BACKUP_ACCOUNT_ID with the account id of the [corresponding backup account](#backup-account-pairings).

Once you're happy with your planned changes, you can apply them with:

```shell
$ terraform apply \
    -var 'source_account_id=SOURCE_ACCOUNT_ID' \
    -var 'assume_account=BACKUP_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing SOURCE_ACCOUNT_ID with the account id that will be sending backups and BACKUP_ACCOUNT_ID with the account id of the [corresponding backup account](#backup-account-pairings).

> Record the plan/apply output somewhere for posterity e.g. the release ticket. When deploying backup-infra changes to prod, you'd want to be able to compare the plan output to that of the test account.

## Tear down backup resources

WARNING - This action will destroy all backup resources from the AWS account. This should
only be done if you are sure that this is safe and are sure that you are signed into the correct
AWS account.

To tear down backup resources, first login to the AWS mgmt account on the CLI.

Then, initialise your terraform workspace. For the test account:

```shell
$ cd test
$ terraform init && ( \
    terraform workspace new test || \
    terraform workspace select test )
```

If you want to destroy resources in prod, use the `prod` directory and the `prod` terraform workspace and assume the admin role on the mgmt account.

And then, to tear down:

```shell
$ terraform destroy \
    -var 'source_account_id=SOURCE_ACCOUNT_ID' \
    -var 'assume_account=BACKUP_ACCOUNT_ID' \
    -var 'assume_role=terraform'
```

Replacing SOURCE_ACCOUNT_ID with the account id that will be sending backups and BACKUP_ACCOUNT_ID with the account id of the [corresponding backup account](#backup-account-pairings).
