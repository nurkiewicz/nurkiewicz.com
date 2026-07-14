---
layout: post
title: 'Clean code, clean logs: log exceptions properly (9/10)'
date: '2010-05-19T00:10:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
- slf4j
modified_time: '2010-05-20T18:42:05.679+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3334557185902869182
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html
---

First of all, avoid logging exceptions, let your framework or container (whatever it is) do it for you\*.
Logging exceptions is one of the most important roles of logging at all, but many programmers tend to treat logging as a way to handle the exception.
They sometimes return default value (typically null, 0 or empty string) and pretend that nothing has happened.
Other times they first log the exception and then wrap it and throw back:

```java
log.error("IO exception", e);
throw new MyCustomException(e);
```

This construct will almost always print the same stack trace two times, because something will eventually catch MyCustomException and log its cause.
Log or wrap and throw back (which is preferable), never both, otherwise your logs will be confusing.

But if we really do WANT to log the exception?
For some reason (because we don’t read APIs and documentation?), about half of the logging statements I see are wrong.
Quick quiz, which of the following log the NPE properly?

```java
try {
    Integer x = null;
    ++x;
} catch (Exception e) {
    log.error(e);        //A
    log.error(e, e);        //B
    log.error("" + e);        //C
    log.error(e.toString());        //D
    log.error(e.getMessage());        //E
    log.error(null, e);        //F
    log.error("", e);        //G
    log.error("{}", e);        //H
    log.error("{}", e.getMessage());        //I
    log.error("Error reading configuration file: " + e);        //J
    log.error("Error reading configuration file: " + e.getMessage());        //K
    log.error("Error reading configuration file", e);        //L
}
```

Surprisingly, only G and preferably L are correct!
A and B don’t even compile in [SLF4J](http://www.slf4j.org), others discard stack traces and/or print improper messages.
For example, E won’t print anything as NPE typically don’t provide any exception message and stack trace won’t be printed as well.
Remember, first argument is always the text message, write something about the nature of the problem.
Don’t include exception message, as it will be printed automatically after the log statement, preceding stack trace.
But in order to do so, you must pass the exception itself as the second argument.

\* There is one, ekhem, exception to this rule: if you throw exceptions from some remote service (RMI, EJB remote session bean, etc.), that are capable to serialize exceptions, make sure all of them are available to the client (are part of the API).
Otherwise the client will receive NoClassDefFoundError: SomeFancyException instead of "true" error.

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- Clean code, clean logs: log exceptions properly (9/10)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
