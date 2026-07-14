---
layout: post
title: Few words after Javarsovia 2010
date: '2010-08-02T23:32:00.006+02:00'
author: Tomasz Nurkiewicz
tags:
- conferences
- nosql
modified_time: '2011-03-30T19:06:55.576+02:00'
thumbnail: /assets/img/few-words-after-javarsovia-2010/1.jpg
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2281361457388887889
blogger_orig_url: https://www.nurkiewicz.com/2010/08/few-words-after-javarsovia-2010.html
---

It is never too late to mention about such a great event like [Javarsovia 2010 conference](http://www.javarsovia.pl/).
The conference was really successful, even though I was one of the speakers ;-).
If you were near Warsaw on 26th of June and missed the conference I feel really sorry for you.
But first things first.

I was really surprised not seeing long queues for the registration, so not wasting a lot of time, equipped with good-looking conference T-shirt, we went to see the first presentation.
Tomasz Bujok with his From zero to jBPM hero!
lecture did a great job introducing [jBPM](http://jboss.org/jbpm) framework.
I have seen quite a few presentations about this engine already, thankfully Tomasz made one step further in the topic and have shown some anti-patterns and other tips for jBPM developers.
This was really interesting as anyone, after reading a book or two, can have a "How-to" talk.
But having "How-not-to" talk requires knowledge and experience in the technology far beyond the typical tutorial-driven "experts".
I would really like to work with jBPM for a while, but I’m also full of concerns about the future of this framework.

I have seen Wojciech Seliga last year on [Java Developers’ Day](http://nurkiewicz.com/2009/10/yesterday-i-had-pleasure-to-participate.html), where he’s been talking about [Crucible](http://www.atlassian.com/software/crucible), code review tool his [company](http://www.spartez.com/) is developing for [Atlassian](http://www.atlassian.com/).
This time he shared with us some of his experience in working using agile methodologies.
I must admit I was pretty amazed how well they adapted Scrum, especially in the field of their relationships with customers.
Some people didn’t believe them when they promised to deliver first running software version after a week (one sprint).
But they did and this is how they achieve customer trust.
Probably one of the most successful companies implementing agile, proving it can really work and bring money.
Lots of respect to you [guys](http://www.spartez.com/en/our-people-agile-developers.html)!

Piotr Jagielski had a whole speech about test code refactoring (and actually – test code quality at all).
The most important idea from his lecture: if some setup/data is not important for the test, it is important to not include it in this test.
For instance, suppose you are testing that creating Person object with birth date in the future should throw IllegalArgumentException.
Unfortunately, the only available constructor requires, besides birthDate, also firstName and lastName.
Supplying fake names would do the trick, but the test method is now cluttered with irrelevant setup code.
Moreover, the reader of this test code might not be so sure about fake names irrelevancy.
Some flavor of [Builder](http://en.wikipedia.org/wiki/Builder_pattern) pattern, introduced by Piotr, is the good solution for this problem.
Or one can simply use Groovy with its [ability](http://mrhaki.blogspot.com/2009/09/groovy-goodness-using-lists-and-maps-as.html) to pass arbitrary property -\> value map to the constructor call.
I suggested Piotr he could benefit from using Groovy, but seems like he’s not using it for [testing purposes](http://www.ibm.com/developerworks/java/library/j-pg11094/index.html).

After the lunch my time has come.
[Project Voldemort](http://project-voldemort.com/) - when relation database is not enough (too much?)
lecture taken place in Boolean room (BTW: great idea of naming conference rooms after Java data types according to their size!), here is the English translation of the presentation:

...and one of the photos taken during my presentation, thanks to Javarsovia 2010 [gallery](http://www.javarsovia.pl/galeria-2.html):

[![](/assets/img/few-words-after-javarsovia-2010/1.jpg)](/assets/img/few-words-after-javarsovia-2010/1.jpg)

All about me.
For those who have seen me, hope you didn’t regret it!
Personally I would choose Sławomir Sobótka talk about design patterns, so thank you for choosing me instead :-).

Many times I was a bit jealous of American speakers, but after seeing Paweł Lipiński (and [Dawid Weiss](http://nurkiewicz.com/2010/05/impressions-after-geecon-2010.html) few month earlier) I find some Polish speakers being at least as charismatic and entertaining as those coming from the other side of the Ocean.
Paweł came out with a toothbrush in his mouth, wearing a dressing-gown.
Instantly everybody knew that he’s going to talk about clean...
not code, but tests - although wonderful Uncle Bob’s [book](http://www.amazon.com/gp/product/0132350882?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0132350882) has been mentioned many times.

The truth is, I keep hearing the same things about TDD over and over.
Same techniques, same principles, same dos and donts.
But still some people live in their caves and don’t realize how could they benefit by using TDD (and even unit testing at all!)
Some time ago a friend of mine, after developing in [Wicket](http://wicket.apache.org/) for a few months (and hundreds of my persuasions), finally tried out [WicketTester](https://cwiki.apache.org/WICKET/unit-test.html) class.
"It’s great", he said, "how could I live without it?"
If only I had such a charisma and experience like Paweł, maybe he would have tried earlier.
Why can’t people wake up and keep manually testing their code, redeploying and restarting EARs over and over?
If Paweł’s talk didn’t opened their eyes, they should at least be ashamed.
It was not a developer or project manager lecture.
He looked more like a rock-star, shouting with anger, desperately trying to convince the audience.
Next time I will attend Paweł Lipiński’s talk, even if it will be on National Crocheting Congress.
Great job, wonderful speech.

I really couldn’t wait to see Jarosław Pałka cross-sectional talk on NoSQL.
Unfortunately, being short on time, he only managed to show [Neo4j](http://neo4j.org/) database and skipped promised [CouchDB](http://www.oracle.com/technetwork/database/berkeleydb/overview/index.html) and BerkeleyDB.
Although Neo4j is the most interesting NoSQL software from these three, it’s a shame there was no time for other players.
The speaker had some technical issues while running the examples and focused too much on irrelevant details.
Too bad, because the beginning of the lecture was very promising.
I would really like to hear the lecture again, but it seemed to lack one or two days of preparation.

I must say Javarsovia 2010 was a really successful conference, that could easily compete with [GeeCON](http://2010.geecon.org/) or [JDD](http://jdd.org.pl/).
More than 600 attendees, 4 independent tracks and very good organization.
Oh, did I mention the conference was completely free, including after party in pub?
See you next year, good job!
