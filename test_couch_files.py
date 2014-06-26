#!/usr/bin/env python


import os
import re
import sys
import glob
import json
import time
import shutil
import base64
import inspect
import requests


couch_host = "http://localhost:5984"
clustered_host = "http://localhost:15984"
single_node_host = "http://localhost:15986"

parent_auth = ()
DEBUG = True
final_rev = 1234


dbname = "test_couch_files"
shard_range = "00000000-ffffffff"
shard_suffix = ".1401320900"
shard_suffix_arr = [46, 49, 52, 48, 49, 51, 50, 48, 57, 48, 48]

src_dir = "/Users/russell/src"
couch_db_path = src_dir + "/couchdb/tmp/lib"
test_couch_files_path = src_dir + "/test_couch_file_migrations"

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


def disable_delayed_commits():
    http('put', couch_host + "/_config/couchdb/delayed_commits", raw_data='"false"', headers={}, assertion=200)


def node_db_path(i=1):
    return "{0}/bigcouch/dev/lib/node{1}/data".format(src_dir, i)


def node_shards_path(i=1, s_range=None):
    shards_path = node_db_path(i)
    if s_range is not None:
        shards_path += "/shards/" + s_range
    return shards_path


def node_shard_path(dbname, i=1):
    shards_path = node_shards_path(i, shard_range)
    return "{0}/{1}{2}.couch".format(shards_path, dbname, shard_suffix)


def get_version(host):
    status, resp = http('get', host, assertion=200)
    return re.sub(r"[^0-9a-zA-Z]", "__", resp["version"])


def add_sec_doc(dbname):
    return http('put', dbname + "/_security", assertion=200, data=sec_doc)


def get_sec_doc(dbname):
    _s, resp = http('get', dbname + "/_security", assertion=200)
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
        print "[DEBUG::{0}] {1}".format(func_to_db(), msg)


def func_to_db():
    return inspect.stack()[2][3]


def gen_test_db():
    dbname = func_to_db()
    # return create_db(dbname)
    return dbname


def passed_test(name=None):
    if name is None:
        name = funct_to_db()
    log("{0} passed".format(name))


def delete_db(db):
    return http('delete', db)


def create_db(db, cycle=True):
    if cycle: delete_db(db)
    http('put', db, assertion=201)


def save_ddoc(url, ddoc):
    code, _resp = http('put', url, data=ddoc)
    print "Saving ddoc({0}): {1}".format(code, url)


def delete_doc(url, force=False):
    status, resp = http('get', url)
    if status == 404 and not force:
        return True
    elif status == 200:
        rev = resp['_rev']
        http('delete', url + '?rev=' + rev, assertion=200)
        return True
    else:
        raise Exception("Error deleting doc({0}): {1}".format(status, resp))


def dbs_doc(dbname):
    return {
        "by_range": {
            shard_range : [
                "node1@127.0.0.1",
                "node2@127.0.0.1",
                "node3@127.0.0.1"
            ]
        },
        "by_node": {
            "node1@127.0.0.1": [shard_range],
            "node2@127.0.0.1": [shard_range],
            "node3@127.0.0.1": [shard_range]
        },
        "shard_suffix": shard_suffix_arr,
        "_id": dbname
    }


def file_exists(filename):
    return os.path.exists(filename)


def path_to_dbname(path):
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def doc_rev_num(doc):
    rev = doc.get("_rev", doc.get("rev", "0"))
    return int(rev.split('-')[0])


def get_db_urls(dbname):
    host_db = "{0}/{1}".format(couch_host, dbname)
    single_node_db = "{0}/{1}".format(single_node_host, dbname)
    clustered_db = "{0}/{1}".format(clustered_host, dbname)
    return (host_db, single_node_db, clustered_db)

def get_dbs_db_url(dbname):
    return "{0}/dbs/{1}".format(single_node_host, dbname)


# mkdir -p dev/lib/node{1,2,3}/data/shards/00000000-ffffffff
def get_db_paths(dbname):
    host_file = "{0}/{1}.couch".format(couch_db_path, dbname)
    single_node_file = "{0}/{1}.couch".format(node_db_path(), dbname)
    clustered = [node_shard_path(dbname, i) for i in [1,2,3]]
    return (host_file, single_node_file, clustered)


def copy_file(src, tgt):
    log("cp {0} {1}".format(src, tgt))
    shutil.copy(src, tgt)


def test_single_node():
    dbname = gen_test_db()
    host_db, single_node_db, _clustered_db = get_db_urls(dbname)
    create_db(host_db)
    host_file, single_node_file, _clustered_files = get_db_paths(dbname)
    assert(file_exists(host_file))
    delete_db(single_node_db)
    assert(not file_exists(single_node_file))
    copy_file(host_file, single_node_file)
    assert(file_exists(single_node_file))
    status, resp = http('get', single_node_db, assertion=200)
    assert(0 == resp['update_seq'])
    assert(0 == resp['doc_count'])


def test_single_node_with_doc():
    dbname = gen_test_db()
    host_db, single_node_db, _clustered_db = get_db_urls(dbname)
    doc_id = "asdf"
    create_db(host_db)
    http('put', host_db + "/" + doc_id, data={"foo":"bar"}, assertion=201)
    host_file, single_node_file, _clustered_files = get_db_paths(dbname)
    assert(file_exists(host_file))
    delete_db(single_node_db)
    assert(not file_exists(single_node_file))
    stats = os.stat(host_file)
    copy_file(host_file, single_node_file)
    assert(file_exists(single_node_file))
    stats = os.stat(single_node_file)
    status, resp = http('get', single_node_db, assertion=200)
    assert(1 == resp['update_seq'])
    assert(1 == resp['doc_count'])
    status, resp = http('get', single_node_db + "/" + doc_id, assertion=200)
    assert(resp["_id"] == doc_id)
    assert(resp["foo"] == "bar")


def test_clustered_node():
    dbname = gen_test_db()
    host_db, single_node_db, clustered_db = get_db_urls(dbname)
    dbs_db_doc_url = get_dbs_db_url(dbname)
    dbs_db_doc = dbs_doc(dbname)
    create_db(host_db)
    host_file, _single_node_file, clustered_files = get_db_paths(dbname)
    assert(file_exists(host_file))
    # delete_db(single_node_db)
    delete_doc(dbs_db_doc_url)
    http('put', dbs_db_doc_url, data=dbs_db_doc, assertion=201)
    # assert(not file_exists(single_node_file))
    [copy_file(host_file, f) for f in clustered_files]
    for f in clustered_files:
        assert(file_exists(f))
    status, resp = http('get', clustered_db, assertion=200)
    [num, extra] = resp['update_seq']
    assert(0 == num)
    assert(len(extra) > 0)
    assert(0 == resp['doc_count'])


def test_clustered_node_with_doc():
    dbname = gen_test_db()
    host_db, single_node_db, clustered_db = get_db_urls(dbname)
    doc_id = "asdf"
    dbs_db_doc_url = get_dbs_db_url(dbname)
    dbs_db_doc = dbs_doc(dbname)
    create_db(host_db)
    http('put', host_db + "/" + doc_id, data={"foo":"bar"}, assertion=201)
    host_file, _single_node_file, clustered_files = get_db_paths(dbname)
    assert(file_exists(host_file))
    delete_db(clustered_db)
    # delete_doc(dbs_db_doc_url)
    # http('put', dbs_db_doc_url, data=dbs_db_doc, assertion=201)
    # assert(not file_exists(single_node_file))
    # for f in clustered_files:
    #     assert(not file_exists(f))
    [copy_file(host_file, f) for f in clustered_files]
    for f in clustered_files:
        assert(file_exists(f))
    time.sleep(2)
    http('put', dbs_db_doc_url, data=dbs_db_doc, assertion=201)
    status, resp = http('get', clustered_db, assertion=200)
    [num, extra] = resp['update_seq']
    assert(1 == num)
    assert(len(extra) > 0)
    assert(1 == resp['doc_count'])


def copy_and_test(dbname):
    log("Testing CouchDB version: {}".format(dbname))
    src_file = "{0}/{1}.couch".format(test_couch_files_path, dbname)
    _host_file, single_node_file, _clustered_files = get_db_paths(dbname)
    _host_db, single_node_db, _clustered_db = get_db_urls(dbname)
    http('delete', single_node_db)
    copy_file(src_file, single_node_file)
    test_full_db_cycle(single_node_db)


def test_full_db_cycle(db):
    full_couch_file_assertions(db)
    compact_and_test(db)
    full_couch_file_assertions(db)


def test_couch_file_migrations():
    paths = glob.glob(test_couch_files_path + "/*.couch")
    log("Found {} CouchDB versions to test".format(len(paths)))
    for path in paths:
        dbname = path_to_dbname(path)
        copy_and_test(dbname)


def copy_db(dbname):
    host_file, _single_node_file, _clustered_files = get_db_paths(dbname)
    dest_file = "{0}/{1}.couch".format(test_couch_files_path, dbname)
    copy_file(host_file, dest_file)


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
    log("RESP1: {0}\nRESP2: {1}".format(resp1, resp2))
    disk_size2 = resp2["disk_size"]
    data_size2 = resp2["data_size"]
    assert(disk_size1 > disk_size2)
    # #full_doc_info{} is bigger than #doc_info{}
    assert(data_size1 < data_size2)


def full_couch_file_assertions(db=None):
    if db is None:
        version = get_version(couch_host)
        dbname = "build_full_couch_file_{}".format(version)
        db = "{0}/{1}".format(couch_host, dbname)

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


def build_full_couch_file():
    disable_delayed_commits()

    version = get_version(couch_host)
    dbname = "{0}_{1}".format(gen_test_db(), version)
    couch_db = "{0}/{1}".format(couch_host, dbname)
    create_db(couch_db)

    # add a security doc
    add_sec_doc(couch_db)

    # create sample simple doc
    doc = {
        "_id": "simple_doc",
        "data": "minimal"
    }
    http('put', couch_db + "/" + doc["_id"], data=doc, assertion=201)

    # create sample deleted doc
    doc = {
        "_id": "deleted_doc",
        "data": "deleted"
    }
    _s, resp = http('put', couch_db + "/" + doc["_id"], data=doc, assertion=201)
    doc["_rev"] = resp["rev"]
    doc["_deleted"] = True
    _s, resp = http('put', couch_db + "/" + doc["_id"], data=doc, assertion=200)

    # create sample purged doc
    doc = {
        "_id": "purged_doc",
        "data": "purged"
    }
    _s, resp = http('put', couch_db + "/" + doc["_id"], data=doc, assertion=201)
    rev = resp["rev"]
    to_purge = {
        doc["_id"] : [
            rev
        ]
    }
    _s, resp = http('post', couch_db + "/_purge", data=to_purge, assertion=200)
    assert(resp["purged"] == to_purge)
    assert(resp["purge_seq"] == 1)

    # create sample doc with external attachments
    doc = {
        "_id": "external_attachments_doc",
        "data": "with external .gif attachment"
    }
    status, resp = http('put', couch_db + "/" + doc["_id"], data=doc, assertion=201)
    rev = resp["rev"]
    files = {'file': open("/Users/russell/Pictures/lemming_head_explode.gif", 'rb')}
    data = open("/Users/russell/Pictures/lemming_head_explode.gif", 'rb').read()
    doc_url = couch_db + "/" + doc["_id"] + "/the_attachment.gif?rev=" + rev
    headers = {"Content-Type": "image/gif"}
    status, resp = http('put', doc_url, raw_data=data, headers=headers, assertion=201)

    # create sample doc with inline attachments
    text = "Exciting inline attachment text"
    doc = {
        "_id": "inline_attachments_doc",
        "data": "with inline attachment",
        "_attachments": {
            "asdf.txt": {
                "content_type":"text\/plain",
                "data": base64.b64encode(text)
            }
        }
    }
    doc_url = couch_db + "/" + doc["_id"]
    http('put', doc_url, data=doc, assertion=201)
    status, resp = http('get', doc_url + "/asdf.txt", assertion=200, headers={})
    assert(resp == text)

    # doc with revs
    doc = {
        "_id": "small_num_revs_doc",
        "data": "with revs and num revs < revs_limit"
    }
    doc_url = couch_db + "/" + doc["_id"]
    status, resp = http('put', doc_url, data=doc, assertion=201)
    doc["_rev"] = resp["rev"]
    while doc_rev_num(doc) < 10:
        doc_url2 = "{0}?rev={1}".format(doc_url, doc["_rev"])
        status, resp = http('put', doc_url2, data=doc, assertion=201)
        doc["_rev"] = resp["rev"]
    assert(doc_rev_num(doc) == 10)

    # doc with lots of revs (more than revs_limit=1000)
    doc = {
        "_id": "large_num_revs_doc",
        "data": "with revs and num revs > revs_limit"
    }
    doc_url = couch_db + "/" + doc["_id"]
    status, resp = http('put', doc_url, data=doc, assertion=201)
    doc["_rev"] = resp["rev"]
    while doc_rev_num(doc) < final_rev:
        doc_url2 = "{0}?rev={1}".format(doc_url, doc["_rev"])
        status, resp = http('put', doc_url2, data=doc, assertion=201)
        doc["_rev"] = resp["rev"]
    assert(doc_rev_num(doc) == final_rev)
    status, resp = http('get', doc_url + "?revs_info=true", data=doc, assertion=200)
    assert(len(resp["_revs_info"]) == 1000)
    assert(len(resp["_revs_info"]) < final_rev)

    # database state tests
    db_meta_assertions(couch_db)

    return dbname


def build_and_store():
    dbname = build_full_couch_file()
    couch_db = "{0}/{1}".format(couch_host, dbname)
    full_couch_file_assertions(couch_db)
    copy_db(dbname)


def run_test(name, test, args=[]):
    log("Running test: {}".format(name))
    resp = test(*args)
    if resp is not None:
        print "Result: {}".format(resp)


def main(test=None, args=[]):
    # disable_delayed_commits()

    print "Running tests({})".format(test)
    if test is None:
        attrs = inspect.getmembers(sys.modules[__name__])
        [run_test(n, t, args) for n, t in attrs if "test_" == n[0:5]]
    else:
        func = getattr(sys.modules[__name__], test)
        run_test(test, func, args)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main(sys.argv[1], sys.argv[2:])
    else:
        sys.exit(1)
        # main()
