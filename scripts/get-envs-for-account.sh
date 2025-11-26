#!/bin/bash
# Get the names of all environments in a provided NRL AWS account
set -o errexit -o nounset -o pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: get-envs-for-account.sh <account>"
    exit 1
fi

account="$1"

case "${account}" in
    dev)
        envs_array=("dev" "dev-sandbox")
        echo ${envs_array[@]}
        ;;
    test)
        envs_array=("qa" "perftest" "ref" "int" "int-sandbox") #  "qa-sandbox" currently broken
        echo ${envs_array[@]}
        ;;
    prod)
        envs_array=("prod")
        echo ${envs_array[@]}
        ;;
    *)
        echo "Unknown account ${account}"
        exit 1
esac
