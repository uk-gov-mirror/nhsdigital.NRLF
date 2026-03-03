#!/bin/bash
# Script to manage the NRLF truststore files
#
# Note that all creative and destructive operations are local only apart from
# "push-all". Files are not uploaded to or deleted from S3 automatically.
#
# Once changes have been made locally and have been tested thoroughly, the files
# in the truststore directories can be uploaded to S3 using the appropriate AWS
# CLI commands or the "push-all" command below.
#
set -o errexit -o pipefail -o nounset

BUCKET="nhsd-nrlf--truststore"

function _truststore_help() {
    echo
    echo "$0 <command> [options]"
    echo
    echo "commands:"
    echo "  help                            - this help screen"
    echo "  build-ca <name> <fqdn>          - Build a single CA cert"
    echo "  build-cert <name> <ca> <fqdn>   - Build a single client cert + private key"
    echo "  build-all                       - Build the standard trust store certs"
    echo "  pull-ca <ca>                    - Pull the certificate authority"
    echo "  pull-ca-key <ca>                - Pull the certificate authority private key"
    echo "  pull-client <env>               - pull the files needed for a client connection"
    echo "  pull-server <env>               - pull the files needed for a server connection"
    echo "  pull-all-for-account <acc>      - pull all the truststore files for all environments in a given account"
    echo "  pull-all <env>                  - pull all the truststore files for an environment"
    echo "  push-all <env>                  - push all the truststore files for an environment"
    echo "  rotate-ca <env>                 - rotate the certificate authority, archiving the previous one"
    echo "  rotate-cert <env>               - rotate the client certificate, archiving the previous one"
    echo "  disable-archived-ca <env>       - disable an archived certificate authority"
    echo "  restore-archived-ca <env>       - restore an archived certificate authority"
    echo "  restore-archived-cert <env>     - restore an archived client certificate"
    echo
    return 0
}

# read an input file and substitute all the ${} entries
function substitute_env_in_file() {
    infile=$1
    outfile=$2

    output=$(eval "cat <<EOF
$(cat ${infile})
EOF"
)
    cat > ${outfile} <<EOF
${output}
EOF

    return 0
}

# build a certificate authority
function _truststore_build_ca() {
    if [[ $# -ne 2 ]]; then
        echo "Usage: $0 build-ca <name> <fqdn>"
        return 1
    fi

    env=$1
    fqdn=$2

    substitute_env_in_file ./truststore/config/ca.conf /tmp/ca.conf

    echo -e "🚧 Building CA: $env \t(FQDN: $fqdn)"

    openssl req -newkey rsa:4096 \
        -nodes \
        -keyout ./truststore/ca/$env.key \
        -new \
        -x509 \
        -days 36500 \
        -out ./truststore/ca/$env.crt \
        -config /tmp/ca.conf \
        -extensions v3_req \
        -extensions v3_ca &> /dev/null

    rm /tmp/ca.conf
    echo -e "✅ Successfully Built CA: $env (FQDN: $fqdn)"

    cat ./truststore/ca/$env.crt > ./truststore/server/$env.pem
    echo -e "✅ Successfully Built Server Truststore: $env"
    return 0
}

# build a certificate
function _truststore_build_cert() {
    if [[ $# -ne 3 ]]; then
        echo "Usage: $0 build-cert <name> <ca> <fqdn>"
        return 1;
    fi

    cert_name=$1
    ca_name=$2
    fqdn=$3
    serial=$(date +%s%3N)

    substitute_env_in_file ./truststore/config/client.conf /tmp/client.conf

    echo -e "🚧 Generating $cert_name keypair"

    openssl req \
        -newkey rsa:4096 \
        -nodes \
        -keyout truststore/client/$cert_name.key \
        -new \
        -out truststore/client/$cert_name.csr \
        -config /tmp/client.conf \
        -extensions v3_req \
        -extensions usr_cert &> /dev/null

    echo -e "🚧 Signing $cert_name certificate with ca=$ca_name (serial: $serial)"

    openssl x509 \
        -req \
        -in truststore/client/$cert_name.csr \
        -CA truststore/ca/$ca_name.crt \
        -CAkey truststore/ca/$ca_name.key \
        -set_serial $serial \
        -out truststore/client/$cert_name.crt \
        -days 36500 \
        -sha256 \
        -extfile /tmp/client.conf \
        -extensions v3_req \
        -extensions usr_cert &> /dev/null

    echo -e "✅ Successfully generated $cert_name keypair for ca=$ca_name (FQDN: $fqdn)"
    rm /tmp/client.conf
    rm truststore/client/$cert_name.csr
    return 0
}

# Rotate a CA - archive the existing CA and build a new one
# The previous CA is added to the new CA bundle (can be removed after clients have updated)
function _truststore_rotate_ca() {
    if [[ $# -ne 2 ]]; then
        echo "Usage: $0 rotate-ca <env> <fqdn>"
        return 1;
    fi

    env="$1"
    fqdn="$2"

    if [[ ! -f "truststore/ca/$env.crt" ]] ||
       [[ ! -f "truststore/ca/$env.key" ]] ||
       [[ ! -f "truststore/server/$env.pem" ]]; then
        echo "Error: One or more ca cert truststore files not found for environment $env - cannot rotate CA" 1>&2
        echo "Try running this first:" 1>&2
        echo "    $0 pull-all $env && $0 pull-ca-key dev" 1>&2
        return 1
    fi

    # Archive the existing ca certs
    archive_date="$(date +%Y-%m-%d)"
    if [[ -f "truststore/ca/$env.archived_$archive_date.crt" ]] ||
       [[ -f "truststore/ca/$env.archived_$archive_date.key" ]] ||
       [[ -f "truststore/server/$env.archived_$archive_date.pem" ]]; then
        echo "Error: Archive files already exist for date $archive_date - please resolve before rotating the CA" 1>&2
        return 1
    fi

    mv "truststore/ca/$env.crt" "truststore/ca/$env.archived_$archive_date.crt"
    mv "truststore/ca/$env.key" "truststore/ca/$env.archived_$archive_date.key"
    mv "truststore/server/$env.pem" "truststore/server/$env.archived_$archive_date.pem"

    # Build a new CA
    _truststore_build_ca "$env" "$fqdn"

    # Add the previous CA to the new CA bundle (can be removed after clients have updated)
    cat "truststore/ca/$env.archived_$archive_date.crt" >> "truststore/server/$env.pem"

    echo -e "✅ Successfully rotated CA for $env - previous CA archived with date: $archive_date"
    return 0
}

# Rotate a client cert - archive the existing cert and build a new one
function _truststore_rotate_cert() {
    if [[ $# -ne 3 ]]; then
        echo "Usage: $0 rotate-cert <env> <ca> <fqdn>"
        exit 1;
    fi

    cert_name="$1"
    ca_name="$2"
    fqdn="$3"

    if [[ ! -f "truststore/client/$cert_name.crt" ]] ||
       [[ ! -f "truststore/client/$cert_name.key" ]]; then
        echo "Error: One or more client cert truststore files not found for $cert_name - cannot rotate client cert" 1>&2
        echo "Try running this first:" 1>&2
        echo "    $0 pull-all $cert_name" 1>&2
        return 1
    fi

    # Archive the existing client certs
    archive_date=$(date +%Y-%m-%d)
    if [[ -f "truststore/client/$cert_name.archived_$archive_date.crt" ]] ||
       [[ -f "truststore/client/$cert_name.archived_$archive_date.key" ]]; then
        echo "Error: Archive files already exist for date $archive_date - please resolve before rotating the client cert" 1>&2
        return 1
    fi

    mv "truststore/client/$cert_name.crt" "truststore/client/$cert_name.archived_$archive_date.crt"
    mv "truststore/client/$cert_name.key" "truststore/client/$cert_name.archived_$archive_date.key"

    # Build a new client cert
    _truststore_build_cert "$cert_name" "$ca_name" "$fqdn"

    echo -e "✅ Successfully rotated client cert for $cert_name - previous cert archived with date: $archive_date"
    return 0
}

# Disable an archived CA by removing it from the server pem file
function _disable_archived_ca() {
    env="$1"
    cat "truststore/ca/$env.crt" > "truststore/server/$env.pem"

    echo -e "✅ Successfully disabled archived CA for $env"
    return 0
}

# Restore an archived CA by moving the archived files back to their original names
function _restore_archived_ca() {
    env="$1"
    archive_date="$2"

    mv "truststore/ca/$env.archived_$archive_date.crt" "truststore/ca/$env.crt"
    mv "truststore/ca/$env.archived_$archive_date.key" "truststore/ca/$env.key"
    mv "truststore/server/$env.archived_$archive_date.pem" "truststore/server/$env.pem"

    echo -e "✅ Successfully restored archived CA for $env from date: $archive_date"
    return 0
}

# Restore an archived client cert by moving the archived files back to their original names
function _restore_archived_cert() {
    env="$1"
    archive_date="$2"

    mv "truststore/client/$env.archived_$archive_date.crt" "truststore/client/$env.crt"
    mv "truststore/client/$env.archived_$archive_date.key" "truststore/client/$env.key"

    echo -e "✅ Successfully restored archived client cert for $env from date: $archive_date"
    return 0
}

function _truststore_build_all() {
    _truststore_build_ca "prod"     "record-locator.national.nhs.uk_CA2"
    _truststore_build_ca "int"      "record-locator.int.national.nhs.uk_CA2"
    _truststore_build_ca "ref"      "record-locator.ref.national.nhs.uk_CA2"
    _truststore_build_ca "perftest" "perftest.record-locator.national.nhs.uk_CA2"
    _truststore_build_ca "qa"       "qa.record-locator.national.nhs.uk_CA2"
    _truststore_build_ca "dev"      "record-locator.dev.national.nhs.uk_CA2"

    _truststore_build_cert "prod"     "prod" "api.record-locator.national.nhs.uk"
    _truststore_build_cert "int"      "int"  "int.api.record-locator.int.national.nhs.uk"
    _truststore_build_cert "ref"      "ref"  "ref.api.record-locator.ref.national.nhs.uk"
    _truststore_build_cert "perftest" "perftest"  "api.perftest.record-locator.national.nhs.uk"
    _truststore_build_cert "qa"       "qa"   "api.qa.record-locator.national.nhs.uk"
    _truststore_build_cert "dev"      "dev"  "dev.api.record-locator.dev.national.nhs.uk"

    echo -e "✅ Successfully built all truststore files"
    return 0
}

function _truststore_pull_ca() {
    env=$1
    echo "Pulling ${env} ca certificate"
    aws s3 cp "s3://${BUCKET}/ca/${env}.crt" "truststore/ca/${env}.crt"

    echo -e "✅ Successfully pulled ${env} ca certificate from s3://${BUCKET}"
    return 0
}

function _truststore_pull_ca_key() {
    env=$1
    echo "Pulling ${env} ca private key"
    aws s3 cp "s3://${BUCKET}/ca/${env}.key" "truststore/ca/${env}.key"

    echo -e "✅ Successfully pulled ${env} ca private key from s3://${BUCKET}"
    return 0
}

function _truststore_pull_client() {
    env=$1
    echo "Pulling ${env} client certificate"
    aws s3 cp "s3://${BUCKET}/client/${env}.key" "truststore/client/${env}.key"
    aws s3 cp "s3://${BUCKET}/client/${env}.crt" "truststore/client/${env}.crt"

    echo -e "✅ Successfully pulled ${env} client truststore files from s3://${BUCKET}"
    return 0
}

function _truststore_pull_server() {
    env=$1
    echo "Pulling ${env} server trust certificate"
    aws s3 cp "s3://${BUCKET}/server/${env}.pem" "truststore/server/${env}.pem"

    echo -e "✅ Successfully pulled ${env} server truststore files from s3://${BUCKET}"
    return 0
}

function _truststore_pull_all() {
    env=$1

    _truststore_pull_ca $env
    _truststore_pull_client $env
    _truststore_pull_server $env

    echo -e "✅ Successfully pulled all ${env} truststore files from s3://${BUCKET}"
    return 0
}

function _truststore_pull_all_for_account() {
    account=$1

    # sets envs_array
    source ./scripts/get-envs-for-account.sh $account

    for env in ${envs_array[@]}; do
        # don't need to pull sandbox certs
        if [[ $env != *"-sandbox" ]];
        then
            echo "⏳ Pulling ${env} truststore certs"
            _truststore_pull_ca $env
            _truststore_pull_client $env
            _truststore_pull_server $env
        fi
    done

    echo -e "✅ Successfully pulled all ${account} truststore files from s3://${BUCKET}"
    return 0
}

function _truststore_push_all() {
    env=$1

    timestamp="$(date +%Y-%m-%d_%H%M%S)"
    backup_dir="truststore/backup/${env}_${timestamp}"

    echo -e "Backing up existing files to ${backup_dir}...."
    mkdir -p "${backup_dir}/ca" "${backup_dir}/client" "${backup_dir}/server"
    for f in "ca/${env}.crt" "ca/${env}.key" "client/${env}.crt" "client/${env}.key" "server/${env}.pem"
    do
        echo
        aws s3 cp "s3://${BUCKET}/$f" "${backup_dir}/$f" || echo "No existing file s3://${BUCKET}/$f to back up"

        if [[ -f "${backup_dir}/$f" ]]
        then
            diff --brief "truststore/$f" "${backup_dir}/$f" || true
        fi
    done

    echo
    echo -n "WARNING: You are about to upload files to the ${env} truststore - are you sure? [yes/NO] "
    read answer
    if [[ "$answer" != "yes" ]]; then
        echo "Aborting upload to ${env} truststore" 1>&2
        return 1
    fi

    echo "Uploading ${env} ca certificate"
    aws s3 cp "truststore/ca/${env}.crt" "s3://${BUCKET}/ca/${env}.crt"

    echo "Uploading ${env} ca private key"
    aws s3 cp "truststore/ca/${env}.key" "s3://${BUCKET}/ca/${env}.key"

    echo "Uploading ${env} client certificate"
    aws s3 cp "truststore/client/${env}.key" "s3://${BUCKET}/client/${env}.key"
    aws s3 cp "truststore/client/${env}.crt" "s3://${BUCKET}/client/${env}.crt"

    echo "Uploading ${env} server trust certificate"
    aws s3 cp "truststore/server/${env}.pem" "s3://${BUCKET}/server/${env}.pem"

    echo -e "✅ Successfully uploaded all ${env} truststore files to s3://${BUCKET}"
    return 0
}

function _truststore() {
    local command=$1; shift
    local args=$@

    case $command in
        "build-all") _truststore_build_all $args ;;
        "build-ca") _truststore_build_ca $args ;;
        "build-cert") _truststore_build_cert $args ;;
        "pull-all") _truststore_pull_all $args ;;
        "pull-all-for-account") _truststore_pull_all_for_account $args ;;
        "pull-server") _truststore_pull_server $args ;;
        "pull-client") _truststore_pull_client $args ;;
        "pull-ca") _truststore_pull_ca $args ;;
        "pull-ca-key") _truststore_pull_ca_key $args ;;
        "push-all") _truststore_push_all $args ;;
        "rotate-ca") _truststore_rotate_ca $args ;;
        "rotate-cert") _truststore_rotate_cert $args ;;
        "disable-archived-ca") _disable_archived_ca $args ;;
        "restore-archived-ca") _restore_archived_ca $args ;;
        "restore-archived-cert") _restore_archived_cert $args ;;
        *) _truststore_help $args ;;
    esac

    return 0
}

_truststore $@
