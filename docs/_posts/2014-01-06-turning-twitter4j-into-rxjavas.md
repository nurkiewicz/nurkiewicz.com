---
layout: post
title: Turning Twitter4J into RxJava's Observable
date: '2014-01-06T16:28:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- twitter4j
- rxjava
modified_time: '2014-01-06T16:33:57.909+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-500314652963032083
blogger_orig_url: https://www.nurkiewicz.com/2014/01/turning-twitter4j-into-rxjavas.html
image:
  path: /assets/img/turning-twitter4j-into-rxjavas/hero.jpg
  alt: "North of Oslo"
---

a[Twitter4J](http://twitter4j.org/en/index.html) is a Java wrapper around [Twitter API](https://dev.twitter.com/).
While Twitter supports simple request-response interactions in this article we will explore [streaming APIs](https://dev.twitter.com/docs/streaming-apis).
In contrary to request-response model which is always initiated by the client, streaming API pushes data from Twitter server to the clients as soon as they are available.
Of course in case of Twitter we are talking about tweets, called [`Status`](http://twitter4j.org/javadoc/twitter4j/Status.html) in the API.

The question is, how would you design a Java API for streaming purposes?
No surprise here: *callbacks, callbacks everywhere*!

```java
import twitter4j.*;

TwitterStream twitter = new TwitterStreamFactory().getInstance();
twitter.addListener(new StatusAdapter() {
  public void onStatus(Status status) {
    System.out.println(status.getUser().getName() + " : " + status.getText());
  }
});
twitter.sample();
```

Say that on top of this API we would like to count how many messages we receive per second.
A lot of accidental complexity sneaks in:

```java
final AtomicInteger countPerSecond = new AtomicInteger();

twitter.addListener(new StatusAdapter() {
  public void onStatus(Status status) {
    countPerSecond.incrementAndGet();
  }
});
twitter.sample();

Executors.newScheduledThreadPool(1).scheduleAtFixedRate(new Runnable() {
  @Override
  public void run() {
    final int count = countPerSecond.getAndSet(0);
    log.debug("Tweets/second: {}", count);
  }
}, 1, 1, SECONDS);
```

We need a [`ScheduledExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ScheduledExecutorService.html) and be very careful about thread safety.
Moreover this approach doesn't scale as it requires hand-crafted code for every use case we can imagine, like throttling, combining or accumulating.
It turns out that bridging Twitter4J streaming API (and virtually any callback-based API for that matter) to [RxJava](https://github.com/Netflix/RxJava)'s [`Observable`](https://github.com/Netflix/RxJava/wiki/Observable) is quite straightforward and will greatly simplify further solutions.

Before we explore how to create new `Observable` representing stream of Twitter messages on top of Twitter4J API let's assume that we already have one:

```java
Observable<Status> twitter = twitterObservable();  //to be implemented
```

`Observable<Status> twitter` is a stream of `Status` objects where each such object is one tweet.
How do we solve our initial problem of counting tweets per second (*tps*)?

```java
Observable<Integer> tpsStream = twitter.
    buffer(1, TimeUnit.SECONDS).
    map(list -> list.size());
```

That was easy!
We take initial stream of tweets and buffer them every second.
When one second elapses only a single event is triggered containing a `List<Status>` produced within that time frame.
Later on we transform `List` into `Integer` by taking its `size()`.
And that's it!
`tpsStream` will yield one number per second representing count of tweets per second.
If we suddenly realized that our system is overloaded by that number, we can easily sample the stream and pick just a subset of them.
E.g. we want to get at most one tweet every 100 milliseconds:

```java
twitter.sample(100, MILLISECONDS)
```

There are more than [hundred operators](https://github.com/Netflix/RxJava/wiki/Alphabetical-List-of-Observable-Operators) available similar to `buffer()` and `sample()` but I hope you get the idea.
Now that we see how useful an `Observable<Status>` is, let's implement it.
When defining `Observable` we need to supply two handlers: one describing what happens when client subscribes to a given `Observable` and optionally - how to handle unsubscribing:

```java
public Observable<Status> twitterObservable() {
  return Observable.create(subscriber -> {
    final TwitterStream twitterStream = new TwitterStreamFactory().getInstance();
    twitterStream.addListener(new StatusAdapter() {
      public void onStatus(Status status) {
        subscriber.onNext(status);
      }
      public void onException(Exception ex) {
        subscriber.onError(ex);
      }
    });
    twitterStream.sample();
    return Subscriptions.create(() -> {
      twitterStream.cleanUp();
    });
  });
}
```

Quite a bit of code written in Java 8 (Scala and Groovy work equally well with RxJava).
Callback provided to `Observable.create()` is executed every time someone subscribes to `Observable`.
It turns out that all examples below never trigger this handler because RxJava is very lazy in nature, thus it won't connect to Twitter unless absolutely required.
For example `twitter.filter(...)`
will return a new `Observable` with only a subset of tweets matching certain criteria.
But as long as you don't physically subscribe (using `twitter.subscribe()`) to that `Observable`, nothing will really happen.
In example below the connection is postponed until we call `subscribe()`.
After that text of each encountered tweet is extracted and if it contains `#java` hashtag - it will be printed.
All of this happens asynchronously and the whole statement is non-blocking:

```java
twitter.
  map(Status::getText).
  filter(text -> text.contains("#java")).
  subscribe(System.out::println);
```

The `Subscriptions.create()` also takes a handler - and as you can guess it tells what should happen when client is no longer interested in `Observable<Status>`.

Twitter4J is just an example how you can adapt callback-based API into an `Observable`.
Other examples include incoming network packages, JMS messages or file system changes.
In all cases the scenario is the same.
