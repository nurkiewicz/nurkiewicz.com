---
layout: post
title: Advanced ListenableFuture capabilities
date: '2013-02-28T23:34:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- guava
- multithreading
- concurrency
modified_time: '2013-02-28T23:34:59.408+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6548377248676725214
blogger_orig_url: https://www.nurkiewicz.com/2013/02/advanced-listenablefuture-capabilities.html
image:
  path: /assets/img/advanced-listenablefuture-capabilities/hero.jpg
  alt: "Holmenkollen district"
---

Last time we [familiarized ourselves with `ListenableFuture`](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html).
I promised to introduced more advanced techniques, namely transformations and chaining.
Let's start from something straightforward.
Say we have our `ListenableFuture<String>` which we got from some asynchronous service.
We also have a simple method:

```java
Document parse(String xml) {//...
```

We don't need `String`, we need `Document`.
One way would be to simply resolve `Future` (*wait* for it) and do the processing on `String`.
But much more elegant solution is to apply transformation once the results are available and treat our method as if was always returning `ListenableFuture<Document>`.
This is pretty straightforward:

```java
final ListenableFuture<String> future = //...

final ListenableFuture<Document> documentFuture = Futures.transform(future, new Function<String, Document>() {
    @Override
    public Document apply(String contents) {
        return parse(contents);
    }
});
```

or more readable:

```java
final Function<String, Document> parseFun = new Function<String, Document>() {
    @Override
    public Document apply(String contents) {
        return parse(contents);
    }
};

final ListenableFuture<String> future = //...

final ListenableFuture<Document> documentFuture = Futures.transform(future, parseFun);
```

Java syntax is a bit limiting, but please focus on what we just did.
`Futures.transform()` doesn't wait for underlying `ListenableFuture<String>` to apply `parse()` transformation.
Instead, under the hood, it registers a callback, wishing to be notified whenever given future finishes.
This transformation is applied dynamically and transparently for us at right moment.
We still have `Future`, but this time wrapping `Document`.

So let's go one step further.
We also have an asynchronous, possibly long-running method that calculates *relevance* (whatever that is in this context) of a given `Document`:

```java
ListenableFuture<Double> calculateRelevance(Document pageContents) {//...
```

Can we somehow chain it with `ListenableFuture<Document>` we already have?
First attempt:

```java
final Function<Document, ListenableFuture<Double>> relevanceFun = new Function<Document, ListenableFuture<Double>>() {
    @Override
    public ListenableFuture<Double> apply(Document input) {
        return calculateRelevance(input);
    }
};

final ListenableFuture<String> future = //...
final ListenableFuture<Document> documentFuture = Futures.transform(future, parseFun);
final ListenableFuture<ListenableFuture<Double>> relevanceFuture = Futures.transform(documentFuture, relevanceFun);
```

Ouch!
*Future of future of `Double`*, that doesn't look good.
Once we resolve outer future we need to wait for inner one as well.
Definitely not elegant.
Can we do better?

```java
final AsyncFunction<Document, Double> relevanceAsyncFun = new AsyncFunction<Document, Double>() {
    @Override
    public ListenableFuture<Double> apply(Document pageContents) throws Exception {
        return calculateRelevance(pageContents);
    }
};

final ListenableFuture<String> future = //comes from ListeningExecutorService
final ListenableFuture<Document> documentFuture = Futures.transform(future, parseFun);
final ListenableFuture<Double> relevanceFuture = Futures.transform(documentFuture, relevanceAsyncFun);
```

Please look very carefully at all types and results.
Notice the difference between `Function` and `AsyncFunction`.
Initially we got an asynchronous method returning future of `String`.
Later on we transformed it to seamlessly turn `String` into XML `Document`.
This transformation happens asynchronously, when inner future completes.
Having future of `Document` we would like to call a method that requires `Document` and returns future of `Double`.

If we call `relevanceFuture.get()`, our `Future` object will first wait for inner task to complete and having its result (`String` -\> `Document`) will wait for outer task and return `Double`.
We can also register callbacks on `relevanceFuture` which will fire when outer task (`calculateRelevance()`) finishes.
If you are still here, the are even more crazy transformations.

Remember that all this happens in a loop.
For each web site we got `ListenableFuture<String>` which we asynchronously transformed to `ListenableFuture<Double>`.
So in the end we work with a `List<ListenableFuture<Double>>`.
This also means that in order to extract all the results we either have to register listener for each and every `ListenableFuture` or wait for each of them.
Which doesn't progress us at all.
But what if we could easily transform from `List<ListenableFuture<Double>>` to `ListenableFuture<List<Double>>`?
Read carefully - from list of futures to future of list.
In other words, rather than having a bunch of small futures we have one future that will complete when all child futures complete - and the results are mapped one-to-one to target list.
Guess what, Guava can do this!

```java
final List<ListenableFuture<Double>> relevanceFutures = //...;
final ListenableFuture<List<Double>> futureOfRelevance = Futures.allAsList(relevanceFutures);
```

Of course there is no waiting here as well.
Wrapper `ListenableFuture<List<Double>>` will be notified every time one of its *child* futures complete.
The moment the last child `ListenableFuture<Double>` completes, outer future completes as well.
Everything is event-driven and completely hidden from you.

Do you think that's it?
Say we would like to compute the biggest relevance in the whole set.
As you probably know by now, we won't wait for a `List<Double>`.
Instead we will register transformation from `List<Double>` to `Double`!

```java
final ListenableFuture<Double> maxRelevanceFuture = Futures.transform(futureOfRelevance, new Function<List<Double>, Double>() {
    @Override
    public Double apply(List<Double> relevanceList) {
        return Collections.max(relevanceList);
    }
});
```

Finally, we can listen for completion event of `maxRelevanceFuture` and e.g. send results (asynchronously!)
using JMS.
Here is a complete code if you lost track:

```java
private Document parse(String xml) {
    return //...
}

private final Function<String, Document> parseFun = new Function<String, Document>() {
    @Override
    public Document apply(String contents) {
        return parse(contents);
    }
};

private ListenableFuture<Double> calculateRelevance(Document pageContents) {
    return //...
}

final AsyncFunction<Document, Double> relevanceAsyncFun = new AsyncFunction<Document, Double>() {
    @Override
    public ListenableFuture<Double> apply(Document pageContents) throws Exception {
        return calculateRelevance(pageContents);
    }
};

//...

final ListeningExecutorService pool = MoreExecutors.listeningDecorator(
    Executors.newFixedThreadPool(10)
);

final List<ListenableFuture<Double>> relevanceFutures = new ArrayList<>(topSites.size());
for (final URL siteUrl : topSites) {
    final ListenableFuture<String> future = pool.submit(new Callable<String>() {
        @Override
        public String call() throws Exception {
            return IOUtils.toString(siteUrl, StandardCharsets.UTF_8);
        }
    });
    final ListenableFuture<Document> documentFuture = Futures.transform(future, parseFun);
    final ListenableFuture<Double> relevanceFuture = Futures.transform(documentFuture, relevanceAsyncFun);
    relevanceFutures.add(relevanceFuture);
}

final ListenableFuture<List<Double>> futureOfRelevance = Futures.allAsList(relevanceFutures);
final ListenableFuture<Double> maxRelevanceFuture = Futures.transform(futureOfRelevance, new Function<List<Double>, Double>() {
    @Override
    public Double apply(List<Double> relevanceList) {
        return Collections.max(relevanceList);
    }
});

Futures.addCallback(maxRelevanceFuture, new FutureCallback<Double>() {
    @Override
    public void onSuccess(Double result) {
        log.debug("Result: {}", result);
    }

    @Override
    public void onFailure(Throwable t) {
        log.error("Error :-(", t);
    }
});
```

Was it worth it?
*Yes* and *no*.
*Yes*, because we learned some really important constructs and primitives used together with futures/promises: chaining, mapping (transforming) and reducing.
The solution is beautiful in terms of CPU utilization - no waiting, blocking, etc. Remember that the biggest strength of [Node.js](http://nodejs.org/) is its "no-blocking" policy.
Also in [Netty](http://netty.io/) futures are ubiquitous.
Last but not least, it feels very *functional*.

On the other hand, mainly due to Java syntax verbosity and lack of type inference (yes, we will jump into Scala soon) code seems very unreadable, hard to follow and maintain.
Well, to some degree this holds true for all message driven systems.
But as long as we don't invent better APIs and primitives, we must learn to live and take advantage of asynchronous, highly parallel computations.

If you want to experiment with `ListenableFuture` even more, don't forget to read [official documentation](http://code.google.com/p/guava-libraries/wiki/ListenableFutureExplained).
