---
layout: post
title: 'Clean code, clean logs: easy to read, easy to parse (10/10)'
date: '2010-05-19T23:35:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- commons
- logging
modified_time: '2010-05-20T18:43:32.823+02:00'
thumbnail: /assets/img/clean-code-clean-logs-easy-to-read-easy/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7756002699879628937
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html
---

There are two groups of receivers particularly interested in your application logs: human beings (you might disagree, but programmers belong to this group as well) and computers (typically shell scripts written by system administrators).
Logs should be suitable for both of these groups.
If someone looking from behind your back at your application logs sees:

[![](/assets/img/clean-code-clean-logs-easy-to-read-easy/1.png)](/assets/img/clean-code-clean-logs-easy-to-read-easy/1.png)from [Wikipedia](http://commons.wikimedia.org/wiki/Category:The_Matrix)

then you were probably not reading my tips carefully enough.
The reference to famous [Clean code](http://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882) book in the title of this series is not accidental: logs should be readable and easy to understand just like the code should.

On the other hand, if your application produces half GiB of logs each hour, no man and no graphical text editor will ever manage to read them entirely.
This is where old-school [grep](http://www.gnu.org/software/grep), [sed](http://www.gnu.org/software/sed) and [awk](http://www.gnu.org/software/gawk) come in handy.
If it is possible, try to write logging messages in such a way, that they could be understood both by humans and computers, e.g. avoid formatting of numbers, use patterns that can be easily recognized by regular expressions, etc. If it is not possible, print the data in two formats:

```java
log.debug("Request TTL set to: {} ({})", new Date(ttl), ttl);
// Request TTL set to: Wed Apr 28 20:14:12 CEST 2010 (1272478452437)

final String duration = DurationFormatUtils.formatDurationWords(durationMillis, true, true);
log.info("Importing took: {}ms ({})", durationMillis, duration);
//Importing took: 123456789ms (1 day 10 hours 17 minutes 36 seconds)
```

Computers will appreciate "ms after 1970 epoch" time format, while people would be delighted seeing "1 day 10 hours 17 minutes 36 seconds" text.
BTW take a look at [DurationFormatUtils](http://commons.apache.org/lang/api-release/org/apache/commons/lang/time/DateFormatUtils.html), nice tool.

I thought this article is going to be short, but after writing it I decided to split it into 10 parts, each in separate post.
Hope you enjoyed my logging series, although still not everything has been covered.
This only proves how logging is important and how many pitfalls should be avoided.
Remember, logging code should also be clean and reading your logs is supposed to be as pleasant as reading your code.

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- [Clean code, clean logs: do you know what you are logging? (3/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- Clean code, clean logs: easy to read, easy to parse (10/10)
