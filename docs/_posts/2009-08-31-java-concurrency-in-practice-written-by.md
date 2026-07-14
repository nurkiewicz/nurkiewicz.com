---
layout: post
title: Short review of "Java Concurrency in Practice" and others...
date: '2009-08-31T22:27:00.005+02:00'
author: Tomasz Nurkiewicz
tags:
- refactoring
- review
- concurrency
modified_time: '2009-08-31T22:36:49.681+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6805260497134921641
blogger_orig_url: https://www.nurkiewicz.com/2009/08/java-concurrency-in-practice-written-by.html
---

"[Java Concurrency in Practice](http://www.amazon.com/Java-Concurrency-Practice-Brian-Goetz/dp/0321349601)", written by Brian Goetz et al., is not brand new, but certainly one of the best Java books I had pleasure to read.
But first two other books should be mentioned.
Few months ago I took two classic Java readings: "[Refactoring: Improving the Design of Existing Code](http://www.amazon.com/Refactoring-Improving-Design-Existing-Code/dp/0201485672)" by [Martin Fowler](http://martinfowler.com/bliki) and "[Java Puzzlers: Traps, Pitfalls, and Corner Cases](http://www.amazon.com/Java-TM-Puzzlers-Pitfalls-Corner/dp/032133678X)" by Joshua Bloch and Neal Gafter.
And I didn’t enjoy both of them.

The first mentioned book is completely outdated.
The author explain step-by-step how to perform certain refactorings manually, but nowadays any mature IDE will do those refactorings automatically in not more than two mouse clicks.
Besides, most of explained approaches are simply trivial and obvious.
If I have the same statement at the beginning of if block and else block, I don’t need a book to figure out, that those duplicated statements can be moved before if condition.
Also reading how to extract interface from existing class or advices like "rename your method so that its name better explains what it does" is wasting time of any reasonable developer.
Fowler does a great job of emphasizing the role of refactoring and unit testing, but short article with a table of major Java IDEs refactoring shortcuts is enough for today.

The latter book is a set of short Java code snippets, mostly followed by well known "what will the program print?" question.
But the real question is "why even bother?"
Do we really need to know that backslash still escapes characters in comments?
Is knowledge of every detail of Java Language Specification is really necessary to call ourselves so-called "professional developers"?
Although I have found many surprising and interesting examples in this book, it reminded me SCJP exam too much.
And it is not a compliment.

Now it’s time for the winner, "Java Concurrency in Practice".
Great thing about this reading is that it covers the subject of concurrency from all points of view.
Starting from [Amdahl's law](http://en.wikipedia.org/wiki/Amdahl%27s_law), which should be known by every software engineer taking advantage of multitasking, through the details of JVM and CPU architecture to explaining new concurrency API.
All of that in less than 400 pages.

I can’t remember when was the last time I heard how many CPU cycles does particular Java operation take – thanks to Brian Goetz I am not feeling disgusted by such a nasty technical details.
Also the author introduces many charts and does some research to discover which implementation is actually fastest for some example problem.
Besides, new Java concurrency API (thread pools, atomic primitives, collections) is introduced and discussed, also from implementation side.
For example, look at the source code of Sun’s implementation of [AtomicInteger](http://java.sun.com/javase/6/docs/api/java/util/concurrent/atomic/AtomicInteger.html), which is thread safe.
I felt pretty amazed when I discovered that synchronized keyword or any other synchronization mechanism has not been used in this class.
How is it possible while still preserving thread-safety?
This book answers many more questions.
"Java Concurrency in Practice" will not introduce you another framework, simple servlet example is probably all what you get.
But I am sure that the quality and performance of my code has improved after reading this great book.
Learn how to use threads effectively – and how to avoid them.

For something more up-to-date, I am finishing "[Programming Groovy: Dynamic Productivity for the Java Developer](http://www.amazon.com/Programming-Groovy-Productivity-Developer-Programmers/dp/1934356093)", so expect a few blog entries inspired by this book.
But I am in a hurry, because I can’t wait to start "[Modular Java: Creating Flexible Applications with OSGi and Spring](http://www.amazon.com/Modular-Java-Applications-Pragmatic-Programmers/dp/1934356409)".
So please expect OSGi soon.
