---
layout: post
title: 'Clean code, clean logs: do you know what you are logging? (3/10)'
date: '2010-05-05T20:11:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- commons
- logging
- slf4j
modified_time: '2010-05-20T18:36:59.565+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3590187664497081988
blogger_orig_url: https://www.nurkiewicz.com/2010/05/clean-code-clean-logs-do-you-know-what.html
---

Every time you issue a logging statement, take a moment and have a look what exactly will land in your log file.
Read your logs afterwards and spot malformed sentences.
First of all, avoid NPEs like this:

```java
log.debug("Processing request with id: {}", request.getId());
```

Are you absolutely sure that request is not null here?
Another pitfall is logging collections.
If you fetched collection of domain objects from the database using [Hibernate](http://www.hibernate.org) and carelessly log them like here:

```java
log.debug("Returning users: {}", users);
```

[SLF4J](http://slf4j.org) will call toString() only when the statement is actually printed, which is quite nice.
But if it does...
Out of memory error, [N+1 select problem](http://www.realsolve.co.uk/site/tech/hib-tip-pitfall.php?name=n1selects), thread starvation (logging is synchronous!), lazy initialization exception, logs storage filled completely – each of these might occur.

It is a much better idea to log, for example, only ids of domain objects (or even only size of the collection).
But making a collection of ids when having a collection of objects having getId() method is unbelievably difficult and cumbersome in Java.
Groovy has a great [spread operator](http://groovy.codehaus.org/Operators) (users\*.id), in Java we can emulate it using [Commons Beanutils](http://commons.apache.org/beanutils) library:

```java
log.debug("Returning user ids: {}", collect(users, "id"));
```

Where collect() method can be implemented as follows:

```java
public static Collection collect(Collection collection, String propertyName) {
    return CollectionUtils.collect(collection, new BeanToPropertyValueTransformer(propertyName));
}
```

Unfortunately the method above is not yet part of Commons Beanutils framework, but I have already filed up the request to make our lives easier ([BEANUTILS-375](https://issues.apache.org/jira/browse/BEANUTILS-375)).

The last thing is improper implementation or usage of toString().
First, create toString() for each class that appears anywhere in logging statements, preferably using [ToStringBuilder](http://commons.apache.org/lang/api-release/org/apache/commons/lang/builder/ToStringBuilder.html) (but not its [reflective](http://commons.apache.org/lang/api-release/org/apache/commons/lang/builder/ReflectionToStringBuilder.html) counterpart).
Secondly, watch out for arrays and non-typical collections.
Arrays and some strange collections might not have toString() implemented calling toString() of each item.
Use [Arrays \#deepToString](http://java.sun.com/javase/6/docs/api/java/util/Arrays.html#deepToString%28java.lang.Object%5B%5D%29) JDK utility method.
And read your logs often to spot incorrectly formatted messages.

- 
- [Clean code, clean logs: use appropriate tools (1/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-use-appropriate.html)
- [Clean code, clean logs: logging levels are there for you (2/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-logging-levels.html)
- Clean code, clean logs: do you know what you are logging?
  (3/10)
- [Clean code, clean logs: avoid side effects (4/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-avoid-side.html)
- [Clean code, clean logs: concise and descriptive (5/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-concise-and.html)
- [Clean code, clean logs: tune your pattern (6/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-tune-your-pattern.html)
- [Clean code, clean logs: log method arguments and return values (7/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-method.html)
- [Clean code, clean logs: watch out for external systems (8/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-watch-out-for.html)
- [Clean code, clean logs: log exceptions properly (9/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-log-exceptions.html)
- [Clean code, clean logs: easy to read, easy to parse (10/10)](http://nurkiewicz.com/2010/05/clean-code-clean-logs-easy-to-read-easy.html)
