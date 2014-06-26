import os
import sys
import json
import time
import inspect
import requests

parent_auth = ()
DEBUG = True
final_rev = 1234

sec_doc = {
  "admins" : {
     "names" : ["joe", "phil"],
     "roles" : ["boss"]
   },
   "members" : {
     "names" : ["dave"],
     "roles" : ["producer", "consumer"]
   }
}


def doc_rev_num(doc):
    rev = doc.get("_rev", doc.get("rev", "0"))
    return int(rev.split('-')[0])


def get_sec_doc(db):
    _s, resp = http('get', db + "/_security", assertion=200)
    return resp


def http(method, url, data=None, auth=None, headers=None, assertion=None, files=None, raw_data=None):
    meth = getattr(requests, method)
    if headers is None:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if data is not None:
        data = json.dumps(data)
    if raw_data is not None:
        data = raw_data
    if auth is None:
        auth = parent_auth
    log("HTTP[{0}]: {1}".format(method, url))
    resp = meth(url, data=data, auth=auth, headers=headers, files=files)
    if assertion is not None:
        name = auth[0] if len(auth) == 2 else "undefined"
        msg = "ERROR IN {5}: {0} {1} - {6} || expected ({2}), but received ({3}): {4}".format(
            method.upper(), url, assertion, resp.status_code, resp.content, func_to_db(), name)
        assert (assertion == resp.status_code), msg
    if resp.headers["content-type"] == "application/json":
        return resp.status_code, resp.json()
    else:
        return resp.status_code, resp.content


def log(msg):
    if DEBUG:
        print("[DEBUG::{0}] {1}".format(func_to_db(), msg))


def func_to_db():
    return inspect.stack()[2][3]


def passed_test(name=None):
    if name is None:
        name = func_to_db()
    log("{0} passed".format(name))


def compact_db(db, block=True):
    http('post', db + "/_compact", assertion=202)
    if block:
        while True:
            log("Compacting {} ...".format(db))
            _s, resp = http('get', db, assertion=200)
            if resp["compact_running"] is True:
                time.sleep(0.1)
            else:
                break


def compact_and_test(db):
    _s, resp1 = http('get', db, assertion=200)
    disk_size1 = resp1["disk_size"]
    data_size1 = resp1["data_size"]
    if resp1["disk_format_version"] > 5:
        assert(resp1["data_size"] is not None)
    compact_db(db)
    _s, resp2 = http('get', db, assertion=200)
    disk_size2 = resp2["disk_size"]
    data_size2 = resp2["data_size"]
    assert(disk_size1 > disk_size2)
    # #full_doc_info{} is bigger than #doc_info{}
    assert(data_size1 < data_size2)


def test_full_db_cycle(db):
    full_couch_file_assertions(db)
    compact_and_test(db)
    full_couch_file_assertions(db)


def full_couch_file_assertions(db):
    dbname = os.path.basename(db)

    log("Running full couch file assertions on {}".format(db))

    # security doc test
    assert(get_sec_doc(db) == sec_doc)
    passed_test("[{}] security doc test".format(dbname))

    # simple doc test
    _status, resp = http('get', db + "/simple_doc", assertion=200)
    rev_num = doc_rev_num(resp)
    assert(resp["data"] == "minimal")
    assert(rev_num == 1)
    passed_test("[{}] simple doc test".format(dbname))

    # deleted doc test
    _status, resp = http('get', db + "/deleted_doc", assertion=404)
    assert(resp == {"error":"not_found","reason":"deleted"})
    passed_test("[{}] deleted doc test".format(dbname))

    # purged doc test
    _status, resp = http('get', db + "/purged_doc", assertion=404)
    assert(resp == {"error":"not_found","reason":"missing"})
    passed_test("[{}] purged doc test".format(dbname))

    # external attachments doc test
    _status, resp = http('get', db + "/external_attachments_doc", assertion=200)
    _status, resp2 = http('get', db + "/external_attachments_doc/the_attachment.gif", assertion=200)
    rev_num = doc_rev_num(resp)
    assert(resp["data"] == "with external .gif attachment")
    assert(rev_num == 2)
    assert(len(resp2) == 59769)
    passed_test("[{}] external attachments doc test".format(dbname))

    # inline attachments doc test
    _status, resp = http('get', db + "/inline_attachments_doc", assertion=200)
    _status, resp2 = http('get', db + "/inline_attachments_doc/asdf.txt", assertion=200)
    rev_num = doc_rev_num(resp)
    assert(resp["data"] == "with inline attachment")
    assert(rev_num == 1)
    assert(resp2 == "Exciting inline attachment text")
    passed_test("[{}] inline attachments doc test".format(dbname))

    # doc with num revs < revs_limit test
    _status, resp = http('get', db + "/small_num_revs_doc", assertion=200)
    rev_num = doc_rev_num(resp)
    assert(resp["data"] == "with revs and num revs < revs_limit")
    assert(rev_num == 10)
    passed_test("[{}] small num revs doc test".format(dbname))

    # doc with num revs > revs_limit test
    _status, resp = http('get', db + "/large_num_revs_doc?revs_info=true", assertion=200)
    rev_num = doc_rev_num(resp)
    assert(resp["data"] == "with revs and num revs > revs_limit")
    assert(rev_num == final_rev)
    assert(len(resp["_revs_info"]) == 1000)
    passed_test("[{}] large num revs doc test".format(dbname))

    # database state tests
    db_meta_assertions(db)
    passed_test("[{}] database state test".format(dbname))



def db_meta_assertions(db, disk_format_version=6):
    disk_format_version = 5 if '1__1__2' in db else 6
    _s, resp = http('get', db, assertion=200)
    log("DB RESP: {}".format(resp))
    assert(resp['update_seq'] == 1253)
    assert(resp['doc_count'] == 5)
    assert(resp['doc_del_count'] == 1)
    # TODO: Clean this up, need to support v5 and v6 after compaction
    # assert(resp['disk_format_version'] == disk_format_version)
    assert(resp['purge_seq'] == 1)


def main(db):
    log("*****Running tests against: {}*****".format(db))
    # full_couch_file_assertions(db)
    test_full_db_cycle(db)
    log("*****Tests Completed*****")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(1)
