---
layout: post
title: Impressions after GeeCON 2010
date: '2010-05-16T18:37:00.003+02:00'
author: Tomasz Nurkiewicz
tags:
- conferences
- jpa
- warsaw-jug
- gorm
- hades
modified_time: '2010-05-16T18:41:20.729+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6769129648169860524
blogger_orig_url: https://www.nurkiewicz.com/2010/05/impressions-after-geecon-2010.html
---

Two days ago I came back from [Poznań](http://en.wikipedia.org/wiki/Pozna%C3%85%C2%84), Poland, where second edition of [GeeCON](http://2010.geecon.org/) conference took place.
After [attending the first edition](http://nurkiewicz.com/2009/05/relacja-z-geecon-2009-w-krakowie.html) my expectations were very high and sadly I left Poznań a bit disappointed.
It is most likely a matter of my personal taste, but still just a few presentations are worth mentioning.

The biggest surprise and most fabulous piece of lecture has been given by [Dawid Weiss](http://www.cs.put.poznan.pl/dweiss/xml/index.xml?lang=en) on Java in high-performance computing.
He managed to combine great show with lots of non-trivial examples.
Lots of humour, brilliant slides and great contact with the audience.
One of the most charismatic speakers I have seen.
But on the other hand it was not a stand-up comedy, where you have lots of fun during the lecture but you don’t gain anything useful after them.
Dawid given plenty of examples and micro-benchmarks during his speech, making us believe that tuning, benchmarking and even studying bytecode and assembly language might be interesting.
Bravo for Dawid, I was really proud to see Polish speaker doing so well.
Dawid also mentioned about his library [HPPC](http://labs.carrotsearch.com/hppc.html), besides I found pretty amazing search clustering tool called [Carrot2](http://search.carrot2.org/), authored by his company.

Dawids’ speech has been mentioned several times by [Holly Cummins](http://hollycummins.blogspot.com/) in her lecture: Java Performance Tuning - not so scary after all.
It was quite good presentation with nice demo and good slides.
It is true that all performance-related Java speeches are similar (few months ago I have seen [Kirk Pepperdine](http://www.kodewerk.com/) presentation on [Warsaw JUG](http://groups.google.com/group/warszawa-jug) and it had pretty similar structure) but still it is worth to know as much as possible when you need to instantly discover performance bottlenecks in your application.

But before Holly I must mention about [Ed Burns](http://www.java.net/blogs/edburns)’ talk Secrets of the Rockstar Programmers.
Presentation was based mainly on [his book](http://www.amazon.com/Secrets-Rock-Star-Programmers-Riding/dp/0071490833) and consisted many audio-video interviews.
Two things that stayed in my mind are levels of programmers ignorance and underlying the importance of using your good tools.
Learning all these silly keyboard shortcuts and knowing absolutely everything about your debugger capabilities is important and makes you much more productive in both reading and writing code.

[Oliver Gierkes'](http://www.olivergierke.de/) talk maybe wasn’t outstanding, but the tool he presented, [Hades](http://hades.synyx.org/), was.
If you are writing DAO layer using JPA, Hades greatly simplifies development.
Basic idea behind this tool is that you provide only an interface for DAO service and Hades will do its best to dynamically implement your DAO.
Basic CRUD with paging and sorting is given out-of-box, but Hades can also generate queries based on method name and arguments.
If you enjoy [GORM](http://www.grails.org/GORM), definitely try this library.
And my enthusiasm has nothing to do with the [SpringSource](http://www.springsource.com/) memory stick I got for asking a question ;-).

Although I am a backend guy, I found HTML5 Web Sockets: All-You-Can-Eat Real Time!
presentation by [Peter Lubbers](http://www.kaazing.com/) very interesting.
Co-author of [Pro HTML5 Programming](http://www.amazon.com/Pro-HTML5-Programming-Application-Development/dp/1430227907) uncovered weaknesses of [AJAX](http://en.wikipedia.org/wiki/Ajax_%28programming%29) and [Comet](http://en.wikipedia.org/wiki/Comet_%28programming%29) and presented a remedy: [Web Sockets](http://en.wikipedia.org/wiki/Web_Sockets).
After some brief theory behind asynchronous web communication, he showed few examples of web applications using Comet and web sockets.
[Firebug](http://getfirebug.com/) and [Wireshark](http://www.wireshark.org/) were used to help us deeply understand what is happening behind the scenes.
Very good, straightforward lecture without unnecessary "presentation sugar".

After asking the last question on the conference (I asked [Charles Nutter](http://blog.headius.com/) and [Thomas Enebo](http://railsmagazine.com/authors/38) to compare [Groovy](http://groovy.codehaus.org/) and [JRuby](http://jruby.org/), it seems they are technically and semantically equivalent, so it is basically a matter of your personal preference), me and a other employees from my company left.
GeeCON 2010 was a good conference, but only a few presentations were memorable.
Some speakers seemed to be not prepared enough, others bored me completely.
I will attend the conference next year, but I would really like to see more great, charismatic speakers like Scott Davis, Mark Richards, Ted Neward or Neal Ford I happened to see on Java Developers Day.
