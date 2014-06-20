# Test .couch file migrations

This is a set of .couch files created with different tagged versions
of CouchDB. Each database has the following five documents

  1. Simple doc with minimal data
  2. Doc with an external attachment
  3. Doc with an inline attachment
  4. Doc with 1 < num revs < revs_limit
  5. Doc with num revs > revs_limit

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

The current script is an ugly hack with hardcoded values for my dev
box. The main purpose was to push up a set of .couch files. If there's
interest I can make this more easily usable by other people.
