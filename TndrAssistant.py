import pynder
import robobrowser
import requests
import re
import pickle
import argparse
import logging
import pprint
import time
import random
import sys
import os 
from datetime import datetime

from config import *

parser = argparse.ArgumentParser()
parser.add_argument("--store", help="Store new users in database", action="store_true")
parser.add_argument("--dislike", help="Dislike users by IDs", nargs="+", metavar="ID")	
parser.add_argument("--like", help="Like users by IDs", nargs="+", metavar="ID")
parser.add_argument("--superlike", help="Superlike users by IDs", nargs="+", metavar="ID")
parser.add_argument("--location", help="Change location", nargs=2, metavar=("LAT", "LON"))
parser.add_argument("--details", help="Print user details", nargs="+", metavar="ID")
parser.add_argument("--add", help="Add user to database by IDs", nargs="+", metavar="ID")
parser.add_argument("--pics", help="""Show user pictures 
								   (m: show your matches | 
								   all: show all users in DB | 
								   r [TIMESTAMP]: show users added after TIMESTAMP (MySQL format), defaults to current day | 
								   id ID [ID ...]: show users by IDs)""", nargs="+", metavar="OPTION")
args = parser.parse_args()
args_dict = vars(args)
n_args_not_empty = sum(1 for arg_value in args_dict.values() if arg_value)

requests.packages.urllib3.disable_warnings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(message)s")
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("requests").addHandler(logging.NullHandler())

if DB_NAME:
	import pymysql
	conn = pymysql.connect(host="127.0.0.1", port=3306, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
	cur = conn.cursor()

if NOTIFICATIONS_EMAIL:
	import smtplib
	server = smtplib.SMTP(SMTP_SERVER, 587)
	server.starttls()
	server.login(NOTIFICATIONS_EMAIL, SMTP_PASSWORD)

current_timestamp = datetime.now()
parent_folder = os.path.dirname(os.path.realpath(sys.argv[0]))
if not WEBSERVER_FOLDER:
	WEBSERVER_FOLDER = parent_folder


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
		# Read Facebook cookies
		cookies_file = open(parent_folder + "/cookies.pckl", "rb")
		cookies = pickle.load(cookies_file)
		rb.session.cookies = cookies
		cookies_file.close()
		rb.open(FB_AUTH_URL)
	except IOError:
		# Facebook login
		rb.open(FB_AUTH_URL)
		login_form = rb.get_form()
		login_form["pass"] = password
		login_form["email"] = email
		rb.submit_form(login_form)
	
	# Get token
	auth_form = rb.get_form()
	rb.submit_form(auth_form, submit=auth_form.submit_fields["__CONFIRM__"])
	access_token = re.search(r"access_token=([\w\d]+)", rb.response.content.decode()).groups()[0]
		
	return access_token



# OPEN SESSION
try:
	# Read token
	access_token_file = open(parent_folder + "/access_token.txt", "r")
	access_token = access_token_file.read()
	access_token_file.close()
	session = pynder.Session(access_token)
except Exception as e:
	# Update token
	access_token = get_facebook_token(FACEBOOK_USER, FACEBOOK_PASSWORD)
	access_token_file = open(parent_folder + "/access_token.txt", "w")
	access_token_file.write(access_token)
	access_token_file.close()
	session = pynder.Session(access_token)

my_profile = session._api.profile()


if n_args_not_empty==0 or args.store:
	# FETCH NEW USERS
	users = []
	for i in range(3):
		users += session.nearby_users()
	
	if args.store:
		# Save all users
		if DB_NAME:
			i = 0
			for user in users:
				i += 1
				try:
					user_name = session._api.user_info(user.id)["results"]["name"]
					print((user.id, user_name, user.age, i, datetime.strptime(user.ping_time[:len(user.ping_time)-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"), round(user.distance_km,1), my_profile["pos"]["lat"], my_profile["pos"]["lon"], user.instagram_username, 0, current_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
					cur.execute("INSERT INTO TndrAssistant (user_id, name, age, list_index, ping_time_utc, distance, my_lat, my_lon, instagram, match_candidate, content_hash, s_number, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
								(user.id, user_name, user.age, i, datetime.strptime(user.ping_time[:len(user.ping_time)-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"), round(user.distance_km,1), my_profile["pos"]["lat"], my_profile["pos"]["lon"], user.instagram_username, 0, user.content_hash, user.s_number, current_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
							   )
					conn.commit()
				except Exception as e:
					logging.exception(e)
		else:
			print("Database not set.")
			exit()
		
	# Match candidates
	id_list = [user.id for user in users]
	match_candidate_id_list = list(set([id for id in id_list if id_list.count(id)>1]))
	match_candidate_hash_list = []
	match_candidate_snumber_list = []
	for id in match_candidate_id_list:
		for user in users:
			if user.id == id:
				match_candidate_hash_list.append(user.content_hash)
				match_candidate_snumber_list.append(user.s_number)
	logging.debug(id_list)
	logging.debug(match_candidate_id_list)
	logging.debug(match_candidate_hash_list)
	logging.debug(match_candidate_snumber_list)
	logging.debug([id_list.count(id) for id in id_list])
	for i in range(len(match_candidate_id_list)):
		id = match_candidate_id_list[i]
		content_hash = match_candidate_hash_list[i]
		s_number = match_candidate_snumber_list[i]
		user = session._api.user_info(id)["results"]
		age = current_timestamp.year - int(user["birth_date"][0:4])
		ping_time = datetime.strptime(user["ping_time"][:-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
		if "instagram" in user:
			instagram_username = user["instagram"]["username"] if "username" in user["instagram"] else None
		else:
			instagram_username = None
		if AUTO_LIKE:
			res = session._api.like(id, content_hash, s_number)
			time.sleep(random.uniform(1,2))
			logging.info("Match candidate: %s, %s, %s | %s" % (id, user["name"].decode("latin-1"), age, res))
			if res["match"]:
				if DB_NAME:
					if args.store:
						cur.execute("UPDATE TndrAssistant SET match_candidate = 1, liked = 3 WHERE user_id = %s AND record_time = %s", (id, current_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
						conn.commit()
					else:
						cur.execute("INSERT INTO TndrAssistant (user_id, name, age, ping_time_utc, distance, my_lat, my_lon, instagram, match_candidate, liked, content_hash, s_number, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
									(id, user["name"], age, ping_time, round(user["distance_mi"]*1.6), my_profile["pos"]["lat"], my_profile["pos"]["lon"], instagram_username, 1, 3, content_hash, s_number, current_timestamp.strftime("%Y-%m-%d %H:%M"))
								   )
						conn.commit()
				if NOTIFICATIONS_EMAIL:
					email_body = "MIME-Version: 1.0\nContent-type: text/html\nSubject: TndrAssistant - New match\n\n"
					email_body += "%s, %s, %s<br>\n" % (user["name"], age, id)
					email_body += "%s<br>\n" % (user["bio"])
					for photo in user["photos"]:
						email_body += "<img src=\"" + photo["url"] + "\">\n"
					logging.debug(email_body)
					server.sendmail(NOTIFICATIONS_EMAIL, NOTIFICATIONS_EMAIL, email_body)
				elif NOTIFICATIONS_IFTTT_KEY:
					payload = {"value1": "TA: New match"}
					IFTTTRes = requests.post("https://maker.ifttt.com/trigger/TA_new_match/with/key/"+NOTIFICATIONS_IFTTT_KEY, data=payload)
			else:
				if DB_NAME:
					if args.store:
						cur.execute("UPDATE TndrAssistant SET match_candidate = 1, liked = 1 WHERE user_id = %s AND record_time = %s", (id, current_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
						conn.commit()
					else:
						cur.execute("INSERT INTO TndrAssistant (user_id, name, age, ping_time_utc, distance, my_lat, my_lon, instagram, match_candidate, liked, content_hash, s_number, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
									(id, user["name"], age, ping_time, round(user["distance_mi"]*1.6), my_profile["pos"]["lat"], my_profile["pos"]["lon"], instagram_username, 1, 1, content_hash, s_number, current_timestamp.strftime("%Y-%m-%d %H:%M"))
								   )
						conn.commit()
		else:
			logging.info("Match candidate: %s, %s, %s" % (id, user["name"].decode("latin-1"), age))
			if DB_NAME:
				num_rows = cur.execute("SELECT * FROM TndrAssistant WHERE user_id = \"" + id + "\" AND match_candidate = 1 AND liked IS NULL")
				if num_rows == 0:
					if args.store:
						cur.execute("UPDATE TndrAssistant SET match_candidate = 1 WHERE user_id = %s AND record_time = %s", (id, current_timestamp.strftime("%Y-%m-%d %H:%M:%S")))
						conn.commit()
					else:
						cur.execute("INSERT INTO TndrAssistant (user_id, name, age, ping_time_utc, distance, my_lat, my_lon, instagram, match_candidate, content_hash, s_number, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
									(id, user["name"], age, ping_time, round(user["distance_mi"]*1.6), my_profile["pos"]["lat"], my_profile["pos"]["lon"], instagram_username, 1, content_hash, s_number, current_timestamp.strftime("%Y-%m-%d %H:%M"))
								   )
						conn.commit()
					if NOTIFICATIONS_EMAIL:
						email_body = "MIME-Version: 1.0\nContent-type: text/html\nSubject: TndrAssistant - New match candidate\n\n"
						email_body += "%s, %s, %s<br>\n" % (user["name"], age, id)
						email_body += "%s<br>\n" % (user["bio"])
						for photo in user["photos"]:
							email_body += "<img src=\"" + photo["url"] + "\">\n"
						logging.debug(email_body)
						server.sendmail(NOTIFICATIONS_EMAIL, NOTIFICATIONS_EMAIL, email_body)
					elif NOTIFICATIONS_IFTTT_KEY:
						payload = {"value1": "TA: New match candidate"}
						IFTTTRes = requests.post("https://maker.ifttt.com/trigger/TA_new_match/with/key/"+NOTIFICATIONS_IFTTT_KEY, data=payload)
			else:
				if NOTIFICATIONS_EMAIL:
					email_body = "MIME-Version: 1.0\nContent-type: text/html\nSubject: TndrAssistant - New match candidate\n\n"
					email_body += "%s, %s, %s<br>\n" % (user["name"], age, id)
					email_body += "%s<br>\n" % (user["bio"])
					for photo in user["photos"]:
						email_body += "<img src=\"" + photo["url"] + "\">\n"
					logging.debug(email_body)
					server.sendmail(NOTIFICATIONS_EMAIL, NOTIFICATIONS_EMAIL, email_body)
				elif NOTIFICATIONS_IFTTT_KEY:
					payload = {"value1": "TA: New match candidate"}
					IFTTTRes = requests.post("https://maker.ifttt.com/trigger/TA_new_match/with/key/"+NOTIFICATIONS_IFTTT_KEY, data=payload)
	
	if NOTIFICATIONS_EMAIL:
		server.quit()
	logging.info("Search completed (lat: %s, lon: %s)." % (my_profile["pos"]["lat"], my_profile["pos"]["lon"]))

else:
	if args.dislike:
		# USER DISLIKE
		if DB_NAME:
			for user_triplet in args.dislike:
				id, hash, s_number = user_triplet.split("_")
				print(session._api.dislike(id, hash, s_number))
				if DB_NAME:
					cur.execute("SELECT liked FROM TndrAssistant WHERE user_id =\"" + id + "\"")
					liked = cur.fetchone()
					if liked[0] == 3:
						cur.execute("UPDATE TndrAssistant SET liked = -1 WHERE user_id = \"" + id + "\"")
						conn.commit()
					else:
						cur.execute("UPDATE TndrAssistant SET liked = 0 WHERE user_id = \"" + id + "\"")
						conn.commit()
				time.sleep(random.uniform(1,2))
		else:
			print("Database not set.")
			exit()
	
	if args.like:
		# USER LIKE
		if DB_NAME:
			for user_triplet in args.like:
				id, hash, s_number = user_triplet.split("_")
				res = session._api.like(id, hash, s_number)
				if DB_NAME:
					if res["match"]:
						cur.execute("UPDATE TndrAssistant SET liked = 3 WHERE user_id = \"" + id + "\"")
						conn.commit()
					else:
						cur.execute("UPDATE TndrAssistant SET liked = 1 WHERE user_id = \"" + id + "\"")
						conn.commit()
				print(res)
				time.sleep(random.uniform(1,2))
		else:
			print("Database not set.")
			exit()
			
	if args.superlike:
		# USER SUPERLIKE
		if DB_NAME:
			for user_triplet in args.superlike:
				id, hash, s_number = user_triplet.split("_")
				res = session._api.superlike(id, hash, s_number)
				if DB_NAME:
					if res["match"]:
						cur.execute("UPDATE TndrAssistant SET liked = 3 WHERE user_id = \"" + id + "\"")
						conn.commit()
					else:
						cur.execute("UPDATE TndrAssistant SET liked = 2 WHERE user_id = \"" + id + "\"")
						conn.commit()
				print(res)
				time.sleep(random.uniform(1,2))
		else:
			print("Database not set.")
			exit()
	
	if args.location:
		# UPDATE LOCATION
		logging.info(session.update_location(args.location[0], args.location[1]))
	
	if args.details:
		# USER DETAILS
		for id in args.details:
			user = session._api.user_info(id)
			pprint.pprint(user)
	
	if args.add:
		# ADD USER
		if DB_NAME:
			for id in args.add:
				user = session._api.user_info(id)["results"]
				logging.debug(pprint.pformat(user))
				age = current_timestamp.year - int(user["birth_date"][0:4])
				ping_time = datetime.strptime(user["ping_time"][:-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
				if "instagram" in user:
					instagram_username = user["instagram"]["username"] if "username" in user["instagram"] else None
				else:
					instagram_username = None
				cur.execute("INSERT INTO TndrAssistant (user_id, name, age, ping_time_utc, distance, my_lat, my_lon, instagram, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
							(id, user["name"], age, ping_time, round(user["distance_mi"]*1.6,1), my_profile["pos"]["lat"], my_profile["pos"]["lon"], instagram_username, current_timestamp.strftime("%Y-%m-%d %H:%M"))
						   )
				conn.commit()
				print("User %s (%s, %s) added to database." % (id, user["name"], age))
		else:
			print("Database not set.")
			exit()
		
	if args.pics:
		# SHOW USER PICTURES
		if args.pics[0]!="id" and args.pics[0]!="all" and args.pics[0]!="m" and args.pics[0]!="r":
			print("Invalid OPTION value for --pics argument, choose from \"m\", \"r\", \"all\", \"id\"")
			exit()
		if args.pics[0] == "id":
			id_list = args.pics[1:]
		else:
			if DB_NAME:
				if args.pics[0] == "all":
					cur.execute("SELECT user_id, list_index FROM TndrAssistant WHERE liked IS NULL ORDER BY list_index ASC")
					temp_list = cur.fetchall()
					id_list = []
					for i in range(len(temp_list)):
						id_list.append(temp_list[i][0])
				elif args.pics[0] == "m":
					cur.execute("SELECT user_id, MAX(record_time) as rdate, MAX(liked) as liked FROM TndrAssistant WHERE (match_candidate = 1 AND (liked >= 1 OR liked IS NULL)) OR liked = 3 GROUP BY user_id ORDER BY rdate DESC")
					temp_list = cur.fetchall()
					id_list = []
					for i in range(len(temp_list)):
						id_list.append(temp_list[i][0])
					cur.execute("SELECT user_id, MAX(record_time) as rdate, MAX(liked) as liked FROM TndrAssistant WHERE match_candidate = 1 AND liked < 1 GROUP BY user_id ORDER BY rdate DESC")
					temp_list = cur.fetchall()
					for i in range(len(temp_list)):
						id_list.append(temp_list[i][0])
				elif args.pics[0] == "r":
					if len(args.pics) == 1:
						timestamp = current_timestamp.strftime("%Y-%m-%d")
					else:
						timestamp = args.pics[1]
					cur.execute("SELECT user_id, MIN(list_index) as ind, MAX(record_time) as rdate FROM TndrAssistant WHERE record_time > \"" + timestamp + "\" AND ((liked > 0 AND liked < 4) OR liked IS NULL) GROUP BY user_id ORDER BY rdate DESC, ind ASC")
					temp_list = cur.fetchall()
					id_list = []
					for i in range(len(temp_list)):
						id_list.append(temp_list[i][0])
			else:
				print("Database not set.")
				exit()
		
		webpage = open(WEBSERVER_FOLDER + "/show_users.html", "w")
		webpage.write("<html><body><p style=\"text-align: right; font-size: 10pt\">D: distance [km]<br>L: your previous action on the user<br>([0] disliked, [1] liked, [2] superliked, [3] match)<br>C: database appearances count</p>\n")
		webpage.write("<form name=\"swipe_form\" action=\"swipe_users.php\" method=\"post\"><input type=\"submit\"></input>\n")
		for id in id_list:
			try:
				user = session._api.user_info(id)["results"]
				cur.execute("SELECT age, match_candidate, liked, content_hash, s_number, record_time FROM TndrAssistant WHERE user_id = \"" + id + "\" ORDER BY record_time DESC")
				if cur.rowcount:
					age, match_candidate, liked, content_hash, s_number, record_time = cur.fetchone()
					cur.execute("SELECT count(*), MAX(record_time) as rdate FROM TndrAssistant WHERE user_id = \"" + id + "\" GROUP BY user_id")
					count, last_update = cur.fetchone()
				else:
					age = current_timestamp.year - int(user["birth_date"][0:4])
					match_candidate = 0
					liked = "NULL"
					count = 0
					last_update = ""
				if last_update:
					last_update = last_update.strftime("%Y-%m-%d %H:%M:%S")
				label = "<hr>" + user["name"] + ", " + str(age) + " - D: " + str(user["distance_mi"]*1.6) + ", L: " + str(liked) + ", C: " + str(count) + ", ID: " + user["_id"] + ", last update: " + last_update
				if "instagram" in user:
					if user["instagram"]:
						label = label + " - IG: <a href=\"https://www.instagram.com/" + user["instagram"]["username"] + "/\">" + user["instagram"]["username"] + "</a>"
				if match_candidate:
					label = "<b>" + label + "</b>"
				if liked==0 or liked==-1:
					label = "<font color=\"grey\">" + label + "</font>"
				elif liked==1 or liked==2:
					label = "<font color=\"blue\">" + label + "</font>"
				elif liked==3:
					label = "<font color=\"red\">" + label + "</font>"
				if content_hash:
					field_name = id + "_" + content_hash + "_" + str(s_number)
				else:
					field_name = id
				label = label + "<br><input type=\"radio\" name=\"" + field_name + "\" value=\"PASS\">do nothing<input type=\"radio\" name=\"" + field_name + "\" value=\"DISLIKE\">dislike<input type=\"radio\" name=\"" + field_name + "\" value=\"LIKE\">LIKE<input type=\"radio\" name=\"" + field_name + "\" value=\"SUPERLIKE\">SUPERLIKE"
				webpage.write((label+"<br>").encode("utf8"))
				for photo in user["photos"]:
					webpage.write("<a href=\"" + photo["url"] + "\"><img width=\"200\" src=\"" + photo["url"] + "\"></a>")
				webpage.write("<br>"+(user["bio"]+"<p>").encode("utf8"))
			except Exception as e:
				logging.debug("%s (id: %s)", e, id)
		webpage.write("<input type=\"hidden\" name=\"parent_folder\" value=\"" + parent_folder + "\"></input>\n")
		webpage.write("<input type=\"submit\"></input></form></body></html>")
		webpage.close()
		try:
			open_browser(WEBSERVER_FOLDER + "/show_users.html")
		except Exception as e:
			pass