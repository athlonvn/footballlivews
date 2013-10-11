from __future__ import division
import bottle
import json
import hashlib
import sys
import pymongo
import os
import datetime
from bson import json_util
from pymongo import Connection
from bottle import default_app

mongo_con = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_HOST'],
                               int(os.environ['OPENSHIFT_MONGODB_DB_PORT']))

mongo_db = mongo_con[os.environ['OPENSHIFT_APP_NAME']]
mongo_db.authenticate(os.environ['OPENSHIFT_MONGODB_DB_USERNAME'],
                      os.environ['OPENSHIFT_MONGODB_DB_PASSWORD'])

##mongo_con = Connection('mongodb://localhost',safe=False)
##mongo_db = mongo_con['adcolony']



SECRET_KEY = ''
def parse_to_json_str(dict_doc):
	return str(json.dumps(dict_doc,default=json_util.default))

def hash_md5(strmsg):
	h = hashlib.md5()
	h.update(strmsg)
	return str(h.hexdigest())

def insert_callback(trans_id, data):
    if not is_trans_id_exist(trans_id):
        try:
            mongo_db['callback'].update({"trans_id":trans_id},{"$set":data}, upsert=True)
        except:
            return str(sys.exc_info()[1])
        return 'vc_success'
    else:
        return 'vc_decline'

def is_trans_id_exist(trans_id):
    if not trans_id: return None
    return mongo_db['callback'].find_one({ 'trans_id': trans_id})

def get_transaction():
    return [data for data in mongo_db['callback'].find()]

@bottle.route('/')
def print_vc_fail():
    return 'This is webservice adcolony'
'''
id=[ID]
uid=[USER_ID]
zone=[ZONE_ID]
amount=[CURRENCY_AMOUNT]
currency=[CURRENCY_TYPE]
verifier=[HASH]
open_udid=[OPEN_UDID]
udid=[UDID]
odin1=[ODIN1]
mac_sha1=[MAC_SHA1]
'''
# http://adservicecallback-footballstvappws.rhcloud.com/adcolony?id=somthi1&uid=something82&zone=superzone&udid=didyou&open_udid=eopnudid&odin1=someodin&mac_sha1=supersha&amount=200&currency=money&verifier=superkey
# $test_string="".$trans_id.$dev_id.$amt.$currency.$MY_SECRET_KEY;
@bottle.route('/adcolony')
def callback_receiver():
    param_key = ['id','uid','zone','amount','currency','verifier','open_udid','udid','odin1','mac_sha1','platform','device_model','network_type','language','country_code']
    param_value = {}
    trans_id = ' '
    for i in range(len(param_key)):
        if i == 0:
            trans_id = bottle.request.GET[param_key[i]]
        else:
            server_request = ''
            try:
                server_request = bottle.request.GET[param_key[i]]
            except:
                server_request = ''
            if server_request is not None:
                param_value[param_key[i]] = server_request

    param_value['called_time'] =  datetime.datetime.now()
    return insert_callback(trans_id, param_value)

@bottle.route('/showtransactions')
def show_all_transactions():
    datadict = get_transaction()
    if len(datadict) > 0:
        return parse_to_json_str(datadict)
    else:
        return str('vc_decline')

@bottle.route('/deletetransactions')
def delete_all_transactions():
    mongo_db['callback'].drop()
    return 'vc_success'

from bottle import TEMPLATE_PATH
TEMPLATE_PATH.append(os.path.join(os.environ['OPENSHIFT_HOMEDIR'],
    'runtime/repo/wsgi/views/'))


application=default_app()

#bottle.run(host='localhost', port=8080, debug=True)