---
layout: post
title: Spring AOP riddle demystified
date: '2009-09-20T17:03:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- aop
- spring
modified_time: '2009-09-20T17:06:55.345+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1024886805638820376
blogger_orig_url: https://www.nurkiewicz.com/2009/09/spring-aop-riddle-demystified.html
---

In one of my previous [posts](http://nurkiewicz.com/2009/08/spring-aop-riddle.html) I gave you an example of some unexpected behavior when using Spring AOP proxies.
Few days later I began to read "[Pro Spring 2.5](http://www.amazon.com/Pro-Spring-2-5-PRO-SPRING/dp/B001TKL4SC)" by Jan Machacek, Jessica Ditt, Aleksa Vukotic and Anirvan Chakraborty.
It turned out that my riddle is actually a well known problem which has more than one solution.
Also one of my Readers suggested some different approach.

This almost nine-hundred-pages book has a whole section in Chapter 6: Advanced AOP introducing the problem which I believed I have discovered.
There is even a programmatic solution, similar to EJB’s [SessionContext.getBusinessObject()](http://java.sun.com/javaee/5/docs/api/javax/ejb/SessionContext.html#getBusinessObject%28java.lang.Class%29).
But if the EJB method may be treated as somewhat standardized, using [AopContext.currentProxy()](http://static.springsource.org/spring/docs/2.5.6/api/org/springframework/aop/framework/AopContext.html#currentProxy%28%29) looks awkward and unnecessarily couples you to the Spring framework.
I almost feel guilty for telling you about this method and you should feel the same if you thought about using it.
Luckily, authors of "Pro Spring 2.5" also discourage its use.

So if you want to have in-depth understanding of Spring AOP, I suggests you to take I look at this book.
Or at least follow my blog, as I will surely present a few more concepts considering Spring AOP and AspectJ in the future.
Stay tuned!
