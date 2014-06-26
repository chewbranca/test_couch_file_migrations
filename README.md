# Test .couch file migrations

This is a set of .couch files created with different tagged versions
of CouchDB. Each database has the following five documents

  1. Simple doc with minimal data
  2. Doc with an external attachment
  3. Doc with an inline attachment
  4. Doc with 1 < num revs < revs_limit
  5. Doc with num revs > revs_limit

The database should also include one deleted document, and it should
_not_ include the test purged doc.

There is a security doc stored in the database that is tested as well.

# Build info

Release 1.4.0 and up built with:

```
git checkout 1.4.0 && git clean -fqdx && erln8 --use=r16b03-1 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r16b03-1//dist/lib/erlang/erts-5.10.4/include/ && make dev && ./utils/run -i
```

Release 1.3.1 and below built with:

```
git checkout 1.3.1 && git clean -fqdx && erln8 --use=r14b01 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r14b01/dist/lib/erlang/erts-5.8.2/include/ && make dev && ./utils/run -i
```

# 1.0.4 and below

I stopped at 1.1.2 as going back further required messing with Spider
Monkey.

# Running the tests

First get BigCouch running:

```
$ git clone https://github.com/apache/couchdb.git bigcouch
$ cd bigcouch
$ git checkout -b 1843-feature-bigcouch origin/1843-feature-bigcouch
$ ./configure && make && ./dev/run
```

In another terminal grap this repo and run the tests. This will take a
minute to clone, as this repo is heavy with binary .couch files.

```
$ git clone https://github.com/chewbranca/test_couch_file_migrations.git
$ cd test_couch_file_migrations
$ export BIGCOUCH_PATH=/Users/russell/src/bigcouch # your path here
$ export BIGCOUCH=http://localhost:15986
$ for f in $(ls *.couch); do
    d=${f%.couch};
    echo "Testing CouchDB version: $d";
    curl -X DELETE $BIGCOUCH/$d;
    cp $f $BIGCOUCH_PATH/dev/lib/node1/data/$f;
    python test_migration.py $BIGCOUCH/$d
done
```