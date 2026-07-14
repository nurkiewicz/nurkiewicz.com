---
layout: post
title: EJB 3.1 Cookbook by Richard Reese review
date: '2011-07-21T21:15:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- review
- books
modified_time: '2011-11-17T19:23:18.307+01:00'
thumbnail: /assets/img/ejb-31-cookbook-by-richard-reese-review/1.jpg
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1002127732823020463
blogger_orig_url: https://www.nurkiewicz.com/2011/07/ejb-31-cookbook-by-richard-reese-review.html
---

Recently I received a copy of EJB 3.1 Cookbook (courtesy to [Packt Publishing](http://www.packtpub.com/)) with a kind request to prepare a review.
And since I have just got my new [Kindle reader](http://www.amazon.com/?tag=javaandneighb-20&camp=0&creative=0&linkCode=as4), this was a great opportunity to test them together.

[![](/assets/img/ejb-31-cookbook-by-richard-reese-review/1.jpg)](/assets/img/ejb-31-cookbook-by-richard-reese-review/1.jpg)

[](http://www.packtpub.com/ejb-3-1-cookbook/book)

[EJB 3.1 Cookbook](http://www.packtpub.com/ejb-3-1-cookbook/book) by Richard Reese aims to provide “*a collection of simple but incredibly effective recipes*” – quoting the subtitle.
The book covers expected part of the EJB stack: session and message-driven beans, JPA, security, interceptors, timer service and web services.
Contents are

organized around so called *recipes* – short (no more than three pages long) micro-chapters focused on one specific issue.
This is the most advantageous feature of this publication: all recipes all self-contained most of the time, so one can jump between them and apply the most suitable in given scenario.
This makes the book suitable for both the beginners, which should read it from cover to cover and slightly more experienced developers.
However the latter ones will probably prefer more comprehensive sources and skip significant parts of the book.

Although I found the book structure very convenient, contents (both granularity and volume) are highly subjective and controversial.
On the one hand the author devotes five recipes to describe separately each JMS message type (string, byte, stream, map and object) – each one is almost identical.
Whilst he could only list different types, he fills half of the JMS chapter this way (*sic!*) On the other hand, there is only one recipe explaining new JPA 2.0 Criteria API – to make matters worse, only using weakly typed queries.
Probably one of the most important new features in EJB 3.1 stack has been covered on two pages.
And this API is not particularly easy to grasp.
To depict you the scale – the art of adding Bean Validation annotations (@NotNull etc.)
on fields required ten pages and eight recipes...
Where a half-page bullet-list would suffice.

The last chapter – *EJB Techniques* – is very intriguing.
Lots of valuable and accurate tips have been given, like the difference between Date and Calendar, logging and dealing with exceptions, effective String manipulations.
Despite appearances, this is not the basic Java knowledge and many experienced programmers still don't know that SimpleDateFormat is not thread-safe and that Date class does not store time zone.
I am really happy that this kind of knowledge found its way in the book.
Unfortunately – in the wrong one.
That being said, there are more appropriate books, not focused on EJB or even Java EE.
Here it just looks like putting anything useful to reach dozen chapters in total.

There are however bright sides as well.
I particularly enjoyed *Transaction Processing* and *Interceptors* chapters.
In the former one the author briefly but succinctly explains different transaction propagation and error handling behaviours, very important topics.
Table on page 210 captures the essence of transaction demarcation in few simple rules, brilliant in its simplicity.
In the interceptors chapter the recipes are focused on typical cross-cutting concerns, forming handy starting point.
Also pretty informative.

When in comes to code examples and use-cases, they were generally interesting and well thought.
Nevertheless, I am still awfully confused after reading a recipe on @Singleton: “*We will assume that our game will never have more than one player so a singleton is an appropriate choice* ” - says the author to justify the usage of singleton to store user attributes.
Yes, I think we are all using Enterprise Java Beans and Application Servers to develop systems that would never have more than one user at a time...
(Hint: statefull session bean) The same thing with the usage of *[Facade](http://en.wikipedia.org/wiki/Facade_pattern)* pattern throughout the book.
First the author quotes the exact definition of this design pattern and then names a class wrapping EntityManager and providing convenient, strongly typed create(), remove(), findAll(), etc. - PatientFacade.
No, this class is not hiding the complexity of Patient entity, and all programmers all over the world would call this abstraction a *Repository* or *DAO*.
Not here.

By the way in the same recipe one-to-many relationship is introduced between a patient and medication, where clearly many-to-many is required.
Curiously enough, in the next recipe DISTINCT SQL statement is used to filter out duplications that have appeared due to denormalization.
Well, if the database was designed properly, there wouldn't be any duplicates on the first place...
After all these misleading and sometimes harmful advices, typos and errors in source codes (*ClassNoDefException*?
- never heard of it...)
are not that irritating.

In conclusion, despite all the deficiencies and inconsistencies, I mostly enjoyed reading this book.
Once again I will highlight the very elegant chapter-recipe structure and the fixed layout inside each recipe.
I believe it is suitable for people that suddenly inherited an EJB application and need an immediate help and suggestions.
However on the long run, they should invest in more comprehensive publication.
Few years back I managed to pass SCBCD exam (EJB 3.0 by that time) after reading [Enterprise JavaBeans 3.0](http://www.amazon.com/gp/product/059600978X/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=217145&creative=399377&creativeASIN=059600978X).
With the book in question it would be virtually impossible.
If you need a quick and dirty, yet entertaining source of ready solutions, go ahead.
Otherwise, definitely look for something broader and less verbose.
