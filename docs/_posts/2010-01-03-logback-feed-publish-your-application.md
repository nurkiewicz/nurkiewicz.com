---
layout: post
title: 'Logback-feed: publish your application logs using Atom/RSS feed'
date: '2010-01-03T12:39:00.006+01:00'
author: Tomasz Nurkiewicz
tags:
- logging
- logback-feed
modified_time: '2010-01-03T13:03:49.296+01:00'
thumbnail: /assets/img/logback-feed-publish-your-application/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2542744773310045981
blogger_orig_url: https://www.nurkiewicz.com/2010/01/logback-feed-publish-your-application.html
---

I assume you are familiar with RSS/Atom protocol, probably you are even reading this post using [feed](http://nurkiewicz.com/feeds/posts/default) delivered by my blog.
Atom and his older brother RSS are used to publish various materials (articles, posts) allowing users to monitor multiple web sites or blogs being up to date all the time.
Can you see the advantages of this protocols arising when application logs come into play?
Application might publish its own logs as Atom/RSS feed making them easily available for anyone with a web browser or feed reader.

Of course granularity of the information is essential: system administrator could subscribe for tech-critical events, like application restarts or some major failures.
On the other hand business administrators might like to monitor the overall health of business processes, asynchronous tasks, etc. And everything with nice-and-easy user interface (see screenshots below) instead of not very friendly log files reading.

Publishing application logs using Atom or RSS protocol with Log4j is not actually a new idea ([\[1\]](http://code.google.com/p/rssappender), [\[2\]](http://old.nabble.com/log4j-RSS-ATOM-Appender-td1725283.html), [\[3\]](http://www.jroller.com/laraDAB/entry/rss_atom_log4j_appender)).
But this is not the reason why I chose [Logback](http://logback.qos.ch/) rather than Log4j to base my library.
Log-what?
Haven’t you heard about Logback?
It is the successor of Log4j (see dates in their [changes report](http://logging.apache.org/log4j/1.2/changes-report.html)...), made by the same author.
Logback has many benefits over Log4j, including improved performance and many new features.
The good news is that migration from Log4j (or other logging frameworks) is painless and requires only some JAR replacements and configuration update (see [\[4\]](http://ceki.blogspot.com/2006/12/migrate-from-log4j-to-logback-in.html) and [\[5\]](http://logback.qos.ch/manual/migrationFromLog4j.html)).
I really suggest you to upgrade (treat Logback as the new generation of Log4j), especially because Logback-feed requires this...

So, once again, why Logback?
When designing the library I came on a problem, how to communicate between appender (I thought custom appender was the only option) and feed servlet or standalone server.
As it came out, the only possibility was to use shared memory, possibly hidden behind singleton anti-pattern (yes, I said it) and nasty static variables.
So there were actually no possibilities at all.
Especially when I realized that using memory is not only resource-consuming, but also would not survive server crash.
And what is the point of having feed monitoring application crashes and restarts if all the logs before the restart are lost?
That is how I came across [JDBCAppender](http://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/jdbc/JDBCAppender.html) in Log4j.
Take a look at its [API](http://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/jdbc/JDBCAppender.html), it is hard not to notice something...
And since Logback IS the next Log4j "version", it introduced decent replacement: [DbAppender](http://logback.qos.ch/apidocs/ch/qos/logback/classic/db/DBAppender.html).
If you haven’t guessed already, both of this appenders store logging events in the database in some predefined tables.
This might introduce big overhead, but logs will survive application restart.

OK, coming back to logback-feed library, it can be found on GitHub:

<http://github.com/nurkiewicz/logback-feed>

If you want to see it in action, just download 0.0.1 release (available [here](http://github.com/nurkiewicz/logback-feed/zipball/logback-feed-0.0.1)).
After unpacking, type:

```text
mvn install
```

browse to logback-feed-examples module and run example web application:

```text
mvn jetty:run
```

Then simply use this URL in your favorite feed reader/aggregator:

http://localhost:8080/logback-feed-examples

If even this is too much for you, at least take a look at these screenshots \[\*\]:

[![](/assets/img/logback-feed-publish-your-application/1.png)](/assets/img/logback-feed-publish-your-application/1.png)
[![](/assets/img/logback-feed-publish-your-application/2.png)](/assets/img/logback-feed-publish-your-application/2.png)
[![](/assets/img/logback-feed-publish-your-application/3.png)](/assets/img/logback-feed-publish-your-application/3.png)
[![](/assets/img/logback-feed-publish-your-application/4.png)](/assets/img/logback-feed-publish-your-application/4.png)
Wouldn’t your boss or client be delighted?
Seeing most critical application logs (especially prepared, filtered and formatted) alongside her/his e-mails or opened web pages?
Opera web browser even displays pop-up window when new entries (logs) are found!
And of course any Atom/RSS capable reader would work as well (except Google Reader, unless you make your application logs feed accessible publicly on the Internet...)

Other features of Logback-feed:

- Both title and content of each log entry is customizable, so you can control what information is published.
  [PatternLayout](http://logback.qos.ch/manual/layouts.html#ClassicPatternLayout) syntax is used.
  You can see default (HTML table) on screenshots.
- Each entry can have customizable URL.
  This is typically used to point the original article or blog post, but you can use this URL to display exact .log file path (for instance on FTP or SMB server).
  See com.blogspot.nurkiewicz.logback.feed.config.EntryLinkGenerator interface.
- Easy Spring integration with Spring MVC com.blogspot.nurkiewicz.logback.feed.
  LogbackFeedController.

Before you start using Logback-feed, you must first migrate your project to Logback (if you haven’t done it already, see links above) and [configure](http://logback.qos.ch/manual/appenders.html#DBAppender) DbAppender.
But as I said, your most important task is to choose which logs to publish.
Publishing all logs is extremely bad idea, as it will slow down your application and make your feed reader go crazy.
You should carefully pick only most essential logs and send them to DbAppender.
This can be done on logger level:

```xml
<logger name="com.example.VeryImportantJob" level="INFO">
   <appender-ref ref="DB_APPENDER"/>
</logger>
```

or on appender level:

```xml
<appender name="DB_APPENDER " class="ch.qos.logback.classic.db.DBAppender">
   <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
       <level>WARN</level>
   </filter>
   <connectionSource class="ch.qos.logback.core.db.DriverManagerConnectionSource">
       <!-- -->
   </connectionSource>
</appender>
```

Hope you are encouraged enough to try my tiny library.
Merciless time does not allow me to work on this project as much as possible, but if you find it useful, please let me now!
Take a look at project site, there are few issues opened, feel free to add more if something does not work properly.
And of course, it’s open source, feel free to contribute!

\[\*\] I am very sorry for Polish labels in Internet Explorer screenshot.
Polish Is my native language and I am currently working on Polish Windows OS.
Changing language in Opera was trivial, Mozilla Firefox and Thunderbird need some hacky [tricks](http://kb.mozillazine.org/Change_Default_Mozilla_Language), but apparently to change IE language you should buy another copy of Windows – and preferably a new computer...
But I must admit, IE 8 has very nice feed reader, the only one showing categories (allows to filter logs by level or logger – or tags on my blog).
BTW I would be delighted to see other screenshots in different readers and/or of different applications.
If you have any, please send them to me!
