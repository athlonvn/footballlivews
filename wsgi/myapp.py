from __future__ import division
from bs4 import BeautifulSoup, Tag ,NavigableString
import urllib
import urllib2
import os
import socket
import sys
import bottle
import json
import hashlib
import pymongo
import datetime
from bson import json_util
from pymongo import Connection
import collections
#------------------------------------------------------------------------
#------------------------------------------------------------------------
#-----                         Mongo Connection                     -----
#------------------------------------------------------------------------
#------------------------------------------------------------------------
mongo_con = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_HOST'],
                              int(os.environ['OPENSHIFT_MONGODB_DB_PORT']))
mongo_db = mongo_con[os.environ['OPENSHIFT_APP_NAME']]
mongo_db.authenticate(os.environ['OPENSHIFT_MONGODB_DB_USERNAME'],
                     os.environ['OPENSHIFT_MONGODB_DB_PASSWORD'])

# mongo_con = Connection('mongodb://localhost',safe=False)
# mongo_db = mongo_con['footballws']

# util functions
leagues_names = ['Premier League','Bundesliga','Serie A','Ligue 1','Primera Division']
league_alias = ['premierleague','bundesliga','seriea','ligue1','primeradivision']
collection_names = ['standing','schedule']


#------------------------------------------------------------------------
#------------------------------------------------------------------------
#-----                         Util functions                       -----
#------------------------------------------------------------------------
#------------------------------------------------------------------------
def parse_to_json_str(dict_doc):
	return str(json.dumps(dict_doc,default=json_util.default))

def hash_md5(strmsg):
	h = hashlib.md5()
	h.update(strmsg)
	return str(h.hexdigest())

def show_all_collections():
	cols = list(mongo_db.collection_names())
	return parse_to_json_str(cols[1:])

def convert_string_to_datetime(strdatetime):
	strdate, strtime = strdatetime.split(' ')
	paramdate = [int(i) for i in strdate.split('-')]
	paramtime = [int(j) for j in strtime.split(':')]
	paramdate.extend(paramtime)
	return datetime.datetime(*paramdate)

def compile_to_date_time_str(date_str, time_str):
    return date_str +' '+time_str

def create_schedule_object(league_name, match_date_time, team1, team2, score1='-',score2='-'):
    return Schedule(league_name,match_date_time,team1,team2,score1,score2)

def create_standing_object(league_name, team_name, match_play, win, draw,lose, goal_ratio, point):
    return Standing(league_name, team_name, match_play, win, draw,lose, goal_ratio, point)


# standing object
class Standing(object):
	def __init__(self,league_name, rank, team_name,match_play, win, draw, lose, goal_for, goal_agaisnt,  goal_ratio ,point):
		self.rank = int(rank)
		self.team_name = team_name
		self.league_name = league_name
		self.match_play = int(match_play)
		self.win = int(win)
		self.draw = int(draw)
		self.lose = int(lose)
		self.goal_for = int(goal_for)
		self.goal_agaisnt = int(goal_agaisnt)
		self.goal_ratio = int(goal_ratio)
		self.point =int(point)
		self.sku = hash_md5(self.league_name+self.team_name)

	def get_json(self):
		return {
			'rank':int(self.rank),
			'team_name':self.team_name,
			'league_name':self.league_name,
			'match_play':int(self.match_play),
			'win':int(self.win),
			'goal_for':int(self.goal_for),
			'goal_agaisnt':int(self.goal_agaisnt),
			'draw':int(self.draw),
			'lose':int(self.lose),
			'goal_ratio':int(self.goal_ratio),
			'point':int(self.point)
		}

# schedule object
class Schedule(object):
	def __init__(self, league_name, match_date_time, team1, team2 , score1, score2):
		self.sku = hash_md5(league_name+match_date_time.strftime('%B %d, %Y')+team1+team2)
		self.league_name = league_name
		self.match_date_time = match_date_time
		self.team1 = team1
		self.team2 = team2
		self.score1 = score1
		self.score2 = score2

	def get_json(self):
		return {
			'league_name':self.league_name,
			'match_date_time':self.match_date_time,
			'team1':self.team1,
			'team2':self.team2,
			'score1':self.score1,
			'score2':self.score2,
		}

#------------------------------------------------------------------------
#------------------------------------------------------------------------
#-----                   Data operation functions                   -----
#------------------------------------------------------------------------
#------------------------------------------------------------------------

# ----------------------- Standing processing -----------------------
def insert_standing(standing_object):
	try:
		mongo_db['standing'].update({"sku":standing_object.sku}
			,{"$set":standing_object.get_json()}, upsert=True)
	except:
		return str(sys.exc_info()[1])
	return 'Standing Done'

def update_standing(standing_object):
	try:
		mongo_db['standing'].update({"sku":standing_object.sku}
			,{"$set":standing_object.get_json()})
	except:
		return str(sys.exc_info()[1])
	return 'Standing Done'


def delete_standing(standing_sku):
	try:
		mongo_db['standing'].remove({"sku":standing_sku})
	except:
		return str(sys.exc_info()[1])
	return 'Standing Done'

def drop_standing():
	try:
		mongo_db['standing'].drop()
	except:
		return str(sys.exc_info()[1])
	return 'Standing Done'

def find_standing_by_league(league_name,sort_method = 'rank'):
	print league_name
	standing = mongo_db['standing'].find({'league_name':league_name}
		,{"_id":False,"sku":False}).sort(sort_method,1)
	rs = [m for m in standing]
	return parse_to_json_str(rs)


def find_standing(standing_sku):
	if not standing_sku: return None
	return mongo_db['standing'].find_one({ 'sku': standing_sku})
# ----------------------- Schedule processing -----------------------
def insert_schedule(schedule_object):
	try:
		mongo_db['schedule'].update({"sku":schedule_object.sku}
			,{"$set":schedule_object.get_json()},  upsert=True)
	except:
		return str(sys.exc_info()[1])
	return 'Schedule Done'

def update_schedule(schedule_object):
	try:
		mongo_db['schedule'].update({"sku":schedule_object.sku}
			,{"$set":standing_object.get_json()})
	except:
		return str(sys.exc_info()[1])
	return 'Schedule Done' 

def delete_schedule(schedule_sku):
	try:
		mongo_db['schedule'].remove({"sku":schedule_sku})
	except:
		return str(sys.exc_info()[1])
	return 'Schedule Done'

def drop_schedule():
	try:
		mongo_db['schedule'].drop()
	except:
		return str(sys.exc_info()[1])
	return 'Schedule Done'

def find_schedule(schedule_sku):
	if not schedule_sku: return None
	return mongo_db['schedule'].find_one({ 'sku': schedule_sku})

def find_schedule_by_league_and_date(leagues_name ,date_search):
	if not leagues_name: return None
	today =  datetime.datetime.strptime(date_search, '%d-%m-%Y')
	tomorrow = today + datetime.timedelta(days=1)
	data = mongo_db['schedule'].find({'match_date_time':{"$gte": today, "$lt": tomorrow},'league_name':leagues_name}
,{"_id":False,"sku":False}).sort("match_date_time",1)
	rs = [i for i in data]
	return parse_to_json_str(rs)


def find_schedule_by_league_and_date_range(leagues_name,datefrom, dateto):
	if not leagues_name: return None
	day1 =  datetime.datetime.strptime(datefrom, '%d-%m-%Y')
	day2 =  datetime.datetime.strptime(dateto, '%d-%m-%Y')
	data =  mongo_db['schedule'].find({'match_date_time':{"$gte": day1, "$lt": day2},'league_name':leagues_name}
,{"_id":False,"sku":False}).sort("match_date_time",1)
	rs = [i for i in data]
	return parse_to_json_str(rs)


# vote processing
def insert_vote_schedule():
	pass
def delete_vote_schedule(schedule_sku):
	pass
def count_vote_schedule(schedule_sku):
	pass

#------------------------------------------------------------------------
#------------------------------------------------------------------------
#-----                      Crawling functions                      -----
#------------------------------------------------------------------------
#------------------------------------------------------------------------
headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1',
	'Content-type': 'application/nx-www-form-urlencoded; charset=UTF-8',
	'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
}

league_urls_list = ['http://www.livescore.com/soccer/england/premier-league/','http://livescore.com/soccer/germany/bundesliga/',
'http://livescore.com/soccer/spain/primera-division/','http://livescore.com/soccer/france/ligue-1/'
,'http://www.livescore.com/soccer/italy/serie-a/']

leagues_names_list = ["Premier League", "Bundesliga" , "Primera Division","Ligue 1", "Serie A"]
TIME_OUT_REQUEST_PAGE = 12

def getPage(pageUrl):
	try:
		request = urllib2.Request(pageUrl)
		request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0')
		request.add_header('Accept','image/png,image/*;q=0.8,*/*;q=0.5')
		request.add_header('Accept-Language','en-US,en;q=0.5')
		request.add_header('Connection','keep-alive')
		request.add_header('Connection','www.google-analytics.com')
		return urllib2.urlopen(request,None, TIME_OUT_REQUEST_PAGE)
	except urllib2.URLError, e:
		print pageUrl+"%r"% e+"Error"
	except socket.timeout:
		print pageUrl+" Timed out!Error"
	return '0'

def get_page_soup(url):
    page = getPage(url)
    return BeautifulSoup(page)

# league_name, match_date_time, team1, team2 , score1, score2
def leech_schedule(league_name,league_url):
    rs = {}
    soup= get_page_soup(league_url+'fixtures/30-days/')
    schedule_section = soup.find('table', attrs={'class':'league-table mtn'})
    urls = schedule_section.findAll('tr')
    key , value = '', []
    match_time = ''
    for i in urls:
        match_day = i.find('th',attrs={'colspan':'4'})
        if match_day is not None:
            match_time = i.text.strip()
            key = convert_to_date_format(match_time)
            value = []
        else:
            matches = []
            tds = i.findAll('td')
            for j in range(len(tds)):
                if j == 0:
                    matches.append(convert_to_full_date_format(match_time,tds[j].text.strip()))
                else:
                    matches.append(tds[j].text.strip())
            value.append(matches)
            rs[key.strftime("%B %d, %Y")] = value
    newrs = collections.OrderedDict(sorted(rs.items(),key=lambda t:t[0]))
    for i ,j in newrs.iteritems():
        for t in j:
            s = Schedule(league_name, t[0],t[1],t[3],t[2].split('-')[0],t[2].split('-')[1])
            insert_schedule(s)
    return 'Finish Update '+league_name+' schedule in database'
# league_name, rank, team_name,match_play, win, draw, lose, goal_for, goal_agaisnt,  goal_ratio ,point
def leech_standing(league_name, league_url):
    rs = []
    soup= get_page_soup(league_url)
    schedule_section = soup.find('table', attrs={'class':'league-wc table mtn bbn'})
    urls = schedule_section.findAll('tr')
    stand = []
    for i in urls:
        tds = i.findAll('td')
        for j in range(len(tds)):
            if j > 0:
                stand.append(tds[j].text.strip())
            else:
            	stand.append(league_name)
        if len(stand) > 0:
            rs.append(stand)
            s = Standing(*stand)
            insert_standing(s)
        stand = []
    return 'Finish Update '+league_name+' standing in database'

def full_fill_date_format(datestr):
    temp_date = ''
    if(len(datestr.split(','))==1):
        return datestr+', '+ str(datetime.date.today().year)
    else:
        return datestr

def convert_to_date_format(datestr):
	date_object = datetime.datetime.strptime(full_fill_date_format(datestr), '%B %d, %Y')
	return date_object

def convert_to_full_date_format(datestr, timepart):
	date_object = datetime.datetime.strptime(full_fill_date_format(datestr)+' '+timepart, '%B %d, %Y %H:%M')
	return date_object
#------------------------------------------------------------------------
#------------------------------------------------------------------------
#-----                         Bottle routing                       -----
#------------------------------------------------------------------------
#------------------------------------------------------------------------
@bottle.route('/')
def bootle_insert_schedule():
    return 'This is sparta'


@bottle.route('/standing/<league_name>')
def get_standing_by_league(league_name):
    return find_standing_by_league(league_name)


@bottle.route('/standing/<league_name>/<sortmethod>')
def get_standing_by_league_method(league_name,sortmethod):
    return find_standing_by_league(league_name,sortmethod)

# Testing ws
@bottle.route('/')
def index():
	return "This is football ws"
# ["Premier League", "Bundesliga" , "Primera Division","Ligue 1", "Serie A"]
@bottle.route('/auto_update_schedule/<league_name>')
def auto_update_schedule_by_league(league_name):
    if league_name in leagues_names_list:
        return leech_schedule(league_name,league_urls_list[leagues_names_list.index(league_name)])
    else:
        return 'League name not found'

@bottle.route('/auto_update_standing/<league_name>')
def auto_update_schedule_by_league(league_name):
    if league_name in leagues_names_list:
        return leech_standing(league_name,league_urls_list[leagues_names_list.index(league_name)])
    else:
        return 'League name not found'

@bottle.route('/drop_db_command/<db_name>')
def drop_db_standing(db_name):
	if db_name =='standing':
		return drop_standing()
	elif db_name =='schedule':
		return drop_schedule()
	return 'Finish'

@bottle.route('/show_collections')
def show_collections():
	return show_all_collections()

# dd.mm.yyyy
@bottle.route('/get_matches/<league_name>/datefrom/<date_from>/date_to/<date_to>')
def get_matches_from_range(league_name,date_from,date_to):
    return find_schedule_by_league_and_date_range(league_name,date_from,date_to)

@bottle.route('/get_matches/<league_name>/date/<chosen_date>')
def get_matches_from_date(league_name,chosen_date):
    return find_schedule_by_league_and_date(league_name,chosen_date)

from bottle import TEMPLATE_PATH
TEMPLATE_PATH.append(os.path.join(os.environ['OPENSHIFT_HOMEDIR'],
   'runtime/repo/wsgi/views/'))
application=default_app()

#bottle.run(host='localhost', port=8080, debug=True)


#[u'1', u'Arsenal', u'7', u'5', u'1', u'1', u'14', u'8', u'6', u'16']
#for i in leech_standing('Premier League',league_urls_list[0]):
#	print i
#print find_standing_by_league('Premier League')
