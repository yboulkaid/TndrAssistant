import sys, os, pprint, pymysql, pynder, time
from datetime import datetime
from tabulate import tabulate
reload(sys)  
sys.setdefaultencoding('utf8')

from config import *
currentFolder = os.path.dirname(os.path.realpath(sys.argv[0]))
if not PHPFolder:
	PHPFolder = currentFolder

currentTimestamp = datetime.now()
conn = pymysql.connect(host="127.0.0.1", port=3306, user=dbUser, passwd=dbPassword, db=dbName)
cur = conn.cursor()

def open_browser(url):
	if os.name == "posix":
		os.system("open /Applications/Safari.app " + url)
	else:
		os.startfile(url)


# OPEN SESSION
try:
	# READ TOKEN
	FBtokenFile = open(currentFolder + "/FBtoken.txt", "r")
	FBtoken = FBtokenFile.read()
	FBtokenFile.close()
	session = pynder.Session(FBtoken)
except Exception as e:
	# UPDATE TOKEN
	open_browser("https://www.facebook.com/v2.6/dialog/oauth?redirect_uri=fb464891386855067%3A%2F%2Fauthorize%2F\&display=touch\&state=%7B%22challenge%22%3A%22IUUkEUqIGud332lfu%252BMJhxL4Wlc%253D%22%2C%220_auth_logger_id%22%3A%2230F06532-A1B9-4B10-BB28-B29956C71AB1%22%2C%22com.facebook.sdk_client_state%22%3Atrue%2C%223_method%22%3A%22sfvc_auth%22%7D\&scope=user_birthday%2Cuser_photos%2Cuser_education_history%2Cemail%2Cuser_relationship_details%2Cuser_friends%2Cuser_work_history%2Cuser_likes\&response_type=token%2Csigned_request\&default_audience=friends\&return_scopes=true\&auth_type=rerequest\&client_id=464891386855067\&ret=login\&sdk=ios\&logger_id=30F06532-A1B9-4B10-BB28-B29956C71AB1\&ext=1470840777\&hash=AeZqkIcf-NEW6vBd")
	FBtoken = raw_input("FBtoken: ")
	FBtokenFile = open(currentFolder + "/FBtoken.txt", "w")
	FBtokenFile.write(FBtoken)
	FBtokenFile.close()
	session = pynder.Session(FBtoken)
	pass

if len(sys.argv) == 1:
	# GET USERS
	users = []
	for i in range(2):
		users += session.nearby_users()
	
	# SAVE USERS
	i = 0
	for user in users:
		i += 1
		try:
			cur.execute("INSERT INTO Users (user_id, name, age, list_index, ping_time_utc, distance, instagram, record_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
						user.id, user.name, user.age, i, datetime.strptime(user.ping_time[:len(user.ping_time)-5],"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"), round(user.distance_km,1), user.instagram_username, currentTimestamp.strftime("%Y-%m-%d %H:%M")
						))
			conn.commit()
		except Exception as e:
			print(e)
			pass
	
	# LOOK FOR MATCH CANDIDATES
	for user in users:
		cur.execute("SELECT count(*) FROM Users WHERE user_id = \"" + user.id + "\" GROUP BY record_time")
		res = cur.fetchall()
		for count in res:
			if count[0] > 1:
				cur.execute("UPDATE Users SET match_candidate = 1 WHERE user_id = \"" + user.id + "\"")
				conn.commit()
	
	# PRINT RESULTS
	cur.execute("SELECT name, age, distance, match_candidate, user_id FROM Users WHERE record_time = \"" + currentTimestamp.strftime("%Y-%m-%d %H:%M") + "\"")
	results = cur.fetchall()
	print tabulate(results, headers=['Name', 'Age', 'Distance', 'Match candidate', 'ID'])
	
elif sys.argv[1] == "-v":
	# USER VERBOSE
	os.system("clear")
	for i in range(len(sys.argv[2:])):
		user = session._api.user_info(sys.argv[2+i])
		pprint.pprint(user)
	
elif sys.argv[1] == "-L":
	# USER LIKE
	for i in range(len(sys.argv[2:])):
		res = session._api.like(sys.argv[2+i])
		if res["match"]:
			cur.execute("UPDATE Users SET liked = 3 WHERE user_id = \"" + sys.argv[2+i] + "\"")
			conn.commit()
		else:
			cur.execute("UPDATE Users SET liked = 1 WHERE user_id = \"" + sys.argv[2+i] + "\"")
			conn.commit()
		print(res)
		time.sleep(1)

elif sys.argv[1] == "-dl":
	# USER DISLIKE
	for i in range(len(sys.argv[2:])):
		print(session._api.dislike(sys.argv[2+i]))
		cur.execute("SELECT liked FROM Users WHERE user_id =\"" + sys.argv[2+i] + "\"")
		liked = cur.fetchone()
		if liked[0] == 3:
			cur.execute("UPDATE Users SET liked = -1 WHERE user_id = \"" + sys.argv[2+i] + "\"")
			conn.commit()
		else:
			cur.execute("UPDATE Users SET liked = 0 WHERE user_id = \"" + sys.argv[2+i] + "\"")
			conn.commit()
		time.sleep(1)

elif sys.argv[1] == "-SL":
	# USER SUPERLIKE
	for i in range(len(sys.argv[2:])):
		res = session._api.superlike(sys.argv[2+i])
		if res["match"]:
			cur.execute("UPDATE Users SET liked = 3 WHERE user_id = \""+sys.argv[2+i]+"\"")
			conn.commit()
		else:
			cur.execute("UPDATE Users SET liked = 2 WHERE user_id = \""+sys.argv[2+i]+"\"")
			conn.commit()
		print(res)
		time.sleep(1)
		
elif sys.argv[1] == "-loc":
	# UPDATE LOCATION
	print(session.update_location(sys.argv[2], sys.argv[3]))
	
elif sys.argv[1] == "-p":
	# GET PHOTOS
	if sys.argv[2] == "-all":
		cur.execute("SELECT user_id, list_index FROM Users WHERE liked IS NULL ORDER BY list_index ASC")
		tempList = cur.fetchall()
		idList = []
		for i in range(len(tempList)):
			idList.append(tempList[i][0])
	elif sys.argv[2] == "-m":
		cur.execute("SELECT user_id, MAX(record_time) as rdate, MAX(liked) as liked FROM Users WHERE match_candidate = 1 GROUP BY user_id ORDER BY rdate DESC, liked DESC")
		tempList = cur.fetchall()
		idList = []
		for i in range(len(tempList)):
			idList.append(tempList[i][0])
	elif sys.argv[2] == "-recent":
		if len(sys.argv)==3:
			timestamp = currentTimestamp.strftime("%Y-%m-%d")
		elif len(sys.argv)==4:
			timestamp = sys.argv[3]
		cur.execute("SELECT user_id, MIN(list_index) as ind, MAX(record_time) as rdate FROM Users WHERE record_time > \"" + timestamp + "\" AND ((liked > 0 AND liked < 4) OR liked IS NULL) GROUP BY user_id ORDER BY rdate DESC, ind ASC")
		tempList = cur.fetchall()
		idList = []
		for i in range(len(tempList)):
			idList.append(tempList[i][0])
	else:
		idList = []
		idList.append(sys.argv[2])
	
	photosFile = open(currentFolder + "/pics.html", "w")
	photosFile.write("<html><body><p style=\"text-align: right; font-size: 10pt\">D: distance [km]<br>L: your previous action on the user<br>([0] disliked, [1] liked, [2] superliked, [3] match, [4] disliked after match)<br>C: database appearances count</p>\n")
	photosFile.write("<form name=\"swipe_form\" action=\"" + PHPFolder + "/swipe_users.php\" method=\"post\"><input type=\"submit\"></input>\n")
	for id in idList:
		try:
			user = session._api.user_info(id)
			cur.execute("SELECT age, match_candidate, liked FROM Users WHERE user_id = \"" + id + "\"")
			age, match_candidate, liked = cur.fetchone()
			cur.execute("SELECT count(*), MAX(record_time) as rdate FROM Users WHERE user_id = \"" + id + "\" GROUP BY user_id")
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
			label = label + "<br><input type=\"radio\" name=\"" + id + "\" value=\"NULL\">NULL<input type=\"radio\" name=\"" + id + "\" value=\"0\">dislike<input type=\"radio\" name=\"" + id + "\" value=\"1\">LIKE<input type=\"radio\" name=\"" + id + "\" value=\"2\">SUPERLIKE"
			photosFile.write((label+"<br>").encode("utf8"))
			for photo in user["results"]["photos"]:
				photosFile.write("<a href=\"" + photo["url"] + "\"><img width=\"200\" src=\"" + photo["url"] + "\"></a>")
			photosFile.write("<br>"+(user["results"]["bio"]+"<p>").encode("utf8"))
		except Exception as e:
			print(e, id)
			pass
	photosFile.write("<input type=\"submit\"></input></form></body></html>")
	photosFile.close()
	open_browser(currentFolder + "/pics.html")