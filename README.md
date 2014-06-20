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

git checkout 1.4.0 && git clean -fqdx && erln8 --use=r16b03-1 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r16b03-1//dist/lib/erlang/erts-5.10.4/include/ && make dev && ./utils/run -i

Release 1.3.1 and below built with:

git checkout 1.3.1 && git clean -fqdx && erln8 --use=r14b01 && ./bootstrap && ./configure --with-erlang=/Users/russell/.erln8.d/otps/r14b01/dist/lib/erlang/erts-5.8.2/include/ && make dev && ./utils/run -i


# 1.0.4 and below

I stopped at 1.1.2 as going back further required messing with Spider
Monkey.

# Current status

The function `test_couch_file_migrations` in `test_couch_files.py`
grabs all the .couch files in the repo, and copies them into BigCouch
to test out the results, and verify the same assertions are true.

Sadly they are not true.

All versions greater than or equal to 1.3.1 fail the
`large_num_revs_doc` test. This test creates a document with a number
of revs greater than the system revs_limit. All of the failing
versions end up with a different rev number that is different than
what it should be. Unfortunately the requests do not fail, but rather
return incorrect data. Sample output (also notice that the
`small_num_revs_doc` test passes fine):

```
$ curl http://localhost:15986/build_full_couch_file_1__6__0__build__fauxton__233__g23490c1/large_num_revs_doc
{"_id":"large_num_revs_doc","_rev":"1212-7f710abf8a65f6c4f66c6fcd8f208483","data":"with revs and num revs > revs_limit"}

$ curl http://localhost:5984/build_full_couch_file_1__6__0__build__fauxton__233__g23490c1/large_num_revs_doc
{"_id":"large_num_revs_doc","_rev":"1234-c1309313251306d53d31862ed7fae575","data":"with revs and num revs > revs_limit"}

$ curl http://localhost:5984/build_full_couch_file_1__6__0__build__fauxton__233__g23490c1/small_num_revs_doc
{"_id":"small_num_revs_doc","_rev":"10-327187f3c8c237933d2962cbe00bc87b","data":"with revs and num revs < revs_limit"}

$ curl http://localhost:15986/build_full_couch_file_1__6__0__build__fauxton__233__g23490c1/small_num_revs_doc
{"_id":"small_num_revs_doc","_rev":"10-327187f3c8c237933d2962cbe00bc87b","data":"with revs and num revs < revs_limit"}

# Running the tests

The current script is an ugly hack with hardcoded values for my dev
box. The main purpose was to push up a set of .couch files. If there's
interest I can make this more easily usable by other people, but the
script has done it's job and demonstrated a serious problem.