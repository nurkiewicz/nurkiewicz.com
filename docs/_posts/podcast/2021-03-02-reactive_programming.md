---
category: podcast
title: "#35: Reactive programming: from spreadsheets to modern web frameworks"
permalink: /35
tags: reactive rxjs rxjava rxpy rxswift reactor excel elm
description: >
    To understand what reactive programming is, let's contrast it to _imperative_ programming.
    Imperative programs can be read top-to-bottom, with occasional jumps.
    Jumps are `if` statements, loops and procedure calls.
    Program is executed line by line.
    If you see `x = y + z`, the expression on the right is evaluated once.
    Then the symbol on the left is modified.
    If you change the value of `y` or `z` in the next line, obviously, it won't affect `x`.
    Compare it to a spreadsheet.
    Yes, an Excel file.
    It's obvious that changing any cell immediately propagates to all cells that depend on it, right?
    The process continues until all affected cells are updated.
    Essentially, every spreadsheet is internally represented by a dependency graph.
    We declare which pieces of data depend on which.
    The rest happens automatically.
    This approach to developing software is called... _reactive programming_.
---

{% include player.html episode_id="1kbgcxBKVQk2Dd7UttS4G2" %}

{{ page.description }}

Yes, good old spreadsheet is a very sophisticated reactive programming environment.
The change propagation is crucial here.
Rather than defining a sequence of operations, we declare data dependencies.
When any input changes, the output reflects that change almost instantaneously.
Contrast that to imperative program.
Inputs are evaluated only once.
So you either poll for changes manually or show stale data.

Do you think this problem is artificial?
Imagine the simplest front-end application.
It has two inputs, body weight and height.
And one output, your BMI (body mass index).
How do you update the BMI field?
The first approach is a "_Calculate_" button.
Update happens only when the user requests that.
This feels very unresponsive and outdated.

Another approach is to attach event listeners to weight and height, reacting to change.
This looks much better, but event listeners tend to get complex after a while.
Especially when there are many levels of dependencies.

But imagine if we could simply say: BMI field is always weight divided by height.
Period.
Some kind of framework takes care of the rest.
Weight changed?
The reactive backbone propagates that to BMI field.
BMI field changed because of that?
Let's update a diet suggestion.
Diet changed?
Let's display different ads.
All of these dependencies are declared, rather than programmed.

If you think this is impossible, check out Elm programming language.
It's a reactive runtime for web development.
Other frameworks are getting there as well.
For example, Angular uses RxJS.
A library that translates UI events into streams.
We can then transform and subscribe to such stream, compose multiple streams, etc.

RxJS is actually a member of a broader family of Reactive Extensions.
A family introduced in .NET, later ported to Java, Swift, Python and many more.
Rx libraries encourage modelling your system as a declarative stream of changes.
Incoming users, file system changes, key presses, CPU temperature reading.
All of these can be modelled as a stream.
A stream that you can transform, rather than a callback you need to manage.

Reactive programming is often associated with low-latency and high-throughput.
That's because it can help with writing efficient, yet manageable input/output code.
For example, accepting incoming connections, making RESTful calls, querying a database.
All of these are essentially network packets flowing in and out.
Which, in turn, can be easily modeled with abstract streams.

Another by-product of reactive programming is a mechanism called _backpressure_.
It's an algorithm that tries to slow down the producer is the consumer can't keep up.
Because eerything is a stream, backpressure effectively manages supply and demand on each level of your app.
It keeps your cores busy and prevents overflows.

That's it, thanks for listening, bye!

# More materials

* [Reactive programming](https://en.wikipedia.org/wiki/Reactive_programming) in Wikipedia


