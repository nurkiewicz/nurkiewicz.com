---
layout: post
title: 'Clean code, clean logs: watch out for external systems (8/10)'
date: '2010-05-17T22:46:00.006+02:00'
author: Tomasz Nurkiewicz
tags:
- esb
- apache cxf
- mule
- web services
- logging
modified_time: '2010-05-20T18:41:22.100+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8466122454784362301
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html
---

This is the special case of the previous [tip](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html): if you communicate with any external system, consider logging every piece of data that comes out from your application and gets in.
Period.
Integration is a tough job and diagnosing problems between two applications (think two different vendors, environments, technology stacks and teams) is particularly hard.
Recently, for example, we've discovered that logging full messages contents, [including](http://cxf.apache.org/docs/debugging-and-logging.html) SOAP and HTTP headers in [Apache CXF](http://cxf.apache.org) web services is extremely useful during integration and system testing.

This is a big overhead and if performance is an issue, you can always disable logging.
But what is the point of having fast, but broken application, that no one can fix?
Be extra careful when integrating with external systems and prepare to pay that cost.
If you are lucky and all your integration is handled by ESB, bus is probably the best place to log every incoming request and response.
See for example [Mule](http://www.mulesoft.org)s' [\<log-component/\>](http://www.mulesoft.org/documentation/display/MULE2USER/Configuring+Components).

Sometimes the amount of information exchanged with external systems makes it unacceptable to log everything.
On the other hand during testing and for short period of time on production (for example when something wrong is happening) we would like to have everything saved in logs and are ready to pay performance cost.
This can be achieved by carefully using logging levels.
Just take a look at the following idiom:

```java
Collection<Integer> requestIds = //...

if(log.isDebugEnabled())
    log.debug("Processing ids: {}", requestIds);
else
    log.info("Processing ids size: {}", requestIds.size());
```

If this particular logger is configured to log DEBUG messages, it will print the whole requestIds collection contents.
But if it is configured to print INFO messages, only the size of collection will be outputted.
If you are wondering why I forgot about isInfoEnabled() condition, go back to this [tip](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html).
One thing worth mentioning is that requestIds collection should not be null in this case.
Although it will be logged correctly as null if DEBUG is enabled, but big fat NullPointerException will be thrown if logger is configured to INFO.
Remember my lesson about [side effects](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)?

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- Clean code, clean logs: watch out for external systems (8/10)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
