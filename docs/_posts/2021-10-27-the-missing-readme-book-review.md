---
title: "The Missing README: A Guide for the New Software Engineer book review"
tags: book review openapi graphql soap
description: >
    So instead of an ordinary review, I'll share a few highlights.
    These are quotes that I found especially interesting, with my comments.
    Long story short, I wish this book have existed when I started.
    Really recommended!
layout: post
---

I recently read [The Missing README: A Guide for the New Software Engineer](https://amzn.to/3Bk8kjP) by *Chris Riccomini* and *Dmitriy Ryaboy*.
_I'm something of a Junior myself_, so I decided to give it a try.
This book is packed with good advice for developers starting their career and thinking seriously about it.
Every chapter is full of exemplary behaviours and practices.
Authors have some great experience which they share with engineers.

This book is actually quite deep and I learned a bit from it as well.
Despite 15+ years in the industry.
If you are just beginning, it's definitely a book for you.
No matter which language or technology you chose.
The book is applicable to every platform.
Also, every sentence counts.
Even for a brief moment, it didn't feel bloated.

So instead of an ordinary review, I'll share a few highlights.
These are quotes that I found especially interesting, with my comments.
Long story short, I wish this book had existed when I started.
Highly recommended!

## Chapter 1: The Journey Ahead

> You create value by solving problems with code

Probably the best explanation of what software engineering really means.
Notice the order:

1. value
2. solving problems
3. code

> Make sure your manager adds you to team and company meetings

Sounds obvious.
But how many times I missed a meeting only because I was a new team member and calendar meetings didn't propagate?

> Remind your manager to schedule a one-on-one meeting if they conduct them

These days I'm a manager and I make sure to have a 1:1 meetings once every 2-3 months on average.
I have a simple spreadsheet with conditional formatting.
People who had their 1:1 longest time ago are marked red.
Simple and effective.

## Chapter 2: Getting to Conscious Competence

> Set the limit before you start your research to encourage discipline and prevent diminishing returns

It's easy to get very deep into the rabbit hole.
Set yourself a deadline for research or making proofs-of-concept.
Extend that timeframe only if you make significant progress.

## Chapter 3: Working with Code

> Breaking encapsulation increases the surface area of behaviour you have to guarantee across the lifetime of the project.

Java has sealed types and I also use [ArchUnit](https://www.archunit.org/) where it's not enough.
Also, design your modules and dependencies carefully.

> Use boring technology when possible. Don’t ignore convention, even if you disagree with it, and avoid forking code.

Yes!
I did a [presentation some time ago](https://www.youtube.com/watch?v=5TJiTSWktLU&t=924s) where I claim the best code is... boring.
It's not about testability, low-coupling, SOLID.
Make it boring.
So easy to read that you don't even think about it.

> Failure modes of boring technology are well understood

Everyone understands timeouts with rich stack traces in blocking Java code.
Timeout in a complex reactive application or actor system may lead to hours of painful investigation.
How good you are at troubleshooting new technologies?

## Chapter 4: Writing Operable Code

> Dmitriy was too lazy to handle inputs properly. Don’t be 20-year-old Dmitriy. He might have sabotaged a cure for cancer with this.

The "_cure for cancer_" is not a metaphor here.
This is a real case mentioned by one of the authors.
A poor UI in some medical software led to years of frustration and misunderstandings among staff.

> Backoff increases sleep time nonlinearly (usually using an exponential backoff, such as (retry number)^2). If you use this approach, make sure to cap the backoff at some maximum so it doesn’t get too large. However, if a network server has a blip and all clients experience that blip simultaneously, then back off using the same algorithm; they will all reissue their requests at the same time. This is called a thundering herd; many clients issuing retry requests simultaneously can bring a recovering service back down. To handle this, add jitter to the backoff strategy. With jitter, clients add a random, bounded amount of time to the backoff. Introducing randomness spreads out the requests, reducing the likelihood of a stampede.

This is an amazing phenomenon in distributed systems.
I talked about it in my podcast about [retrying failures](https://nurkiewicz.com/9).
This is a really valuable, practical piece of advice.

> Beware that changing log verbosity and configuration can eliminate race conditions and bugs because it slows down the application.

Changing log verbosity has other implications.
I once brought down the whole e-mail infrastructure in my company by increasing the log level on the Nexus server.
Nexus has nothing to do with e-mail.
It's an artifact repository.
But it happened to share server and disk with a mailer daemon.
Nexus filled up the whole disk and crashed e-mail for everyone.
Sorry...

> restarting a process to pick up a new configuration is usually operationally and architecturally superior.

I learned that lesson as well.
Spring has some sophisticated mechanisms for dynamic property reloading.
Beans are proxied and reloaded without restarting the whole app.
In general, I much rather restart the whole application than deal with inconsistencies, bugs, and unobvious behaviours during dynamic reload.
Restarting is fast, especially with GraalVM and modern frameworks like Quarkus or Micronaut.
Don't overengineer.

## Chapter 5: Managing Dependencies

> Adding a single dependency seems like a small change, but if that library depends on 100 others, your code now depends on 101 libraries

I'm yet to write a script that counts lines of code in typical, small microservices.
But!
Such a script would include the source from all JAR dependencies.
Suddenly your "_tiny 500-liner_" becomes the multi-million monster.

## Chapter 6: Testing

> see if you can restructure the test so that everything will execute deterministically. If not, that’s okay, but make an honest effort

This is about testing concurrent code that quickly becomes non-deterministic.
Chances are you can rewrite your code so that thread pools are injected.
Inside unit tests, you can inject fake thread pools with just one thread.
This changes the behaviour slightly.
But at least your test is deterministic.

## Chapter 8: Delivering Software

> the steps between git commit and live traffic should not be a mystery

Make sure you understand how it happens:

* How build scripts are run?
* How the application is packaged?
* How packages are deployed to production?
* How traffic is redirected to newly deployed packages?

> rapid release cycles produce more stable software that is easier to repair when bugs are found. Fewer changes go out per cycle, so each release carries less risk. When a bug makes it to production, there are fewer changes to look at when debugging. Code is fresh in developers’ minds, which makes the bug easier and faster to fix.

When recruiting or evaluating a company, the time between `git commit` and landing on production with live traffic is an important factor.

* "Hours" is healthy and very agile.
* "Weeks" implies a sad, slow corporate environment.

It's not always bad, some industries need weeks of manual testing and checks.
But being able to deploy to production in 15 minutes is a blessing.

> In a dark launch, an application proxy sits between the live traffic and the application. The proxy duplicates requests to the dark system. Responses to these identical requests from both systems are compared, and differences are recorded.

Also, this is a great architectural pattern if you are replacing an old component with a new one.
Make sure both produce the same responses, without affecting live traffic.
Typically it involves some large background job for comparing and looking for discrepancies.

## Chapter 9: Going On-Call

> Be patient and polite when responding to support tasks. While it might be your 10th interruption of the day, it’s the requestor’s first interaction with you.

This is the kind of advice that works in your private life as well.
Don't be rude to random people just because you had a bad day.

> Communicate in concise sentences. It can feel uncomfortable to be direct, but being direct doesn’t mean being rude.

True, people are much more likely to get your message if it's short and simple.
"_Billing system is down, investigating_" is so much better than:

"Due to unexpected circumstances, we are experiencing brief malfunctioning of one of our core billing components.
Our experienced team of engineers began triage and works around the clock to analyse the root cause of the issue you are facing at the moment"

> Each item that you work on while on-call should be in an issue tracker or the team’s on-call log

Very good advice.
Every unmonitored change to the production environment, every query, every insight or idea you try.
Help other people who may attempt to duplicate your work.
Also, it's a great material for future post mortem and runbooks.

> Mitigation isn’t about fixing the problem; it’s about reducing its severity. Fixing a problem can take a lot of time while mitigating it can usually be done quickly.

Actually, I never thought about it this way.
Indeed, immediate mitigation is much more important than finding the root cause and putting all safety measures in place.
It may sound unprofessional, but *maybe* start from a quick fix deployed straight to production.
Then move on to thorough automated testing.
Of course, this can lead production to an even greater outage where rushed mitigation of a small bug produces a much bigger one.
So proceed with care.

> DON’T leave a problem unmitigated while you search for the root cause.

First make sure people can use your system, whatever it takes.
Then think about long term strategies.

## Chapter 10: Technical Design Process

> "What happens if we don’t solve this problem?" is a powerful question. When the stakeholder answers, ask if the outcome is acceptable. You’ll find many problems don’t actually need to be solved.

So true.
Some bugs or missing features aren't worth fixing.
If it only impacts 0.001% of users on the cheapest pricing plan, or there is a workaround, maybe your time can be spent somewhere else?
Sometimes it's better to roll out to production with a bug than deploying perfect software, weeks after the deadline.
As a matter of fact, perfect software is a necessity quite rarely.

## Chapter 11: Creating Evolvable Architectures

> If your company still hand-rolls REST APIs and the JSON interfaces are evolved in code without a formal spec, your best bet is OpenAPI

The lack of schema or formal specification of RESTful APIs worries me.
There are approaches like OpenAPI or, from a completely different perspective, Consumer-Driven Contracts.
I am old enough to remember using SOAP.
Maybe that's why I'm looking with some hope at GraphQL.

> a schemaless approach has significant data integrity and complexity problems

Yes!
Claiming that MongoDB has no schema is wrong.
It has _implicit schema_, scattered through all applications running with different versions that use the database.
The schema is in your head, and every time you want to change the data model, you need to be very carefully.
Just like with schemaless APIs, I'd much rather have strict schema that's painful at first, but avoids lots of problems during maintenance phase.

> Don’t couple database and application lifecycles. Tying schema migrations to application deployment is dangerous. 

I sort of agree, althought it's really handy.
In small projects I used Flyway running migrations on startup and it was very simple.
But I do understand implications, like unexpectedly long migration that prevents application startup.
If you are doing blue/green or canary deployments, it's a smaller issue.
So you have to choose between the ease of deployment and reliability.

## Chapter 13: Working with Managers

> you set the agenda in a 1:1, and 1:1s are not for status updates

By "you" the authors mean ordinary developers, not their managers.
But it's a valuable piece of advice for both roles.
Treat 1:1 as an honest feedback session, time to discuss problems and plans.
No BS.

> Situation-Behavior-Impact (SBI) framework when providing feedback

I heard this many times.
When giving feedback, start from a real situation, not some general observation.

* Bad: "_you don't help teammates_".
* Good: "_remember that one time back in April when you didn't have time to troubleshoot Jane's production issue?_"

> A good way to understand your manager is to read the books they read

Good point!
I can tell the same thing about marketing.
If you want to be immune to cheap marketing tricks, learn these tricks!

## Chapter 14: Navigating Your Career

> Just because your teammate doesn’t know what a monad is doesn’t mean that they aren’t good at something else

[Impostor syndrome](https://en.wikipedia.org/wiki/Impostor_syndrome) in its entirety.
People have different skills and experiences.
You are great at functional programming.
Alice is not.
Bot she is exceptional at mitigating production issues of any sort.
Embrace that!

> A promotion isn’t a function of time: whether you are in your job for one year or five, impact is what matters

Do you remember the definition of a software developer?
"_You create value by solving problems with code_".
This is how you make an impact, by solving problems.
Too often I find myself coding to solve imaginary problems, creating no value.
Don't be like me...

I hope these quotes convinced you that it's a valuable book.
I enjoyed reading it throughout my vacation quite a lot.