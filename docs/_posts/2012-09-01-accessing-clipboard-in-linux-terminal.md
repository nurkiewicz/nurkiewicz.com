---
layout: post
title: Accessing clipboard in Linux terminal
date: '2012-09-01T23:17:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- linux
- bash
modified_time: '2012-09-01T23:17:14.397+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2651442878637348416
blogger_orig_url: https://www.nurkiewicz.com/2012/09/accessing-clipboard-in-linux-terminal.html
image:
  path: /assets/img/accessing-clipboard-in-linux-terminal/hero.jpg
  alt: "Oslofjord as seen from Tjuvholmen"
---

On a *day-to-day* basis I am using Ubuntu, which means constantly switching between terminal window and ordinary graphical application like IDE, editors, etc. Often I need to copy a bit of text from IDE to terminal or back.
At least in Ubuntu using inconsistent *Ctrl + **Shift** + C* (or *V*) key combination and mouse to select area in terminal is a bit painful.
Life would be so much simpler if there was a command line utility to print current clipboard contents to standard terminal output and a second one to take standard input and put it into the clipboard.
Life *can* be much simpler, have a look at [`xclip`](http://linux.die.net/man/1/xclip)!
Without diving into details, start by defining the following aliases in your system (put them in `~/.bash_aliases` right now, you'll love them):

```bash
alias ctrlc='xclip -selection c'
alias ctrlv='xclip -selection c -o'
```

`ctrlc` and `ctrlv`, sounds familiar?
Of course aliases are completely arbitrary.
Now run any bash command but pipe its output to `ctrlc`:

```bash
$ ps | ctrlc
```

Nothing happened?
Open your favourite editor or any graphical application and hit *Ctrl + V*, like I just did in [ReText](https://sourceforge.net/p/retext/home/ReText/) Markdown editor:

```bash
  PID TTY          TIME CMD
 5300 pts/0    00:00:00 bash
 5389 pts/0    00:00:00 ps
 5390 pts/0    00:00:00 xclip
```

That's right, the output of [`ps`](http://linux.die.net/man/1/ps) magically appeared in my Ubuntu clipboard.
But there's more.
Put any text you want in the clipboard using *Ctrl + C* and send it to standard output of your terminal:

```bash
$ ctrlv
Accessing clipboard in Linux terminal
```

These two simple commands show their real power when used together as part of larger pipe.
Say you want to extract two most common IP addresses appearing in your `access.log` ([example](http://www.howtoforge.com/logresolvemerge.pl_merge_apache_access_logs)) and send them to your team mate over IRC or e-mail:

```bash
$ cut -f1 -d' ' access.log | sort | uniq -c | sort -n | tail -n 2 | ctrlc
```

My clipboard contents after running this command:

```bash
2 72.149.148.248
4 192.6.178.101
```

Step by step: take the first space-delimited field from `access.log` (IP), sort all IPs and count how many times each IP appears (`uniq -c`).
Finally sort by the number of occurrences, take two most common (`tail -n 2`) and copy to clipboard.
But I would like to share yet another tip with you:

#### Pretty-printing (formatting) of XML and JSON in command line.

That's right, it's also possible, with two more aliases:

```bash
alias jsonformat='python -mjson.tool'
alias xmlformat='xmllint --format -'
```

How many times you copied a piece of XML from logs or from [SoapUI](http://www.soapui.org/) which was completely unreadable due to missing newlines and indentation?
Suffer no more, say you have `<a><b><c>C1</c><c>C2</c></b><d>D</d></a>` in your clipboard.
Try this:

```bash
$ ctrlv | xmlformat
<?xml version="1.0"?>
<a>
  <b>
    <c>C1</c>
    <c>C2</c>
  </b>
  <d>D</d>
</a>
```

And what if you want to put the formatted XML back to the clipboard?
I think you already know...
Let's try something more sophisticated.
Unformatted XML and JSON is typically returned from all sorts of APIs (and we live in the API era).
Good, APIs are for computers, not for humans.

```bash
$ curl "http://search.twitter.com/search.json?q=%23Java&rpp=1"

{"completed_in":0.16,"max_id":241658217820741632,"max_id_str":"241658217820741632","next_page":"?page=2&max_id=241658217820741632&q=%23Java&rpp=1","page":1,"query":"%23Java","refresh_url":"?since_id=241658217820741632&q=%23Java","results":[{"created_at":"Fri, 31 Aug 2012 22:06:23 +0000","from_user":"DBCOOPA","from_user_id":103392633,"from_user_id_str":"103392633","from_user_name":"Anonymous","geo":null,"id":241658217820741632,"id_str":"241658217820741632","iso_language_code":"en","metadata":{"result_type":"recent"},"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2509685076\/r148jpb6pat3g2olf8zz_normal.png","profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2509685076\/r148jpb6pat3g2olf8zz_normal.png","source":"&lt;a href=&quot;http:\/\/twitter.com\/&quot;&gt;web&lt;\/a&gt;","text":"Critical bug in newest Java gives attackers complete control of PCs: http:\/\/t.co\/YjJqdQ40 #Java #Security via @ArsTechnica","to_user":null,"to_user_id":0,"to_user_id_str":"0","to_user_name":null}],"results_per_page":1,"since_id":0,"since_id_str":"0"}
```

Ouch!
But there is hope:

```bash
$ curl "http://search.twitter.com/search.json?q=%23Java&rpp=1" | jsonformat
{
    "completed_in": 0.122, 
    "max_id": 241658217820741632, 
    "max_id_str": "241658217820741632", 
    "next_page": "?page=2&max_id=241658217820741632&q=%23Java&rpp=1", 
    "page": 1, 
    "query": "%23Java", 
    "refresh_url": "?since_id=241658217820741632&q=%23Java", 
    "results": [
        {
            "created_at": "Fri, 31 Aug 2012 22:06:23 +0000", 
            "from_user": "DBCOOPA", 
            "from_user_id": 103392633, 
            "from_user_id_str": "103392633", 
            "from_user_name": "Anonymous", 
            "geo": null, 
            "id": 241658217820741632, 
            "id_str": "241658217820741632", 
            "iso_language_code": "en", 
            "metadata": {
                "result_type": "recent"
            }, 
            "profile_image_url": "http://a0.twimg.com/profile_images/2509685076/r148jpb6pat3g2olf8zz_normal.png", 
            "profile_image_url_https": "https://si0.twimg.com/profile_images/2509685076/r148jpb6pat3g2olf8zz_normal.png", 
            "source": "&lt;a href=&quot;http://twitter.com/&quot;&gt;web&lt;/a&gt;", 
            "text": "Critical bug in newest Java gives attackers complete control of PCs: http://t.co/YjJqdQ40 #Java #Security via @ArsTechnica", 
            "to_user": null, 
            "to_user_id": 0, 
            "to_user_id_str": "0", 
            "to_user_name": null
        }
    ], 
    "results_per_page": 1, 
    "since_id": 0, 
    "since_id_str": "0"
}
```

The same applies to XML documents:

```bash
$ curl "http://search.twitter.com/search.json?q=%23Java&rpp=1" | xmlformat

<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:google="http://base.google.com/ns/1.0" xmlns:openSearch="http://a9.com/-/spec/opensearch/1.1/" xmlns="http://www.w3.org/2005/Atom" xmlns:twitter="http://api.twitter.com/" xml:lang="en-US">
  <id>tag:search.twitter.com,2005:search/#Java</id>
  <link type="text/html" href="http://search.twitter.com/search?q=%23Java" rel="alternate"/>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?q=%23Java" rel="self"/>
  <title>#Java - Twitter Search</title>
  <link type="application/opensearchdescription+xml" href="http://twitter.com/opensearch.xml" rel="search"/>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?since_id=241658217820741632&amp;q=%23Java" rel="refresh"/>
  <updated>2012-08-31T22:06:23Z</updated>
  <openSearch:itemsPerPage>1</openSearch:itemsPerPage>
  <link type="application/atom+xml" href="http://search.twitter.com/search.atom?page=2&amp;max_id=241658217820741632&amp;q=%23Java&amp;rpp=1" rel="next"/>
  <entry>
    <id>tag:search.twitter.com,2005:241658217820741632</id>
    <published>2012-08-31T22:06:23Z</published>
    <link type="text/html" href="http://twitter.com/DBCOOPA/statuses/241658217820741632" rel="alternate"/>
    <title>Critical bug in newest Java gives attackers complete control of PCs: http://t.co/YjJqdQ40 #Java #Security via @ArsTechnica</title>
    <content type="html">Critical bug in newest Java gives attackers complete control of PCs: &lt;a href="http://t.co/YjJqdQ40"&gt;http://t.co/YjJqdQ40&lt;/a&gt; &lt;em&gt;&lt;a href="http://search.twitter.com/search?q=%23Java" title="#Java" class=" "&gt;#Java&lt;/a&gt;&lt;/em&gt; &lt;a href="http://search.twitter.com/search?q=%23Security" title="#Security" class=" "&gt;#Security&lt;/a&gt; via @&lt;a class=" " href="https://twitter.com/ArsTechnica"&gt;ArsTechnica&lt;/a&gt;</content>
    <updated>2012-08-31T22:06:23Z</updated>
    <link type="image/png" href="http://a0.twimg.com/profile_images/2509685076/r148jpb6pat3g2olf8zz_normal.png" rel="image"/>
    <twitter:geo/>
    <twitter:metadata>
      <twitter:result_type>recent</twitter:result_type>
    </twitter:metadata>
    <twitter:source>&lt;a href="http://twitter.com/"&gt;web&lt;/a&gt;</twitter:source>
    <twitter:lang>en</twitter:lang>
    <author>
      <name>DBCOOPA (Anonymous)</name>
      <uri>http://twitter.com/DBCOOPA</uri>
    </author>
  </entry>
</feed>
```

Possibility to access system clipboard both-ways is a life saver when working a lot with the terminal.
But it's even greater if you work with XML or JSON and you can simply type: `ctrlv | xmlformat | ctrlc` to replace unformatted clipboard content with pretty-printed version of it.
I hope you'll enjoy
