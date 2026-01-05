# Performance Testing

some high level context short

## Run perf tests

### Prep the environment

Perf tests are generally conducted in the perftest env. There's a selection of tables in the perftest env representing different pointer volume scenarios e.g. perftest-baseline vs perftest-1million (todo: update with real names!).

To reset this table to the expected state for perftests, restore the table from a backup.

In the steps below, make sure the table name is the table your environment is pointing at. You might need to redeploy NRLF lambdas to point at the desired table.

### Prepare to run tests

#### Pull certs for env

```sh
assume management
make truststore-pull-all ENV=perftest
```

#### Generate permissions

You will need to generate pointer permissions the first time performance tests are run in an environment e.g. if the perftest environment is destroyed & recreated.

```sh
make generate permissions   # makes a bunch of json permission files
make build  # will take all permissions & create nrlf_permissions.zip file

# apply this new permissions zip file to your environment
cd ./terraform/infrastructure
assume test # needed?
make init TF_WORKSPACE_NAME=perftest-1 ENV=perftest
tf apply
```

#### Generate input files

```sh
# creates 2 csv files and a json file
make perftest-prepare PERFTEST_TABLE_NAME=perftest-baseline
```

### Run tests

```sh
make perftest-consumer ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
make perftest-producer ENV_TYPE=perftest PERFTEST_HOST=perftest-1.perftest.record-locator.national.nhs.uk
```
