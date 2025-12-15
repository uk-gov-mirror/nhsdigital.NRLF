# Performance Testing

some high level context short

## Run perf tests

### Prepare

```sh
assume management
make truststore-pull-all ENV=<env>  # e.g. perftest
cd ./terraform/infrastructure
tf workspace select # perftest-1 or active stack
cd ../../ # project root
assume dev
make perftest-prepare PERFTEST_TABLE_NAME=<POINTER_TABLE_NAME>

make perftest-consumer ENV_TYPE=<env>  # e.g. perftest
```

choose existing table name/create table with this script > `PERFTEST_TABLE_NAME` env var
makes these files

### Run

these/find profiles available

### Outputs

handy bits
