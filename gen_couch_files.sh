#!/bin/bash


COUCH_PATH="/Users/russell/src/couchdb"
CWD=$(pwd)


build_and_store() {
    local erl_ver=$1
    local erts_inc=$2
    local couch_ver=$3

    echo -e "\n\n\n****Building CouchDB****"
    echo -e "\tCouchDB version: $couch_ver"
    echo -e "\tErlang version: $erl_ver"
    echo -e "\tErts include: $erts_inc\n"

    git checkout $couch_ver && git clean -fqdx && erln8 --use=$erl_ver && ./bootstrap && ./configure --with-erlang=$erts_inc && make dev && ./utils/run -b

    # Let the engines warm up
    sleep 3
    echo -e '\n\n\n****COUCHDB IS:'
    curl http://localhost:5984
    echo -e '****\n\n\n'

    cd $CWD
    python test_couch_files.py build_and_store

    cd $COUCH_PATH
    ./utils/run -d
    # kill all the couches
    sleep 3
    ps aux | grep ibrowse | grep -v grep | awk '{ print $2 }' | xargs kill
    ps aux | grep 'utils/run' | grep -v grep | awk '{ print $2 }' | xargs kill
    # Let the engines cool down
    sleep 3
}


# git checkout 1.2.2 && git clean -fqdx && erln8 --use=r14b01 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r14b01/dist/lib/erlang/erts-5.8.2/include/ && make dev && ./utils/run -i
# git checkout 1.4.0 && git clean -fqdx && erln8 --use=r16b03-1 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r16b03-1//dist/lib/erlang/erts-5.10.4/include/ && make dev && ./utils/run -i


cd $COUCH_PATH

for version in $(git tag --list | grep '^1.[1-3]' | grep -v 1.1.0);
do
    erts_version="/Users/russell/.erln8.d/otps/r14b01/dist/lib/erlang/erts-5.8.2/include/"
    build_and_store r14b01 $erts_version $version || exit 1
done
for version in $(git tag --list | grep '^1.[4-6]');
do
    erts_version="/Users/russell/.erln8.d/otps/r16b03-1//dist/lib/erlang/erts-5.10.4/include/"
    build_and_store r16b03-1 $erts_version $version
done

cd $PWD
