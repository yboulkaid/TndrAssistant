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
- to completely automate the process of obtaining a Tinder access token, the modules [robobrowser](https://github.com/jmcarp/robobrowser), [re](https://docs.python.org/2/library/re.html) and [pickle](https://docs.python.org/2/library/pickle.html) are required; if, instead, an access token is provided manually following [this](https://gist.github.com/rtt/10403467#gistcomment-1846343) procedure, they are not necessary.

### Database (optional)
If you want to store users as they are fetched for subsequent processing, you can set up a MySQL environment. Using your favorite tool (being [phpmyadmin](https://www.phpmyadmin.net) or the command line), create a new database and import the empty table *TndrAssistant.sql* provided in this repository. Don't forget to edit the file *config.py* with the database name, username and password.

### PHP (optional)
If you wish to use the "semi-automatic swiping" feature, the file *swipe_users.php* has to be put into a folder where an active PHP environment is set. After watching users' pictures, if you want to bulk like/dislike a set of users the script *swipe_users.php* will simply produce the lines to be copied in the terminal to perform those operations all at once. Otherwise, if you stick to manually copying the user identifier, a PHP environment is not needed.

## Usage
```bash
python TndrAssistant.py 
```
When called, the script *TndrAssistant.py* tries to read a Facebook access token already stored in the file *access_token.txt* to open a Tinder session. If it doesn't succeed, it initiates [this](https://gist.github.com/rtt/10403467#gistcomment-1846343) procedure to retrieve it.
The script looks for repetitions in the users fetched, which means a high probability that those users have already liked you.
You can choose to `AUTO_LIKE` them, or to be simply notified of them by means of email or an IFTTT notification, by setting the variables `NOTIFICATIONS_EMAIL` and `NOTIFICATIONS_IFTTT_KEY` respectively.
If you set up a MySQL environment, you can store the retrieved users calling the script with the parameter `--store`.

TndrAssistant can also be used to see at a glance all pictures and bio of a set of users; for example, you can call it as:
```bash
python TndrAssistant.py --pics m
```
and a browser page will open, showing all the match candidates logged in the database.
From this webpage, if you set a PHP environment, you can pick your choice for each user, click the Submit button, and another page will appear with the automatically generated commands for actually performing your like/dislike intentions, you just have to copy them in Terminal.
If you didn't set a PHP environment, you can still manually copying the identifiers of the users you want to perform an action onto, and issue the following commands with the desired option parameter:
```bash
python TndrAssistant.py --dislike|--like|--superlike user_id1 [user_id2 ...]
```
Another option you have is to look for recently logged users, which shows you all the logged profiles in the database since a certain date (if omitted, default is the current date), and you can like/dislike them at your choice.
```bash
python TndrAssistant.py --pics -r 2016-11-27
```
You can also use:
```bash
python TndrAssistant.py --location lat lon
```
to change the location where you appear in Tinder.

## Credits
This work has been done thanks to [this](https://gist.github.com/rtt/10403467) comprehensive analysis fo Tinder's APIs, and to the useful [pynder](https://github.com/charliewolf/pynder) wrapper.

## Disclaimer
This is just a funny project about playing with Tinder unofficial APIs, please don't take it too seriously :)

## License
This work is release under MIT license.