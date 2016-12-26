# TndrAssistant
TndrAssistant is a python script which can interact with your Tinder account in multiple ways. The main features are:

 - find users who already liked you, and automatically like them back to create a new match (without having to like everyone); a notification of this event can also be triggered (by means of email or [IFTTT](www.ifttt.com))
 - store all users Tinder proposes you into a database for later interaction;
 - see users pictures and details, either from your personal database or by directly providing a Tinder user ID;
 - dislike ("swipe left"), like ("swipe right"), or superlike ("swipe up") users whenever you want (you don’t have to decide at the same moment you see him/her as in the Tinder official app), either from your personal database or by directly providing a Tinder user ID.

## Installation
### Dependencies
- [pynder](https://github.com/charliewolf/pynder)
- [pymysql](https://github.com/PyMySQL/PyMySQL) (optional)
- [tabulate](https://pypi.python.org/pypi/tabulate)
- to completely automate the process of obtaining a Tinder access token, the modules [link]robobrowser, re and pickle are required; if, instead, an access token is provided manually following [this](https://gist.github.com/rtt/10403467#gistcomment-1846343) procedure, they are not necessary.

### Database (optional)
You must first set up a MySQL environment. Using your favorite tool (being [phpmyadmin](https://www.phpmyadmin.net) or the command line), you must create a new database in which you can import the empty table *Users.sql* provided in this repository. Don't forget to edit the file *config.py* with your database name, username and password.

### PHP (optional)
In order to use the "semi-automatic swiping" feature, the file *swipe_users.php* has to be put into a folder where an active PHP environment is set. After watching users' pictures, if you want to bulk like/dislike a set of users the script *swipe_users.php* will simply produce the lines to be copied in the terminal to perform those operations all at once. Otherwise, if you stick to manually copying the user IDs, a PHP environment is not needed.

## Usage
```bash
python TndrAssistant.py 
```
When called, the script *TndrAssistant.py* tries to read a Facebook access token already stored in the file *FBToken.txt* to open a Tinder session. If it doesn't succeed, it opens for you the Facebook URL from where you can get your access token, following [this](https://gist.github.com/rtt/10403467#gistcomment-1846343) procedure.
In Safari, open Web Inspector at the Network tab, then click OK in the Facebook webpage, and you find your access token in the content of the "confirm" request in the Network tab. The script asks you for the access token string, and it stores it for subsequent utilization, until it expires (in a couple of hours).
After providing a valid access token, a Tinder session is opened and a number of Tinder users are fetched and stored in the database.
Now it's possible to call the script with the following command:
```bash
python TndrAssistant.py -p -m
```
and a browser page will open, showing all the match candidates logged in the database. This is based on the assumption that Tinder shows you more frequently people who already liked you, in order to improve the chances of making a match. In particular, if a user appears twice in a session there is a high probability that is a match candidate.
From this webpage, if you set a PHP environment, you can pick your choice for each user, click the Submit button, and another page will appear with the automatically generated commands for actually performing your like/dislike intentions; this is not done by the script, instead you have to copy back those strings in the Terminal.
If you didn't set a PHP environment, you can still manually copying the IDs of the users you want to perform an action on, and issue the following commands with the desired option parameter (`-dl` for dislike, `-L` for like, `-SL` for superlike):
```bash
python TndrAssistant.py -dl|-L|-SL user_id1 [user_id2 ...]
```
Another option you have is to look for recently logged users, which shows you all the logged profiles in the database since a certain date (if omitted, default is the current date), and you can like/dislike them at your choice.
```bash
python TndrAssistant.py -p -recent 2016-11-27
```
Other options available are:
```bash
python TndrAssistant.py -p -all
```
to see all users in the database you didn't dislike, and 
```bash
python TndrAssistant.py -loc lat lon
```
to change the location where you appear in Tinder.

## Credits
This work has been done thanks to [this](https://gist.github.com/rtt/10403467) comprehensive analysis fo Tinder's APIs, and to the useful [pynder](https://github.com/charliewolf/pynder) wrapper.

## Todo
Further improvements can include:

- automatically fetch Facebook access token
- make the PHP page actually launching the python script with the correct parameters for liking/disliking users (I made a quick try with curl but ran into issues due to file permissions)

## Disclaimer
This is just a funny project about playing with Tinder unofficial APIs, please don't take it too seriously :)

## License
This work is release under MIT license.