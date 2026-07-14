---
layout: post
title: '"Beginning Java EE 7" by Antonio Goncalves review'
date: '2013-10-24T22:47:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- Java EE
- review
- books
modified_time: '2013-10-24T22:55:50.450+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5721445799555580877
blogger_orig_url: https://www.nurkiewicz.com/2013/10/beginning-java-ee-7-by-antonio.html
image: /assets/img/beginning-java-ee-7-by-antonio/hero.jpg
---

Don't be fooled by the "*beginning*" in the title.
[This 600-pages book](http://www.amazon.com/gp/product/B00EO03GQM/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00EO03GQM&linkCode=as2&tag=javaandneighb-20) is a comprehensive and complete walk-through of all components and technologies comprising Java EE 7 stack.
**Antonio Goncalves**, Java EE evangelist and Java Champion, wrote a reference book for all enterprise software developers.

["*Beginning Java EE 7*"](http://www.amazon.com/gp/product/B00EO03GQM/ref=as_li_ss_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00EO03GQM&linkCode=as2&tag=javaandneighb-20) is not a collection of random tutorials.
Instead this publication covers thoroughly pretty much every aspect of Java EE you might encounter on a daily basis:

- CDI (Contexts and Dependency Injection)
- JPA (Java Persistence API)
- EJB (Enterprise JavaBeans)
- JTA (Java Transaction API)
- JMS (Java Message Service)
- SOAP/REST/XML/JSON processing
- JSF (JavaServer Faces)
- ...and even more

As you can see the book covers all the layers from back-end to API and front-end development.
Moreover due to solid size of the publication each of these subjects is treated with care.
Expect plenty of end-to-end examples including maven configuration.
Sometimes the author goes a little bit too far explaining the history of each technology, how it was evolving and by what was it influenced.
Useless in my opinion but luckily such sections ("*A Brief History Of...*") are clearly separated, thus easy to skip.
Moreover some may find these boxes interesting in a way.

This is the kind of publication that you will definitely not read from cover to cover but instead go back many times, cherry-picking technologies and details you want study.
For example JPA is explained throughout as many as three chapters, I believe almost every annotation is described with concise example.

Being Kindle user I was rather disappointed with the quality of electronic edition.
Page breaks in weird places, missing bullet points, unusual fonts.
Luckily besides that I did not encountered any major shortcomings.
I found few slightly broken code samples (mainly syntax errors), probably unavoidable in such a big book (?)

At times I was left alone with nagging questions.
The author says that "*\[...\]
events in CDI are not treated asynchronously*" - this begs a questions – how to make them asynchronous, is it possible?
When I read that "*Bean Validation is available for both server-side applications as well as \[...\]
Swing, Android*" - I kept asking myself – what about client-side, JavaScript?
Similarly when there are two almost identical code samples, one with `@Resource` and another with `@Inject` annotations, a word of explanation what's the difference would be appreciated.
Finally, suggesting pre-populating database globally before all tests is controversial.
Some find this to be a poor practice since the test relies on data set up somewhere else, outside the actual test scenario, thus making them harder to maintain.

The language is understandable and pleasant to read.
I was a bit uncomfortable though with the term "*configuration by exception*" used instead of more popular (?)
"*convention over configuration*" - not to mention the word "*exception*" is a bit misleading.
I didn't found any grammar issues, maybe except awkward looking "*Constraint annotations are just regular annotations, so they must define meta-annotations*" sentence.

I can honestly recommend this book to anyone from Java EE novice (as a general learning resource) to intermediate developers – to serve as a reference.
It is not a quick and dirty tutorial but a comprehensive guide that will help you for years.
