import subprocess
import datetime
import time
import re
from xml.dom.minidom import parseString

ENTRY="""
<entry>
    <commit_id>%s</commit_id>
    <author>
        <name>%s</name>
    </author>
    <title>%s</title>
    <published>%s</published>
</entry>
"""


def limit_feed_length(fpath, length):
    """ This is run only once every day"""
    with open(fpath, "r") as f:
        data = f.read()
    dom = parseString(data)
    print("length: ",length)
    print("no of entries: ",len(dom.getElementsByTagName('entry')))
    if len(dom.getElementsByTagName('entry')) > length:
        # If more than length get all elements at the end
        last = dom.getElementsByTagName('entry')[length:]
        print(last)
        for item in last:
            dom.documentElement.removeChild(item)
        dom.writexml(open(fpath,"w"))
    return


def write_feed(entry, fpath):
    """Write feed to the beginning of the file"""
    with open(fpath, "r+") as f:
        text = f.read()
        text = re.sub("feed</title>\n",
                      "feed</title>\n" + entry,
                      text)
        f.seek(0)
        f.write(text)
    return

def rss_feed(oldrev, newrev, refname, fpath, length):
    """Post receive hook to check start Git RSS feed"""
    try:
        latest_commit = subprocess.check_output([
            "git", "log", oldrev + ".." + newrev,
            "--pretty=format:%h|%an|%s|%at"
        ])
    except Exception as e:
        print("Exception: %s" % e)
        pass
    if latest_commit:
        print("Latest: ", latest_commit)

        commit_id, author, title, timestamp = latest_commit.split("|")
        date = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        # Entry to the RSS feed
        entry = ENTRY % (commit_id, author, title, date)
    try:
        ## Write FEED and sleep to avoid race condition
        write_feed(entry, fpath)
    except IOError as e:
        ## Avoid race condition during file write
        time.sleep(2)
        try:
            write_feed(entry, fpath)
        except IOError as e:
            print("Error writing feed", e)

    ## Limit feed length to 200
    try:
        limit_feed_length(fpath, length)
    except Exception as e:
        print("Error limiting feed size", e)
    return
