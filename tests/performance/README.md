# Performance Testing

<!-- TODO: make this proper -->

some high level context short

## Run perf tests

```sh
assume management
make truststore-pull-all ENV=<env>  # e.g. perftest
cd ./terraform/infrastructure
tf workspace select # perftest-1 or active stack
cd ../../ # project root
assume
make perftest-prepare PERFTEST_TABLE_NAME=<pointer table name>

make perftest-consumer ENV_TYPE=<env>  # e.g. perftest
```

<!-- Mention relevant input files + any environment prep needed e.g. restoring tables from backup -->
