#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import requests
import json
import codecs
from HTMLParser import HTMLParser
import pickle
from os.path import expanduser
import os.path
import sys
import time
import subprocess

from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import parseaddr, formataddr


# TODO: move that to config file
# The email address messages are from by default:
DEFAULT_FROM = "user@domain"

# The email address messages are to by default:
DEFAULT_TO = "user@domain"

# TODO: Not supported yet
# 1: Send text/html messages when possible.
# 0: Convert HTML to plain text.
HTML_MAIL = 1

# TODO: Not supported yet
# 1: Generate Date header based on item's date, when possible.
# 0: Generate Date header based on time sent.
DATE_HEADER = 1

# 1: Use SMTP_SERVER to send mail.
# 0: Call /usr/sbin/sendmail to send mail.
SMTP_SEND = 0

SMTP_SERVER = "smtp.yourisp.net:25"
AUTHREQUIRED = 0 # if you need to use SMTP AUTH set to 1
SMTP_USER = 'username'  # for SMTP AUTH, set SMTP username here
SMTP_PASS = 'password'  # for SMTP AUTH, set SMTP password here

# Connect to the SMTP server using SSL
SMTP_SSL = 0

# TODO: Not supported yet
# If you have an HTTP Proxy set this in the format 'http://your.proxy.here:8080/'
PROXY=""

# To most correctly encode emails with international characters, we iterate through the list below and use the first character set that works
# Eventually (and theoretically) ISO-8859-1 and UTF-8 are our catch-all failsafes
CHARSET_LIST='US-ASCII', 'BIG5', 'ISO-2022-JP', 'ISO-8859-1', 'UTF-8'

# access to user timeline: ex: https://twitter.com/i/profiles/show/binitamshah/timeline?contextual_tweet_id=497190804268408833&include_available_features=1&include_entities=1&last_note_ts=4&max_id=497190804268408833
TWITTER_TIMELINE_TEMPLATE="https://twitter.com/i/profiles/show/%s/timeline"
TWITTER_TIMELINE_ARGS="?contextual_tweet_id=%s&include_available_features=1&include_entities=1&last_note_ts=4&max_id=%s"
TWITTER_STATUS_TEMPLATE = "https://twitter.com/%s/status/%s"

HOME = expanduser("~")
T2E_DIR = HOME+"/.t2e"
T2E_PICKLE = T2E_DIR+"/t2e.pickle"
T2E_CONF =  T2E_DIR+"/t2e.conf"

lastSeen = {}

def serialize(lastSeen):
    #print "SERIALIZING"
    f = open(T2E_PICKLE, 'wb')
    pickle.dump(lastSeen, f)

def unserialize():
    #print "READING FROM PICKLE"
    data = []
    if (os.path.isfile(T2E_PICKLE)):
        f = open(T2E_PICKLE, 'rb')
        data.append(pickle.load(f))
        return data[0]
    else:
        #print "NO PICKLE PICKLE"
        return {}

# Taken from rss2email http://www.allthingsrss.com/rss2email/
# Note: You can also override the send function.

def send(sender, recipient, subject, body, contenttype, extraheaders=None, smtpserver=None):
	"""Send an email.
	
	All arguments should be Unicode strings (plain ASCII works as well).
	
	Only the real name part of sender and recipient addresses may contain
	non-ASCII characters.
	
	The email will be properly MIME encoded and delivered though SMTP to
	localhost port 25.  This is easy to change if you want something different.
	
	The charset of the email will be the first one out of the list
	that can represent all the characters occurring in the email.
	"""

	# Header class is smart enough to try US-ASCII, then the charset we
	# provide, then fall back to UTF-8.
	header_charset = 'ISO-8859-1'
	
	# We must choose the body charset manually
	for body_charset in CHARSET_LIST:
	    try:
	        body.encode(body_charset)
	    except (UnicodeError, LookupError):
	        pass
	    else:
	        break

	# Split real name (which is optional) and email address parts
	sender_name, sender_addr = parseaddr(sender)
	recipient_name, recipient_addr = parseaddr(recipient)
	
	# We must always pass Unicode strings to Header, otherwise it will
	# use RFC 2047 encoding even on plain ASCII strings.
	sender_name = str(Header(unicode(sender_name), header_charset))
	recipient_name = str(Header(unicode(recipient_name), header_charset))
	
	# Make sure email addresses do not contain non-ASCII characters
	sender_addr = sender_addr.encode('ascii')
	recipient_addr = recipient_addr.encode('ascii')
	
	# Create the message ('plain' stands for Content-Type: text/plain)
	msg = MIMEText(body.encode(body_charset), contenttype, body_charset)
	msg['To'] = formataddr((recipient_name, recipient_addr))
	msg['Subject'] = Header(unicode(subject), header_charset)
	for hdr in extraheaders.keys():
		try:
			msg[hdr] = Header(unicode(extraheaders[hdr], header_charset))
		except:
			msg[hdr] = Header(extraheaders[hdr])
		
	fromhdr = formataddr((sender_name, sender_addr))
	msg['From'] = fromhdr

	msg_as_string = msg.as_string()
#DEPRECATED 	if QP_REQUIRED:
#DEPRECATED 		ins, outs = SIO(msg_as_string), SIO()
#DEPRECATED 		mimify.mimify(ins, outs)
#DEPRECATED 		msg_as_string = outs.getvalue()

	if SMTP_SEND:
		if not smtpserver: 
			import smtplib
			
			try:
				if SMTP_SSL:
					smtpserver = smtplib.SMTP_SSL()
				else:
					smtpserver = smtplib.SMTP()
				smtpserver.connect(SMTP_SERVER)
			except KeyboardInterrupt:
				raise
			except Exception, e:
				print >>warn, ""
				print >>warn, ('Fatal error: could not connect to mail server "%s"' % SMTP_SERVER)
				print >>warn, ('Check your config.py file to confirm that SMTP_SERVER and other mail server settings are configured properly')
				if hasattr(e, 'reason'):
					print >>warn, "Reason:", e.reason
				sys.exit(1)
					
			if AUTHREQUIRED:
				try:
					smtpserver.ehlo()
					if not SMTP_SSL: smtpserver.starttls()
					smtpserver.ehlo()
					smtpserver.login(SMTP_USER, SMTP_PASS)
				except KeyboardInterrupt:
					raise
				except Exception, e:
					print >>warn, ""
					print >>warn, ('Fatal error: could not authenticate with mail server "%s" as user "%s"' % (SMTP_SERVER, SMTP_USER))
					print >>warn, ('Check your config.py file to confirm that SMTP_SERVER and other mail server settings are configured properly')
					if hasattr(e, 'reason'):
						print >>warn, "Reason:", e.reason
					sys.exit(1)
					
		smtpserver.sendmail(sender, recipient, msg_as_string)
		return smtpserver

	else:
		try:
                        #print msg_as_string
			p = subprocess.Popen(["/usr/sbin/sendmail", recipient], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			p.communicate(msg_as_string)
			status = p.returncode
			assert status != None, "just a sanity check"
			if status != 0:
				print >>warn, ""
				print >>warn, ('Fatal error: sendmail exited with code %s' % status)
				sys.exit(1)
		except:
			print '''Error attempting to send email via sendmail. Possibly you need to configure your config.py to use a SMTP server? Please refer to the rss2email documentation or website (http://rss2email.infogami.com) for complete documentation of config.py. The options below may suffice for configuring email:
# 1: Use SMTP_SERVER to send mail.
# 0: Call /usr/sbin/sendmail to send mail.
SMTP_SEND = 0

SMTP_SERVER = "smtp.yourisp.net:25"
AUTHREQUIRED = 0 # if you need to use SMTP AUTH set to 1
SMTP_USER = 'username'  # for SMTP AUTH, set SMTP username here
SMTP_PASS = 'password'  # for SMTP AUTH, set SMTP password here
'''
			sys.exit(1)
		return None

# Fill the mail
def createEmail(name, text, timeline, link):
    from_addr = DEFAULT_FROM
    name = "Twitter: " + name
    fromhdr = formataddr((name, from_addr,))
    tohdr = DEFAULT_TO
    subjecthdr = text
    datetime = time.gmtime()
    datehdr = time.strftime("%a, %d %b %Y %H:%M:%S -0000", datetime)
    useragenthdr = "rss2email"
    extraheaders = {'Date': datehdr, 'User-Agent': useragenthdr, 'X-RSS-Feed': timeline , 'X-RSS-URL': link}
    contenttype = 'plain'
    #print "From: %s \nTo: %s \nSubject: %s \nContent: %s \nContenttype: %s\nLink: %s" % (fromhdr, tohdr, subjecthdr, text, contenttype, link)
    #smtpserver = send(fromhdr, tohdr, subjecthdr, text, contenttype, extraheaders, smtpserver)
    smtpserver = send(fromhdr, tohdr, subjecthdr, text, contenttype, extraheaders)

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    global lastSeen # dic that containt the last viewed "tweetid" by "following" names
    flag = False # tweet data
    First = True # True when reading the first tweet
    Finish = False # If true, everything that follow has already been seen
    following = "" # tweeter user name of the feed you are parsing
    last = "" # last tweet emailed on this timeline
    tweetid = "" # data-tweet-id
    tweetscreenname = "" # data-screen-name
    tweetname = "" # data-name
    text="" # content of the tweet

    def configure(self, following="", last=""):
        self.following = following
        self.last = last
    def handle_starttag(self, tag, attrs):
        #print attrs
        if self.Finish:
            return
        if tag == "div":
            for attr, value in attrs:
                if attr == 'data-tweet-id':
                    self.tweetid = value
                    if self.last == value:
                        self.Finish = True
                if attr == 'data-screen-name':
                    self.tweetscreenname = value
                if attr == 'data-name':
                    self.tweetname=value
        if tag == "p":
            for attr,value in attrs:
                if attr == 'class' and "ProfileTweet-text" in value.split():
                    self.flag=True
    def handle_endtag(self, tag):
        if self.Finish:
            return
        if tag == "p" and self.flag == True:
                #print self.tweetid + " == " + self.tweetscreenname + " == " +self.text
                createEmail(self.tweetname, self.text, TWITTER_TIMELINE_TEMPLATE % self.tweetscreenname, TWITTER_STATUS_TEMPLATE % (self.tweetscreenname, self.tweetid))
                if self.First is True:
                    lastSeen[self.following] = self.tweetid
                    self.First = False
                self.text=''
                self.tweetid=''
                self.tweetname=''
                self.tweetscreenname=''
                self.flag = False
    def handle_data(self, data):
        if self.Finish:
            return
        if self.flag == True:
                self.text += data

# fetch new tweets from user tuser since tweet with id last
def fetchFeed(tuser, last):
    url = TWITTER_TIMELINE_TEMPLATE % (tuser)
    r = requests.get(url)
    content = r.json()['items_html']
    parser = MyHTMLParser()
    parser.configure(tuser, last)
    parser.feed(content)

    # Junk.
    #with codecs.open("file.html", "w+", encoding="utf8") as textfile:
    #    textfile.write(content)
    #    textfile.close()

def main():
    # create configuration folder
    if not os.path.exists(T2E_DIR):
        os.makedirs(T2E_DIR)

    # complain if there is nothing to feed me with!
    if not os.path.isfile(T2E_CONF):
        sys.exit("t2e: put some people to follow in configuration file " + T2E_CONF)

    global lastSeen
    lastSeen = unserialize()

    with open(T2E_CONF) as f:
        tuserlist = f.readlines()
        f.close()
    
    for tuser in tuserlist:
        tuser = tuser.strip()
        last = None
        if tuser in lastSeen.keys():
            last = lastSeen[tuser]
        fetchFeed(tuser, last)

    serialize(lastSeen)

if __name__ == "__main__":
    main()
