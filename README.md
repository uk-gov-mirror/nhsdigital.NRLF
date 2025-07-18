# NRLF

## Overview

This project has been given the name `nrlf` which stands for `National Records Locator (Futures)` as a replacement of the existing NRL.

This project uses the `Makefile` to build, test and deploy. This will ensure that a developer can reproduce any operation that the CI/CD pipelines does, meaning they can test the application locally or on their own deployed dev environment.

## Table of Contents

- [Before You Begin](#before-you-begin)
- [Getting Started](#getting-started)
- [Deploying](#deploying)
- [Feature Tests](#feature-tests)
- [OAuth Tokens for API request](#oauth-tokens-for-api-requests)
- [Route53 & Hosted Zones](#route53--hosted-zones)
- [Sandbox](#sandbox)
- [Releases](#releases)
- [Reports](#reports)

## Before You Begin

Before you start using this repository, you will need to:

- Follow the instructions on the [Developer Onboarding Guide](https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?spaceKey=CLP&title=NRLF+-+Developer+Onboarding) in confluence
- Install `asdf` using https://asdf-vm.com/guide/getting-started.html

Confirm `asdf` is installed and is working with:

```
asdf --version
```

Then install all the dependency packages with:

```
make configure
```

## Getting Started

To build packages:

```
make
```

To run the linters over your changes:

```
make lint
```

To run the unit tests:

```
make test
```

To run the local feature tests:

```
make test-features
```

### Troubleshooting

To check your environment:

```
make check
```

this will provide a report of the dependencies in your environment and should highlight the things that are not configured correctly or things that are missing.

### Integration testing

For the integration tests, you need to have deployed your infrastructure (using Terraform).

To run integration tests:

```
make test-integration
```

To run the Firehose integration tests:

```
make test-firehose-integration
```

To run all the feature integration tests:

```
make test-features-integration
```

To run indivudal feature test scenario(s) using the custom tag :

1. Add `@custom_tag` before each 'Scenario' that needs to be run (in each .feature file)
2. Run the command below:

```
make integration-test-with-custom_tag
```

To run all the feature integration tests and generate an interactive Allure report therafter :

```
make test-features-integration-report
```

### Smoke testing

For smoke tests, you need to have deployed your infrastructure (using Terraform).

Before the first run of the smoke tests, you need to set the required permissions in your deployment. You can do this by running:

```
make set-smoketest-perms
```

To run the internal smoke tests against your stack, do this:

```
make test-smoke-internal
```

To run the smoke tests against the public access endpoints (via APIGEE proxies), do this:

```
make test-smoke-public
```

## API Documentation

If the API changes, the API documentation needs to be updated in the appropriate API repo. This is done by making changes to the API specification `.yaml` files in each repo.

For Consumer API changes, update [NRL Consumer API - consumer.yaml](https://github.com/NHSDigital/nrl-consumer-api/blob/master/specification/record-locator/consumer.yaml)

For Producer API changes, update [NRL Producer API - producer.yaml](https://github.com/NHSDigital/nrl-producer-api/blob/master/specification/record-locator/producer.yaml)

Changes to the files in those repos will be reflected when each one is released. See the documentation in each repo for this process.

## Deploying

The NRLF is deployed using terraform. The infrastructure is split into two parts.

All account wide resources like Route 53 hosted zones or IAM roles are found in `terraform/account-wide-infrastructure`

All resources that are not account specific (lambdas, API gateways etc) can be found in `terraform/infrastructure`

Information on deploying these two parts:

- [NRLF main infrastructure](./terraform/infrastructure/README.md)
- [NRLF account wide infrastructure](./terraform/account-wide-infrastructure/README.md)

## Feature tests

Referring to the sample feature test below:

```gherkin
Scenario: Successfully create a Document Pointer of type Mental health crisis plan
   Given {ACTOR TYPE} "{ACTOR}" (Organisation ID "{ORG_ID}") is requesting to {ACTION} Document Pointers
   And {ACTOR TYPE} "{ACTOR}" is registered in the system for application "APP 1" (ID "{APP ID 1}") for document types
     | system                  | value     |
     | http://snomed.info/sct | 736253002 |
   And {ACTOR TYPE} "{ACTOR}" has authorisation headers for application "APP 2" (ID "{APP ID 2}")
   When {ACTOR TYPE} "{ACTOR}" {ACTION} a Document Reference from DOCUMENT template
     | property    | value                          |
     | identifier  | 1234567890                     |
     | type        | 736253002                      |
     | custodian   | {ORG_ID}                       |
     | subject     | 9278693472                     |
     | contentType | application/pdf                |
     | url         | https://example.org/my-doc.pdf |
   Then the operation is {RESULT}
```

The following notes should be made:

1. ACTOR TYPE, ACTOR and ACTION are forced
   to be consistent throughout your test
2. ACTOR TYPE, ACTOR, ACTION, ORG_ID, APP, APP ID, and
   RESULT are enums: their values are
   restricted to a predefined set
3. ACTOR is equivalent to to both custodian
   and organisation
4. The request method (GET, POST, ...) and
   slug (e.g. DocumentReference/\_search) for
   ACTION is taken from the swagger.
5. ”Given ... is requesting to” is mandatory:
   it sets up the base request
6. ”And ... is registered to” sets up a
   org:app:doc-types entry in Auth table
7. ”And ... has authorisation headers” sets up
   authorisation headers

## OAuth tokens for API requests

Clients must provide OAuth access tokens when making requests to the NRLF APIs.

To create an access token for the dev environment, you can do the following:

```
make get-access-token
```

To create an access token for another environment:

```
$ make ENV=[env-name] get-access-token
```

Valid `[env-name]` values are `dev`, `int`, `ref` and `prod` for each associated NRLF environment.

Once you have your access token, you provide it as a bearer token in your API requests using the `Authorization` header, like this:

```
Authorization: Bearer <token>
```

If you need to get an API token for the `nrl_sync` application, the command is:

```
$ make ENV=[env-name] APP_ALIAS=nrl_sync get-access-token
```

## Route53 & Hosted Zones

There are 2 parts to the Route53 configuration:

### 1. environment accounts

In `terraform/account-wide-infrastructure/prod/route53.tf`, we have a Hosted Zone:

```terraform
resource "aws_route53_zone" "dev-ns" {
  name = "dev.internal.record-locator.devspineservices.nhs.uk"
}
```

### 2. mgmt account

In `terraform/account-wide-infrastructure/mgmt/route53.tf` we have both a Hosted Zone and a Record per environment:

```terraform
resource "aws_route53_zone" "prodspine" {
  name = "record-locator.spineservices.nhs.uk"

  tags = {
    Environment = terraform.workspace
  }
}

resource "aws_route53_record" "prodspine" {
  zone_id = aws_route53_zone.prodspine.zone_id
  name    = "prod.internal.record-locator.spineservices.nhs.uk"
  records = ["ns-904.awsdns-49.net.",
    "ns-1539.awsdns-00.co.uk.",
    "ns-1398.awsdns-46.org.",
    "ns-300.awsdns-37.com."
  ]
  ttl  = 300
  type = "NS"
}
```

The `records` property is derived by first deploying to a specific environment, in this instance, production, and from the AWS Console navigating to the Route53 Hosted Zone that was just deployed and copying the "Value/Route traffic to" information into the `records` property. Finally, deploy to the mgmt account with the new information.

---

## Sandbox

The public-facing sandbox is an additional persistent workspace (`int-sandbox`) deployed in our INT (`int` / `test`) environment, alongside the persistent workspace named `ref`. It is identical to our live API, except it is open to the world via Apigee (which implements rate limiting on our behalf).

### Sandbox deployment

In order to deploy to a sandbox environment (`dev-sandbox`, `qa-sandbox`, `int-sandbox`) you should use the GitHub Action for persistent environments, where you should select the option to deploy to the sandbox workspace.

### Sandbox database clear and reseed

Any workspace suffixed with `-sandbox` has a small amount of additional infrastructure deployed to clear and reseed the DynamoDB tables (auth and document pointers) using a Lambda running
on a cron schedule that can be found in the `cron/seed_sandbox` directory in the root of this project. The data used to seed the DynamoDB tables can found in the `cron/seed_sandbox/data` directory.

### Sandbox authorisation

The configuration of organisations auth / permissions is dealt with in the "apigee" repos, i.e.

- https://github.com/NHSDigital/record-locator/producer
- https://github.com/NHSDigital/record-locator/consumer

Specifically, the configuration can be found in the file proxies/sandbox/apiproxy/resources/jsc/ConnectionMetadata.SetRequestHeaders.js in these repos.

💡 Developers should make sure that these align between the three repos according to any user journeys that they envisage.

Additionally, and less importantly, there are also fixed organization details in proxies/sandbox/apiproxy/resources/jsc/ClientRPDetailsHeader.SetRequestHeaders.js in these repos.

## Releases

The process to create a new release is as follows:

1. In [Github Releases](https://github.com/NHSDigital/NRLF/releases), press the "Draft new release" button.
2. Press "Choose a tag" and enter the version of the release, say `v3.0.1`. This will be the tag we use to release from.
3. Select `develop` for the release Target
4. Press "Generate release notes" button. This will populate the description with everything that's changed since the last release.
5. Enter the version of the release into the Release Title field, say `v3.0.1`
6. Arrange and update the description to accuruately represent the highlights of the release.
7. Make sure the "Set as a pre-release" checkbox it set
8. Press the "Publish release" button to complete the release process

Once your new release has been created, you can then deploy this release through the NRLF environments using the "Persistent Environment Deploy" Github Action. Once your release has been deployed to prod, edit the release and set the "Set as the latest release" checkbox.

If the Consumer API has changed, or the documentation for that API has changed, you will also need to release [NRL Consumer API](https://github.com/NHSDigital/nrl-consumer-api).

If the Producer API has changed, or the documentation for that API has changed, you will also need to release [NRL Producer API](https://github.com/NHSDigital/nrl-producer-api).

### Deploying releases

Once you have a new release version ready, you can deploy it through our environments as follows:

1. Use the "Persistent Environment Deploy" Github Action workflow to deploy the release tag to `dev`, `dev-sandbox`, `qa`, `qa-sandbox`, `int` and `int-sandbox` environments.
2. If any issues arise in the deployment, fix the issues, create a new release version and start this process again.
3. Once the deployments are complete, use the "Persistent Environment Deploy" Github Action workflow to deploy the release version to `ref`.
4. Once that is complete, use the "Persistent Environment Deploy" workflow to deploy the release version to `prod`.

## Reports

Reports are provided as scripts in the `reports/` directory. To run a report:

1. Login to your AWS account on the command line, choosing the account that contains the resources you want to report on.
2. Run your chosen report script, giving the script the resource names and parameters it requires. See each report script for details.

For example, to count the number of pointers from X26 in the pointers table in the dev environment:

```
$ poetry run python ./scripts/count_pointers_for_custodian.py \
   nhsd-nrlf--dev-pointers-table \
   X26
```

### Running reports in the prod environment

The reports scripts may require resources that could affect the performance of the live production system. Because of this, it is recommended that you take steps to minimise this impact before running reports.

If you are running a report against the DynamoDB pointers table in prod, you should create a copy (or restore a PITR backup) of the table and run your report against the copy.

Please ensure any duplicated resource/data is deleted from the prod environment once you have finished using it.
