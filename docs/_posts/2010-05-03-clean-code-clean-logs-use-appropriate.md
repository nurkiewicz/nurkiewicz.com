---
layout: post
title: 'Clean code, clean logs: use appropriate tools (1/10)'
date: '2010-05-03T23:28:00.007+02:00'
author: Tomasz Nurkiewicz
tags:
- log4j
- logging
- logback
- perf4j
- slf4j
modified_time: '2010-05-20T18:35:10.249+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8428375307768807754
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html
---

Many programmers seem to forget how logging application behavior and its current activity is important.
When somebody puts:

```java
log.info("!@#$%");
```

happily somewhere in the code, he probably don't realize the importance of application logs during maintenance, tuning and failure identification.
Underestimating the value of good logs is a terrible mistake.
I have collected few random advices that I find especially useful when it comes to writing logging routines and I will present them in a series of short articles.
First tip (out of ten) is about logging libraries and tools.

In my opinion, [SLF4J](http://www.slf4j.org/) is the best logging API available, mostly because of a great pattern substitution support:

```java
log.debug("Found {} records matching filter: '{}'", records, filter);
```

In Log4j you would have to use:

```java
log.debug("Found " + records + " records matching filter: '" + filter + "'");
```

This is not only longer and less readable, but also inefficient because of extensive use of string concatenation.
SLF4J adds nice {} substitution feature.
Also, because string concatenation is avoided and toString() is not called if the logging statement is filtered, there is no need for isDebugEnabled() anymore.
BTW, have you noticed [single quotes](http://www.javapractices.com/topic/TopicAction.do?Id=204) around filter string parameter?

SLF4J is just a façade, as an implementation I would recommend [Logback](http://logback.qos.ch/) framework, [already advertised](http://nurkiewicz.com/2010/01/logback-feed-publish-your-application.html) on my blog, instead of well established [Log4J](http://logging.apache.org/log4j/1.2).
It has many interesting features (some of them will be discussed in future tips) and, [in contrary](http://logging.apache.org/log4j/1.2/changes-report.html) to Log4J, is actively developed.

The last tool to recommend is [Perf4J](http://perf4j.codehaus.org/).
To quote their motto:

Perf4J is to System.currentTimeMillis() as log4j is to System.out.println()

I've added Perf4J to one existing application under heavy load and seen it in action in few other.
Both administrators and business users were impressed by the nice graphs produced by this simple utility.
Also we were able to discover performance flaws in no time.
Perf4J itself deserves its own article, but for now just check their [Developer Guide](http://perf4j.codehaus.org/devguide.html).

To summarize, this is the ideal pom.xml excerpt to start with:

```xml
<repositories>
    <repository>
        <id>Version99</id>
        <name>Version 99 Does Not Exist Maven repository</name>
        <layout>default</layout>
        <url>http://no-commons-logging.zapto.org/mvn2</url>
    </repository>
</repositories>


<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>slf4j-api</artifactId>
    <version>1.5.11</version>
</dependency>
<dependency>
    <groupId>ch.qos.logback</groupId>
    <artifactId>logback-classic</artifactId>
    <version>0.9.20</version>
</dependency>
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>jul-to-slf4j</artifactId>
    <version>1.5.11</version>
</dependency>
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>log4j-over-slf4j</artifactId>
    <version>1.5.11</version>
</dependency>
<dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>jcl-over-slf4j</artifactId>
    <version>1.5.11</version>
</dependency>
<dependency>
    <groupId>commons-logging</groupId>
    <artifactId>commons-logging</artifactId>
    <version>99.0-does-not-exist</version>
</dependency>
```

To test this, try the following code:

```java
SLF4JBridgeHandler.install();

org.apache.log4j.Logger.getLogger("A").info("Log4J");
java.util.logging.Logger.getLogger("B").info("java.util.logging");
org.apache.commons.logging.LogFactory.getLog("C").info("commons-logging");
org.slf4j.LoggerFactory.getLogger("D").info("Logback via SLF4J");
```

As you can see, no matter which logging framework is used (we don't even have Log4J and [Commons-Logging](http://commons.apache.org/logging) on our CLASSPATH, see [99.0-does-not-exist](http://day-to-day-stuff.blogspot.com/2007/10/announcement-version-99-does-not-exist.html) version!), every logging statement is printed using Logback (see [how it works](http://www.slf4j.org/legacy.html)).
So even if your favorite libraries stick to Commons-Logging (very bad thing!
[\[1\]](http://articles.qos.ch/thinkAgain.html), [\[2\]](http://articles.qos.ch/classloader.html)) or even worse to Log4J, you don't need to include them in your project.

UPDATE: [Ceki Gülcü](http://ceki.blogspot.com) (founder of the [Log4J](http://logging.apache.org/log4j), [SLF4J](http://www.slf4j.org) and [Logback](http://logback.qos.ch) projects) suggested simplier approach to get rid of [commons-logging](http://commons.apache.org/logging) dependency (see his [comment](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html?showComment=1272961561168#c8834760945959609553)).

- 
- Clean code, clean logs: use appropriate tools (1/10)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
