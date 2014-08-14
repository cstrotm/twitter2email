twitter2email
=============

Tool to parse twitter user timeline and send tweets as email.

Inspired by rss2email (http://www.allthingsrss.com/rss2email/).

Not fully tested and debugged yet, use at your own risks.

### HOW TO USE ###
* Edit t2e.py and change the `DEFAULT_TO`, `DEFAULT_FROM` to match your mail address and the source mail address.
* Edit the SMTP server configuration if needed (Not tested yet)
* Install dependencies `pip install requests` ... 
* Create the `~/.t2e` directory and create a list of tweeter user you want to follow under `~/.t2e/t2e.conf`.
```
cat ~/.t2e/t2e.conf
binitamshah
StackCrypto
.
.
.
```
* Call the program `python t2e.py` / create a line in your crontab

### TODO ###

* User mail configuration in config file
* HTML emails
* Email date should match tweet timestamp
* Review Mail headers
* Handle possible exceptions in html fetch and parsing
