---
layout: post
title: 'SiftingAppender: logging different threads to different log files'
date: '2013-04-14T13:45:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
- logback
modified_time: '2013-04-14T13:45:46.068+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3524034460938078548
blogger_orig_url: https://www.nurkiewicz.com/2013/04/siftingappender-logging-different.html
---

One novel feature of Logback is [`SiftingAppender`](http://logback.qos.ch/manual/appenders.html#SiftingAppender) ([JavaDoc](http://logback.qos.ch/apidocs/ch/qos/logback/access/sift/SiftingAppender.html)).
In short it's a proxy appender that creates one child appender per each unique value of a given runtime property.
Typically this property is taken from [MDC](http://logback.qos.ch/manual/mdc.html).
Here is an example based on the official documentation linked above:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

    <appender name="SIFT" class="ch.qos.logback.classic.sift.SiftingAppender">
        <discriminator>
            <key>userid</key>
            <defaultValue>unknown</defaultValue>
        </discriminator>
        <sift>
            <appender name="FILE-${userid}" class="ch.qos.logback.core.FileAppender">
                <file>user-${userid}.log</file>
                <layout class="ch.qos.logback.classic.PatternLayout">
                    <pattern>%d{HH:mm:ss:SSS} | %-5level | %thread | %logger{20} | %msg%n%rEx</pattern>
                </layout>
            </appender>
        </sift>
    </appender>

    <root level="ALL">
        <appender-ref ref="SIFT" />
    </root>
</configuration>
```

Notice that the `<file>` property is parameterized with `${userid}` property.
Where does this property come from?
It has to be placed in MDC.
For example in a web application using [Spring Security](http://static.springsource.org/spring-security/site/index.html) I tend to use a servlet filter with a help of [`SecurityContextHolder`](http://static.springsource.org/spring-security/site/docs/3.1.x/apidocs/org/springframework/security/core/context/SecurityContextHolder.html):

```scala
import javax.servlet._
import org.slf4j.MDC
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.core.userdetails.UserDetails

class UserIdFilter extends Filter
{
    def init(filterConfig: FilterConfig) {}

    def doFilter(request: ServletRequest, response: ServletResponse, chain: FilterChain) {
        val userid = Option(
            SecurityContextHolder.getContext.getAuthentication
        ).collect{case u: UserDetails => u.getUsername}

        MDC.put("userid", userid.orNull)
        try {
            chain.doFilter(request, response)
        } finally {
            MDC.remove("userid")
        }

    }

    def destroy() {}
}
```

Just make sure this filter is applied after Spring Security filter.
But that's not the point.
The presence of `${userid}` placeholder in the file name causes sifting appender to create one child appender for each different value of this property (thus: different user names).
Running your web application with this configuration will quickly create several log files like `user-alice.log`, `user-bob.log` and `user-unknown.log` in case of MDC property not set.

Another use case is using thread name rather than MDC property.
Unfortunately this is not built in, but can be easily plugged in using custom [`Discriminator`](http://logback.qos.ch/apidocs/ch/qos/logback/core/sift/Discriminator.html) as opposed to default [`MDCBasedDiscriminator`](http://logback.qos.ch/apidocs/ch/qos/logback/classic/sift/MDCBasedDiscriminator.html):

```java
public class ThreadNameBasedDiscriminator implements Discriminator<ILoggingEvent> {

    private static final String KEY = "threadName";

    private boolean started;

    @Override
    public String getDiscriminatingValue(ILoggingEvent iLoggingEvent) {
        return Thread.currentThread().getName();
    }

    @Override
    public String getKey() {
        return KEY;
    }

    public void start() {
        started = true;
    }

    public void stop() {
        started = false;
    }

    public boolean isStarted() {
        return started;
    }
}
```

Now we have to instruct `logback.xml` to use our custom discriminator:

```xml
<appender name="SIFT" class="ch.qos.logback.classic.sift.SiftingAppender">
    <discriminator class="com.blogspot.nurkiewicz.ThreadNameBasedDiscriminator"/>
    <sift>
        <appender class="ch.qos.logback.core.FileAppender">
            <file>app-${threadName}.log</file>
            <layout class="ch.qos.logback.classic.PatternLayout">
                <pattern>%d{HH:mm:ss:SSS} | %-5level | %logger{20} | %msg%n%rEx</pattern>
            </layout>
        </appender>
    </sift>
</appender>
```

Note that we no longer put `%thread` in `PatternLayout` - it is unnecessary as thread name is part of the log file name:

- `app-main.log`
- `app-http-nio-8080-exec-1.log`
- `app-taskScheduler-1`
- `app-ForkJoinPool-1-worker-1.log`
- ...and so forth

This is probably not the most convenient setup for server application, but on desktop where you have a limited number of focused threads like [EDT](http://en.wikipedia.org/wiki/Event_dispatching_thread), IO thread, etc. it might be a vital alternative.
