import pynder
import pymysql
import robobrowser
import re
import pickle
import argparse
import pprint
import time
import random
import sys
import os 
from datetime import datetime
from tabulate import tabulate

from config import *

parent_folder = os.path.dirname(os.path.realpath(sys.argv[0]))
if not PHP_FOLDER:
	PHP_FOLDER = parent_folder

current_timestamp = datetime.now()
conn = pymysql.connect(host="127.0.0.1", port=3306, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
cur = conn.cursor()

def open_browser(url):
	if os.name == "posix":
		os.system("open /Applications/Safari.app " + url)
	else:
		os.startfile(url)

def get_facebook_token(email, password):
	MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; U; en-gb; KFTHWI Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Silk/3.16 Safari/535.19"
	FB_AUTH_URL = "https://www.facebook.com/v2.6/dialog/oauth?redirect_uri=fb464891386855067%3A%2F%2Fauthorize%2F&display=touch&state=%7B%22challenge%22%3A%22IUUkEUqIGud332lfu%252BMJhxL4Wlc%253D%22%2C%220_auth_logger_id%22%3A%2230F06532-A1B9-4B10-BB28-B29956C71AB1%22%2C%22com.facebook.sdk_client_state%22%3Atrue%2C%223_method%22%3A%22sfvc_auth%22%7D&scope=user_birthday%2Cuser_photos%2Cuser_education_history%2Cemail%2Cuser_relationship_details%2Cuser_friends%2Cuser_work_history%2Cuser_likes&response_type=token%2Csigned_request&default_audience=friends&return_scopes=true&auth_type=rerequest&client_id=464891386855067&ret=login&sdk=ios&logger_id=30F06532-A1B9-4B10-BB28-B29956C71AB1&ext=1470840777&hash=AeZqkIcf-NEW6vBd"
	
	rb = robobrowser.RoboBrowser(user_agent=MOBILE_USER_AGENT, parser="html5lib")
	
	try:
		# READ FACEBOOK COOKIES
		current_folder = os.path.dirname(os.path.realpath(sys.argv[0]))
		cookies_file = open(current_folder + "/cookies.pckl", "rb")
		cookies = pickle.load(cookies_file)
		rb.session.cookies = cookies
		cookies_file.close()
		rb.open(FB_AUTH_URL)
	except IOError:
		# FACEBOOK LOGIN
		rb.open(FB_AUTH_URL)
		login_form = rb.get_form()
		login_form["pass"] = password
		login_form["email"] = email
		rb.submit_form(login_form)
	
	# GET TOKEN
	auth_form = rb.get_form()
	rb.submit_form(auth_form, submit=auth_form.submit_fields['__CONFIRM__'])
	access_token = re.search(r"access_token=([\w\d]+)", rb.response.content.decode()).groups()[0]
		
	return access_token

parser = argparse.ArgumentParser()
parser.add_argument("-dl", help="Dislike users by IDs", nargs="+", metavar="ID")	
parser.add_argument("-L", help="Like users by IDs", nargs="+", metavar="ID")
parser.add_argument("-SL", help="Superlike users by IDs", nargs="+", metavar="ID")
parser.add_argument("-loc", help="Change location", nargs=2, metavar=("LAT", "LON"))
parser.add_argument("-v", help="Print user details", nargs="+", metavar="ID")
parser.add_argument("-p", help="""Show user pictures 
								(m: show your matches | 
								all: show all users in DB | 
								r [TIMESTAMP]: show users added after TIMESTAMP (MySQL format), defaults to current day | 
								id ID [ID ...]: show users by IDs)""", nargs="+", metavar="OPTION")
args = parser.parse_args()



# OPEN SESSION
try:
	# READ TOKEN
	access_token_file = open(parent_folder + "/access_token.txt", "r")
	access_token = access_token_file.read()
	access_token_file.close()
	session = pynder.Session(access_token)
except Exception as e:
	# UPDATE TOKEN
	access_token = get_facebook_token(FACEBOOK_USER, FACEBOOK_PASSWORD)
	access_token_file = open(parent_folder + "/access_token.txt", "w")
	access_token_file.write(access_token)
	access_token_file.close()
	session = pynder.Session(access_token)


if len(sys.argv) == 1:
	# FETCH USERS
	users = []
	for i in range(2):
		users += session.nearby_users()
	
	# SAVE USERS
	i = 0
	for user in users:
		i += 1
		try:
			cur.execute("INSERT INTO TndrAssistant (user_id, name, age, list_index, ping_time_utc, distance, instagram, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
						(user.id, user.name.decode("utf-8"), user.age, i, datetime.strptime(user.ping_time[:len(user.ping_time)-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"), round(user.distance_km,1), user.instagram_username, current_timestamp.strftime("%Y-%m-%d %H:%M"))
					   )
			conn.commit()
		except Exception as e:
			print(e)
	
	# SEARCH MATCH CANDIDATES
	for user in users:
		cur.execute("SELECT count(*) FROM TndrAssistant WHERE user_id = \"" + user.id + "\" GROUP BY record_time")
		res = cur.fetchall()
		for count in res:
			if count[0] > 1:
				cur.execute("UPDATE TndrAssistant SET match_candidate = 1 WHERE user_id = \"" + user.id + "\"")
				conn.commit()
	
	# PRINT RESULTS
	cur.execute("SELECT name, age, distance, match_candidate, user_id FROM TndrAssistant WHERE record_time = \"" + current_timestamp.strftime("%Y-%m-%d %H:%M") + "\"")
	results = cur.fetchall()
	print tabulate(results, headers=['Name', 'Age', 'Distance', 'Match candidate', 'ID'])

else:
	if args.dl:
		# USER DISLIKE
		for i in range(len(args.dl)):
			print(session._api.dislike(args.dl[i]))
			cur.execute("SELECT liked FROM TndrAssistant WHERE user_id =\"" + args.dl[i] + "\"")
			liked = cur.fetchone()
			if liked[0] == 3:
				cur.execute("UPDATE TndrAssistant SET liked = -1 WHERE user_id = \"" + args.dl[i] + "\"")
				conn.commit()
			else:
				cur.execute("UPDATE TndrAssistant SET liked = 0 WHERE user_id = \"" + args.dl[i] + "\"")
				conn.commit()
			time.sleep(random.random())
	
	if args.L:
		# USER LIKE
		for i in range(len(args.L)):
			res = session._api.like(args.L[i])
			if res["match"]:
				cur.execute("UPDATE TndrAssistant SET liked = 3 WHERE user_id = \"" + args.L[i] + "\"")
				conn.commit()
			else:
				cur.execute("UPDATE TndrAssistant SET liked = 1 WHERE user_id = \"" + args.L[i] + "\"")
				conn.commit()
			print(res)
			time.sleep(random.random())
			
	if args.SL:
		# USER SUPERLIKE
		for i in range(len(args.SL)):
			res = session._api.superlike(args.SL[i])
			if res["match"]:
				cur.execute("UPDATE TndrAssistant SET liked = 3 WHERE user_id = \"" + args.SL[i] + "\"")
				conn.commit()
			else:
				cur.execute("UPDATE TndrAssistant SET liked = 2 WHERE user_id = \"" + args.SL[i] + "\"")
				conn.commit()
			print(res)
			time.sleep(random.random())
	
	if args.loc:
		# UPDATE LOCATION
		print(session.update_location(args.loc[0], args.loc[1]))
	
	if args.v:
		# USER VERBOSE
		os.system("clear")
		for i in range(len(args.v)):
			user = session._api.user_info(args.v[i])
			pprint.pprint(user)
		
	if args.p:
		# SHOW USER PICTURES
		if args.p[0] == "all":
			cur.execute("SELECT user_id, list_index FROM TndrAssistant WHERE liked IS NULL ORDER BY list_index ASC")
			temp_list = cur.fetchall()
			id_list = []
			for i in range(len(temp_list)):
				id_list.append(temp_list[i][0])
		elif args.p[0] == "m":
			cur.execute("SELECT user_id, MAX(record_time) as rdate, MAX(liked) as liked FROM TndrAssistant WHERE match_candidate = 1 GROUP BY user_id ORDER BY rdate DESC, liked DESC")
			temp_list = cur.fetchall()
			id_list = []
			for i in range(len(temp_list)):
				id_list.append(temp_list[i][0])
		elif args.p[0] == "r":
			if len(args.p) == 1:
				timestamp = current_timestamp.strftime("%Y-%m-%d")
			else:
				timestamp = args.p[1]
			cur.execute("SELECT user_id, MIN(list_index) as ind, MAX(record_time) as rdate FROM TndrAssistant WHERE record_time > \"" + timestamp + "\" AND ((liked > 0 AND liked < 4) OR liked IS NULL) GROUP BY user_id ORDER BY rdate DESC, ind ASC")
			temp_list = cur.fetchall()
			id_list = []
			for i in range(len(temp_list)):
				id_list.append(temp_list[i][0])
		elif args.p[0] == "id":
			id_list = args.p[1:]
		else:
			print("Invalid OPTION value for -p argument, choose from '-m', '-recent', '-all', '-id'")
			exit()
		
		webpage = open(parent_folder + "/show_users.html", "w")
		webpage.write("<html><body><p style=\"text-align: right; font-size: 10pt\">D: distance [km]<br>L: your previous action on the user<br>([0] disliked, [1] liked, [2] superliked, [3] match)<br>C: database appearances count</p>\n")
		webpage.write("<form name=\"swipe_form\" action=\"" + PHP_FOLDER + "/swipe_users.php\" method=\"post\"><input type=\"submit\"></input>\n")
		for id in id_list:
			try:
				user = session._api.user_info(id)
				cur.execute("SELECT age, match_candidate, liked FROM TndrAssistant WHERE user_id = \"" + id + "\"")
				age, match_candidate, liked = cur.fetchone()
				cur.execute("SELECT count(*), MAX(record_time) as rdate FROM TndrAssistant WHERE user_id = \"" + id + "\" GROUP BY user_id")
				count, last_update = cur.fetchone()
				label = "<hr>" + user["results"]["name"] + ", " + str(age) + " - D: " + str(user["results"]["distance_mi"]*1.6) + ", L: " + str(liked) + ", C: " + str(count) + ", ID: " + user["results"]["_id"] + ", last update: " + last_update.strftime("%Y-%m-%d %H:%M:%S")
				if "instagram" in user["results"]:
					if user["results"]["instagram"]:
						label = label + " - IG: <a href=\"https://www.instagram.com/" + user["results"]["instagram"]["username"] + "/\">" + user["results"]["instagram"]["username"] + "</a>"
				if match_candidate:
					label = "<b>" + label + "</b>"
				if liked==0 or liked==4:
					label = "<font color=\"grey\">" + label + "</font>"
				elif liked==1 or liked==2:
					label = "<font color=\"blue\">" + label + "</font>"
				elif liked==3:
					label = "<font color=\"red\">" + label + "</font>"
				label = label + "<br><input type=\"radio\" name=\"" + id + "\" value=\"PASS\">do nothing<input type=\"radio\" name=\"" + id + "\" value=\"DISLIKE\">dislike<input type=\"radio\" name=\"" + id + "\" value=\"LIKE\">LIKE<input type=\"radio\" name=\"" + id + "\" value=\"SUPERLIKE\">SUPERLIKE"
				webpage.write((label+"<br>").encode("utf8"))
				for photo in user["results"]["photos"]:
					webpage.write("<a href=\"" + photo["url"] + "\"><img width=\"200\" src=\"" + photo["url"] + "\"></a>")
				webpage.write("<br>"+(user["results"]["bio"]+"<p>").encode("utf8"))
			except Exception as e:
				print(e, id)
				pass
		webpage.write("<input type=\"hidden\" name=\"parent_folder\" value=\"" + parent_folder + "\"></input>\n")
		webpage.write("<input type=\"submit\"></input></form></body></html>")
		webpage.close()
		open_browser(parent_folder + "/show_users.html")