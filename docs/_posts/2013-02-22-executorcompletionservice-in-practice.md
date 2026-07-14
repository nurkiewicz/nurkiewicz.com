---
layout: post
title: ExecutorCompletionService in practice
date: '2013-02-22T21:57:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- multithreading
- concurrency
modified_time: '2013-02-22T21:58:59.656+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5923311808164322969
blogger_orig_url: https://www.nurkiewicz.com/2013/02/executorcompletionservice-in-practice.html
image:
  path: /assets/img/executorcompletionservice-in-practice/hero.jpg
  alt: "Holmenkollen district"
---

Everyone is talking about the future of Java, we continue our journey explaining `Future<T>` interface in Java.
[`ExecutorCompletionService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ExecutorCompletionService.html) wrapper class tries to address one of the biggest deficiencies of `Future<T>` type - no support for callbacks or any event-driven behaviour whatsoever.
Let's go back for a moment to our [sample asynchronous task](http://nurkiewicz.blogspot.no/2013/02/javautilconcurrentfuture-basics.html) downloading contents of a given URL:

```java
final ExecutorService pool = Executors.newFixedThreadPool(10);
pool.submit(new Callable<String>() {
    @Override
    public String call() throws Exception {
        try (InputStream input = url.openStream()) {
            return IOUtils.toString(input, StandardCharsets.UTF_8);
        }
    }
});
```

Having such code we can easily write a simple web search engine/crawler, examining several URLs concurrently:

```java
final List<String> topSites = Arrays.asList(
        "www.google.com", "www.youtube.com", "www.yahoo.com", "www.msn.com",
        "www.wikipedia.org", "www.baidu.com", "www.microsoft.com", "www.qq.com",
        "www.bing.com", "www.ask.com", "www.adobe.com", "www.taobao.com",
        "www.youku.com", "www.soso.com", "www.wordpress.com", "www.sohu.com",
        "www.windows.com", "www.163.com", "www.tudou.com", "www.amazon.com"
);

final ExecutorService pool = Executors.newFixedThreadPool(5);
List<Future<String>> contentsFutures = new ArrayList<>(topSites.size());
for (final String site : topSites) {
    final Future<String> contentFuture = pool.submit(new Callable<String>() {
        @Override
        public String call() throws Exception {
            return IOUtils.toString(new URL("http://" + site), StandardCharsets.UTF_8);
        }
    });
    contentsFutures.add(contentFuture);
}
```

As easy as that.
We simply submit separate task for each web site to a pool and wait for results.
To achieve that we collect all `Future<String>` objects into a collection and iterate through them:

```java
for (Future<String> contentFuture : contentsFutures) {
    final String content = contentFuture.get();
    //...process contents
}
```

Each call to `contentFuture.get()` waits until downloading given web site (remember that each `Future` represent one site) is finished.
This works, but has a major bottleneck.
Imagine you have as many threads in a pool as tasks (20 sites in that case).
I think it's understandable that you want to start processing contents of web sites as soon as they arrive, no matter which one is first.
Response times vary greatly so don't be surprised to find some web sites responding within a second while others need even 20 seconds.
But here's the problem: after submitting all the tasks we block on an arbitrary `Future<T>`.
There is no guarantee that this `Future` will complete first.
It is very likely that other `Future` objects already completed and are ready for processing but we keep hanging on that arbitrary, first `Future`.
In worst case scenario, if the first submitted page is slower by an order of magnitude compared to all the others, all the results except the first one are ready for processing and idle, while we keep waiting for the first one.

The obvious solution would be to sort web sites from fastest to slowest and submit them in that order.
Then we would be guaranteed that `Future`s complete in the order in which we submitted them.
But this is impractical and almost impossible in real life due to dynamic nature of web.

This is where `ExecutorCompletionService` steps in.
It is a thin wrapper around [`ExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ExecutorService.html) that "remembers" all submitted tasks and allows you to wait for the first *completed*, as opposed to first *submitted* task.
In a way `ExecutorCompletionService` keeps a handle to all intermediate `Future` objects and once any of them finishes, it's returned.
Crucial API method is [`CompletionService.take()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/CompletionService.html#take()) that blocks and waits for *any* underlying `Future` to complete.
Here is the submit step with `ExecutorCompletionService`:

```java
final ExecutorService pool = Executors.newFixedThreadPool(5);
final ExecutorCompletionService<String> completionService = new ExecutorCompletionService<>(pool);
for (final String site : topSites) {
    completionService.submit(new Callable<String>() {
        @Override
        public String call() throws Exception {
            return IOUtils.toString(new URL("http://" + site), StandardCharsets.UTF_8);
        }
    });
}
```

Notice how we seamlessly switched to `completionService`.
Now the retrieval step:

```java
for(int i = 0; i < topSites.size(); ++i) {
    final Future<String> future = completionService.take();
    try {
        final String content = future.get();
        //...process contents
    } catch (ExecutionException e) {
        log.warn("Error while downloading", e.getCause());
    }
}
```

You might be wondering why we need an extra counter?
Unfortunately `ExecutorCompletionService` doesn't tell you how many `Future` objects are still there waiting so you must remember how many times to call `take()`.

This solution feels much more robust.
We process responses immediately when they are ready.
`take()` blocks until fastest task still running finishes.
And if processing takes a little bit longer and multiple responses finished, subsequent call to `take()` will return immediately.
It's fun to observe the program when number of pool threads is as big as the number of tasks so that we begin downloading each site at the same time.
You can easily see which websites have shortest response time and which respond very slowly.

------------------------------------------------------------------------

`ExecutorCompletionService` seems wonderful, but in fact it is quite limited.
You cannot use it with arbitrary collection of `Future` objects which you happened to obtain somehow.
It works only with `Executor` abstraction.
Also there is no built in support for processing incoming results concurrently as well.
If we want to parse results concurrently, we need to manually submit them to a second thread pool.
In the next few articles I will show you more powerful constructs that mitigate these disadvantages.
