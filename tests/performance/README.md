# Performance Testing

We have performance tests which give us a benchmark of how NRLF performs under load for consumers and producers.

## Run performance tests

### Prep the environment

Perf tests are generally conducted in the perftest env. There's a selection of tables in the perftest env representing different pointer volume scenarios e.g. perftest-baseline vs perftest-1million (todo: update with real names!).

#### Pull certs for perftest

```sh
assume nhsd-nrlf-mgmt
make truststore-pull-all ENV=perftest
```

#### Point perftest at a different pointers table

We (will) have multiple tables representing different states of NRLF in the future e.g. all patients receiving an IPS (International Patient Summary), onboarding particular high-volume suppliers.

In order to run performance tests to get figures for these different states, we can point the perftest environment at one of these tables.

Currently, this requires tearing down the existing environment and restoring from scratch:

1. Follow instructions in terraform/infrastructure/readme.md to tear down the perf test environment.
   - Do **not** tear down shared account-wide infrastructure
2. Update `perftest-pointers-table.name_prefix` in `terraform/account-wide-infrastructure/test/dynamodb__pointers-table.tf` to be the table name you want, minus "-pointers-table"
   - e.g. to use the baseline table `nhsd-nrlf--perftest-baseline-pointers-table`, set `name_prefix = "nhsd-nrlf--perftest-baseline"`
3. Update `dynamodb_pointers_table_prefix` in `terraform/infrastructure/etc/perftest.tfvars` same as above.
   - e.g. to use the baseline table `dynamodb_pointers_table_prefix = "nhsd-nrlf--perftest-baseline"`
4. Commit changes to a branch & push
5. Run the [Deploy Account-wide infrastructure](https://github.com/NHSDigital/NRLF/actions/workflows/deploy-account-wide-infra.yml) workflow against your branch & `account-test`.
   - If you get a terraform failure like "tried to create table but it already exists", you will need to do some fanangaling:
     1. make sure there is a backup of your chosen table or create one if not. In the AWS console: dynamodb > tables > your perftest table > backups > create backup > Create on-demand backup > leave all settings as defaults > create backup. This might take up to an hour to complete.
     2. once backed up, delete your table. In the AWS console: dynamodb > tables > your perftest table > actions > delete table
     3. Rerun the Deploy Account-wide infrastructure action.
     4. Terraform will create an empty table with the correct name & (most importantly!) read/write IAM policies.
     5. Delete the empty table created by terraform and restore from the backup, specifying the same table name you've defined in code & selecting the matching customer managed encryption key.
6. Run the [Persistent Environment Deploy](https://github.com/NHSDigital/NRLF/actions/workflows/persistent-environment.yml) workflow against your branch & `perftest` to restore the environment with lambdas pointed at your chosen table.
7. You can check this has been successful by checking the table name in the lambdas.
   - In the AWS console: Lambda > functions > pick any perftest-1 lambda > Configuration > Environment variables > `TABLE_NAME` should be your desired pointer table e.g. `nhsd-nrlf--perftest-baseline-pointers-table`

If you've followed these steps, you will also need to [generate permissions](#generate-permissions) as the organisation permissions will have been lost when the environment was torn down.

#### Generate permissions

You will need to generate pointer permissions the first time performance tests are run in an environment e.g. if the perftest environment is destroyed & recreated.

```sh
# In project root
make perftest-generate-permissions   # makes a bunch of json permission files for test organisations
make get-s3-perms ENV=perftest   # will take all permissions & create nrlf_permissions.zip file
make build

# apply this new permissions zip file to your environment
cd ./terraform/infrastructure
assume nhsd-nrlf-mgmt
make init TF_WORKSPACE_NAME=perftest-1 ENV=perftest
make ENV=perftest USE_SHARED_RESOURCES=true apply
```

### Prepare to run tests

Prepare input files

```sh
assume nhsd-nrlf-test
# PERFTEST_TABLE_NAME = pointer table currently pointed to by perftest env
make perftest-prepare PERFTEST_TABLE_NAME=nhsd-nrlf--perftest-baseline-pointers-table ENV=perftest
```

### Run tests

#### Internal mode

```sh
make perftest-consumer-internal ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
make perftest-producer-internal ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
```

#### Public mode

Via apigee proxies - most similar to a supplier. Spins up a local http server in background responsible for refreshing bearer token (valid for 5 mins each).

```sh
make perftest-consumer-public ENV=perftest
make perftest-producer-public ENV=perftest
```

> Troubleshooting: seeing an unprompted message like "Token refreshed at Mon Jan 19 16:43:35 2026" pop up in your terminal after the test run? The background token server is still going. To resolve, kill the server process with `kill $(lsof -t -i :8765)` (replacing 8765 with your custom port if you specified one).

## Seed data

Must be run on an empty table. Cannot top up an existing set of pointers.

```sh
make perftest-seed-tables ENV=perftest \
   PERFTEST_TABLE_NAME=nhsd-nrlf--perftest-anjali-test-2-pointers-table \
   PERFTEST_PATIENTS_WITH_POINTERS=10 \
   PERFTEST_POINTERS_PER_PATIENT=2
```

### Refresh input files in S3

Regenerates the input files from the current state of a given perftest table & uploads files to s3. These files are usually generated at the end of the seed tables make command (above).

> Note: this can be an expensive operation for large table sizes.

```sh
make perftest-generate-pointer-table-extract \
   PERFTEST_TABLE_NAME=nhsd-nrlf--perftest-anjali-test-2-pointers-table
```

## Assumptions / Caveats

- Run performance tests in the perftest environment only\*
- Both producer & consumer tests are repeatable
- These tests work on the assumption that all nhs numbers in the test data are serial and lie within a fixed range i.e. picking any number between NHS_NUMBER_MINIMUM & NHS_NUMBER_MAXIMUM will yield a patient with pointer(s).
- Configure scenarios in the `consumer/perftest.config.json` & `producer/perftest.config.json` files. This does not alter the number of stages per scenario, that's fixed in `perftest.js`.
- Consider running these tests multiple times to get figures for a warm environment - perftest, unlike prod, is not well-used so you will get cold-start figures on your first run

\*These performance tests are tightly coupled to the seed scripts that populate test data. This means these tests can only be run in an environment containing solely test data created by the seed data scripts. `perftest` is a dedicated environment to do this in, but in theory any environment could be populated with the seed data and used.
