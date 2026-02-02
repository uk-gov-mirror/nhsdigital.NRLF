# Performance Testing

We have performance tests which give us a benchmark of how NRLF performs under load for consumers and producers.

## Run performance tests

### Prep the environment

Perf tests are generally conducted in the perftest env. There's a selection of tables in the perftest env representing different pointer volume scenarios e.g. perftest-baseline vs perftest-15m vs perftest-55m

#### Pull certs for perftest

```sh
assume nhsd-nrlf-mgmt
make truststore-pull-all ENV=perftest
```

#### Point perftest at a different pointers table

We have multiple tables representing different states of NRLF in the future e.g. all patients receiving an IPS (International Patient Summary), onboarding particular high-volume suppliers.

In order to run performance tests to get figures for these different volumes, we can point the perftest environment at one of these tables.

To do this, we change an environment variable which defines which table our lambdas talk to and deploy changes.

1. Update `dynamodb_pointers_table_name` to be the desired table name in [terraform/infrastructure/etc/perftest.tfvars](terraform/infrastructure/etc/perftest.tfvars) e.g.

```sh
dynamodb_pointers_table_name = "nhsd-nrlf--perftest-baseline-pointers-table"
```

2. To avoid erasing the test permissions when you deploy these changes, make sure to run through the steps to [generate permissions](#generate-permissions)
3. Apply your changes

```sh
cd ./terraform/infrastructure
make init TF_WORKSPACE_NAME=perftest-1 ENV=perftest
make ENV=perftest USE_SHARED_RESOURCES=true apply
```

4. You can verify this has been successful by checking the table name in the lambdas.
   - In the AWS console: Lambda > functions > pick any perftest-1 lambda > Configuration > Environment variables > `TABLE_NAME` should be your desired pointer table e.g. `nhsd-nrlf--perftest-baseline-pointers-table`

#### Generate permissions

You will need to generate pointer permissions the first time performance tests are run in an environment e.g. if the perftest environment is destroyed & recreated.

##### Internal permissions

```sh
assume nhsd-nrlf-mgmt

# In project root
make perftest-generate-permissions   # makes a bunch of json permission files for test organisations
make get-s3-perms ENV=perftest   # will take all permissions & create nrlf_permissions.zip file
make build

# apply this new permissions zip file to your environment
cd ./terraform/infrastructure
make init TF_WORKSPACE_NAME=perftest-1 ENV=perftest
make ENV=perftest USE_SHARED_RESOURCES=true apply
```

This will set up permissions for the `K6PerformanceTest` organisation, which is used for internal testing.

##### Public permissions

To set additional permissions for public testing, you will need to update the permissions for the default app (currently: `X26-NRL-6981ad7d-cff4-4613-93d0-df60e5e2fc52`) which you can do using [./scripts/manage_permissions.py](./scripts/manage_permissions.py).

You can find the pointer types each ODS code will need permissions for in [tests/performance/seed_data_constants.py](tests/performance/seed_data_constants.py) under `*_POINTERS_CUSTODIAN_DISTRIBUTIONS`. These are used to seed the test data.

For example: while running perf tests, the following failure occurred:

```sh
WARN[0484] {"issue":[{"severity":"error","code":"forbidden","details":{"coding":[{"system":"https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode","code":"ACCESS DENIED","display":"Access has been denied to process this request"}]},"diagnostics":"Your organisation 'TD2L9A' does not have permission to access this resource. Contact the onboarding team."}],"resourceType":"OperationOutcome"}  source=console
```

To resolve this, we can give the organisation `TD2L9A` permission to access the pointer type `824321000000109` on the default app:

```sh
ENV=perftest poetry run python ./scripts/manage_permissions.py set_perms X26-NRL-6981ad7d-cff4-4613-93d0-df60e5e2fc52 TD2L9A http://snomed.info/sct\|824321000000109
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
assume nhsd-nrlf-test
make perftest-consumer-internal ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
make perftest-producer-internal ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
```

#### Public mode

Via apigee proxies - most similar to a supplier. Spins up a local http server in background responsible for refreshing bearer token (valid for 5 mins each).

```sh
assume nhsd-nrlf-mgmt
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
   PERFTEST_TABLE_NAME=nhsd-nrlf--perftest-anjali-test-2-pointers-table ENV=perftest
```

This will generate a csv extract of the given pointer table containing a row per pointer. To run the perf tests, you will need an extract larger than the number of test iterations. The default extract size is 2 million - this can be changed in the make file command by updating the value of`--extract-size`. Too big and the test runners will take a long time to load the file.

## Assumptions / Caveats

- Run performance tests in the perftest environment only\*
- Both producer & consumer tests are repeatable
- These tests work on the assumption that all nhs numbers in the test data are serial and lie within a fixed range i.e. picking any number between NHS_NUMBER_MINIMUM & NHS_NUMBER_MAXIMUM will yield a patient with pointer(s).
- Configure scenarios in the `consumer/perftest.config.json` & `producer/perftest.config.json` files. This does not alter the number of stages per scenario, that's fixed in `perftest.js`.
- Consider running these tests multiple times to get figures for a warm environment - perftest, unlike prod, is not well-used so you will get cold-start figures on your first run

\*These performance tests are tightly coupled to the seed scripts that populate test data. This means these tests can only be run in an environment containing solely test data created by the seed data scripts. `perftest` is a dedicated environment to do this in, but in theory any environment could be populated with the seed data and used.
