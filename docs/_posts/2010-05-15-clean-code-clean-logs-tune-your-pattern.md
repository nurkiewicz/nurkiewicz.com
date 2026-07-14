---
layout: post
title: 'Clean code, clean logs: tune your pattern (6/10)'
date: '2010-05-15T15:53:00.005+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
- logback
- slf4j
modified_time: '2010-05-20T18:39:40.208+02:00'
thumbnail: /assets/img/clean-code-clean-logs-tune-your-pattern/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7257385972050391509
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html
---

Logging pattern is a wonderful tool, that transparently adds meaningful context to every logging statement you make.
But you must consider very carefully which information to include in your pattern.
For example, logging date when your logs roll every hour is pointless as the date is already included in the log file name.
On the contrary, without logging thread name you would be unable to track any process using logs when two threads work concurrently – the logs will overlap.
This might be fine in single-threaded applications – that are almost dead nowadays.

From my experience, ideal logging pattern should include (of course except the logged message itself): current time (without date, milliseconds precision), logging level (if you [pay attention to it](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)), name of the thread, simple logger name (not fully qualified) and the message.
In [Logback](http://logback.qos.ch/) it is something like:

```xml
<appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
        <pattern>%d{HH:mm:ss.SSS} %-5level [%thread][%logger{0}] %m%n</pattern>
    </encoder>
</appender>
```

You should never include file name, class name and line number, although it’s very tempting.
I have even seen empty log statements issued from the code:

```java
log.info("");
```

because the programmer assumed that the line number will be a part of the logging pattern and he knew that "If empty logging message appears in 67th line of the file (in authenticate() method), it means that the user is authenticated".
Besides, logging class name, method name and/or line number has a serious performance impact.
I have prepared some simple benchmark with the following configuration:

```xml
<appender name="CLASS_INFO" class="ch.qos.logback.core.OutputStreamAppender">
    <encoder>
        <pattern>%d{HH:mm:ss.SSS} %-5level [%thread][%class{0}.%method\(\):%line][%logger{0}] %m%n</pattern>
    </encoder>
    <outputStream class="org.apache.commons.io.output.NullOutputStream"/>
</appender>
<appender name="NO_CLASS_INFO" class="ch.qos.logback.core.OutputStreamAppender">
    <encoder>
        <pattern>%d{HH:mm:ss.SSS} %-5level [%thread][LoggerTest.testClassInfo\(\):30][%logger{0}] %m%n</pattern>
    </encoder>
    <outputStream class="org.apache.commons.io.output.NullOutputStream"/>
</appender>
```

[NullOutputStream](http://commons.apache.org/io/apidocs/org/apache/commons/io/output/NullOutputStream.html) is used to eliminate I/O overhead during the test.
The following micro benchmark issues 1,5 million logging statements to CLASS_INFO and 30 million statements to NO_CLASS_INFO logger.
The latter one places some static text instead of dynamically generated class information.
First 1/3 of iterations were discarded to allow JVM warm-up.

```java
import org.junit.Test;
import org.perf4j.StopWatch;
import org.perf4j.slf4j.Slf4JStopWatch;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoggerTest {

    private static final Logger log = LoggerFactory.getLogger(LoggerTest.class);
    private static final Logger classInfoLog = LoggerFactory.getLogger("CLASS_INFO");
    private static final Logger noClassInfoLog = LoggerFactory.getLogger("NO_CLASS_INFO");

    private static final int REPETITIONS = 15;
    private static final int COUNT = 100000;

    @Test
    public void testClassInfo() throws Exception {
        for (int test = 0; test < REPETITIONS; ++test)
            testClassInfo(COUNT);
    }

    private void testClassInfo(final int count) {
        StopWatch watch = new Slf4JStopWatch("Class info");
        for (int i = 0; i < count; ++i)
            classInfoLog.info("Example message");
        printResults(count, watch);
    }

    @Test
    public void testNoClassInfo() throws Exception {
        for (int test = 0; test < REPETITIONS; ++test)
            testNoClassInfo(COUNT * 20);
    }

    private void testNoClassInfo(final int count) {
        StopWatch watch = new Slf4JStopWatch("No class info");
        for (int i = 0; i < count; ++i)
            noClassInfoLog.info("Example message");
        printResults(count, watch);
    }

    private void printResults(int count, StopWatch watch) {
        log.info("Test {} took {}ms (avg. {} ns/log)", new Object[]{
                watch.getTag(),
                watch.getElapsedTime(),
                watch.getElapsedTime() * 1000 * 1000 / count});
    }

}
```

As it turned out, on my computer the logger that produces class information reflectively worked 13 times slower (115 vs. 8.8 microseconds per logging statement, see chart below).
Being a Java developer suggests that 100 microseconds is acceptable, but this also means more than 1% of the server time is wasted when logging , let’s say, 100 statements per second.
Is it worth it?

[![](/assets/img/clean-code-clean-logs-tune-your-pattern/1.png)](/assets/img/clean-code-clean-logs-tune-your-pattern/1.png)

Somewhat more advanced feature of logging frameworks is Mapped Diagnostic Context.
[MDC](http://www.slf4j.org/api/org/slf4j/MDC.html) is simply a map managed on a thread-local basis.
You can put any key-value pair in this map and since then every logging statement issued from this thread is going to have this value attached as part of the pattern.
I need some more complex, multi threaded example to show you the benefits of this utility, so please be so kind and wait for my next articles.

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- Clean code, clean logs: tune your pattern (6/10)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
