---
layout: post
title: 'Clean code, clean logs: logging levels are there for you (2/10)'
date: '2010-05-04T20:48:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
- slf4j
modified_time: '2010-05-20T18:36:06.685+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1919935392697843049
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html
---

Every time you are making a logging statement, you think hard which logging level is appropriate for this type of event, do you?
Somehow 90% of programmers never pay attention to logging levels, simply logging everything on the same level, typically INFO or DEBUG.
Why?
Logging frameworks have two major benefits over System.out: categories and levels.
Both allow you to selectively filter logging statements permanently or only for diagnostics time.
If you really can’t see the difference, print this table and look at it every time you start typing "log." in your IDE:

ERROR – something terribly wrong had happened, that must be investigated immediately.
No system can tolerate items logged on this level.
Example: NPE, database unavailable, mission critical use case cannot be continued.

WARN – the process might be continued, but take extra caution.
Actually I always wanted to have two levels here: one for obvious problems where work-around exists (for example: "Current data unavailable, using cached values") and second (name it: ATTENTION) for potential problems and suggestions.
Example: "Application running in development mode" or "Administration console is not secured with a password".
The application can tolerate warning messages, but they should always be justified and examined.

INFO – Important business process has finished.
In ideal world, administrator or advanced user should be able to understand INFO messages and quickly find out what the application is doing.
For example if an application is all about booking airplane tickets, there should be only one INFO statement per each ticket saying "\[Who\] booked ticket from \[Where\] to \[Where\]".
Other definition of INFO message: each action that changes the state of the application significantly (database update, external system request).

DEBUG – Developers stuff.
I will discuss later what sort of information deserves to be logged.

TRACE – Very detailed information, intended only for development.
You might keep trace messages for a short period of time after deployment on production environment, but treat these log statements as temporary, that should or might be turned-off eventually.
The distinction between DEBUG and TRACE is the most difficult, but if you put logging statement and remove it after the feature has been developed and tested, it should probably be on TRACE level.

The list above is just a suggestion, you can create your own set of instructions to follow, but it is important to have any.
Although my experience is that always, everything is logged without filtering (at least from the application code), having the ability to quickly filter logs and extract the information with proper detail level might be a life-saver.

The last thing worth mentioning is infamous is\*Enabled() condition.
Some put it before every logging statement:

```java
if(log.isDebugEnabled())
    log.debug("Place for your commercial");
```

Personally, I find this idiom being just a clutter that should be avoided.
The performance improvement (especially when using [SLF4J](http://www.slf4j.org) pattern substitution discussed [previously](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)) seems irrelevant and smells like a [premature optimization](http://www.c2.com/cgi/wiki?PrematureOptimization).
Also, can you spot the duplication?
There are very rare cases when having explicit condition is justified – when we can prove that constructing logging message is expensive.
In other situations, just do your job of logging and let logging framework do its job (filtering).

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- Clean code, clean logs: logging levels are there for you (2/10)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
