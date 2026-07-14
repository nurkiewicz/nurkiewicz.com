---
layout: post
title: Parallelization of a simple use case explained
date: '2012-11-18T19:59:00.002+01:00'
author: Tomasz Nurkiewicz
tags:
- spring
- concurrency
modified_time: '2012-11-18T19:59:46.853+01:00'
thumbnail: /assets/img/parallelization-of-simple-use-case/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2585022734493247699
blogger_orig_url: https://www.nurkiewicz.com/2012/11/parallelization-of-simple-use-case.html
---

Some time ago a friend of mine asked me about the possibilities of speeding up the following process: they are generating some data in two stages, reading from a database and processing the results.
Reading takes approximately 70% of time and processing takes the remaining 30%.
Unfortunately they cannot simply load the whole data into memory, thus they split reading into much smaller chunks (pages) and process these pages once they are retrieved, interleaving the these two stages in a loop.
Here is a pseudo-code of what they have so far:

```java
public Data loadData(int page) {
    //70% of time...
}

public void process(Data data) {
    //30% of time...
}

for (int i = 0; i < MAX; ++i) {
    Data data = loadData(i);
    process(data);
}
```

His idea of improving the algorithm was to somehow start fetching next page of data when current page is still being processed, thus reducing the overall run time of the algorithm.
He was correct, but didn't know how to put this into Java code, not being very experienced with magnificent [`java.util.concurrent`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/package-summary.html) package.
This article is targeted for such people, introducing briefly the very basic concepts of concurrent programming in Java such as thread pools and [`Future<T>`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html) type.
First let's visualize the initial and desired implementation using [Gantt chart](http://en.wikipedia.org/wiki/Gantt_chart):

[![](/assets/img/parallelization-of-simple-use-case/1.png)](/assets/img/parallelization-of-simple-use-case/1.png)

The second chart represents the solution we are aiming to achieve.
The first observation you should make is that the second process finishes earlier, which is good.
The second one is: when we are processing first page (yellow `1`), the second page is already being downloaded (green `2`).
When we begin processing page `2`, page `3` began downloading.
And so on.
We will go back to this chart later, once we have a working implementation.
Let's put this into code.

Threads are the way to achieve background loading of data (green blocks).
However simply starting a thread for each green block is both slow and inconvenient.
Thread pool with just a single thread is much more flexible and easier to use.
First let's wrap our call to `loadData()` into `Callable<Data>`:

```java
private class LoadDataTask implements Callable<Data> {

    private final int page;

    private LoadDataTask(int page) {
        this.page = page;
    }

    @Override
    public Data call() throws Exception {
        return loadData(page);
    }
}
```

Once we have such class it's easy to feed thread pool (represented by [`ExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ExecutorService.html)) and wait for a reply.
Here is a full implementation:

```java
ExecutorService executorService = Executors.newSingleThreadExecutor();
Future<Data> next = executorService.submit(new LoadDataTask(0));
for (int i = 0; i < MAX; ++i) {
    Future<Data> current = next;
    if (i + 1 < MAX) {
        next = executorService.submit(new LoadDataTask(i + 1));
    }
    Data data = current.get();  //this can block
    process(data);
}
executorService.shutdownNow();
```

[`Executors.newSingleThreadExecutor()`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Executors.html#newSingleThreadExecutor()) basically creates a background thread waiting for tasks to run.
We cannot use a bigger pool (with more threads) because then we would risk keeping too much data in memory, before it gets processed.

For the purpose of example assume loading a page (green blocks) takes 700ms while processing it (yellow blocks) - 300ms.
At the beginning we submit an initial task to load page `0` (first blue arrow pointing down).
Thus we have to wait full 700ms for the first block.
However once the data is available, before we start processing it, we immediately ask for the next page.
When we run the second iteration, we don't have to wait full 700 ms again, because loading data already progressed by 300 ms, thus `Future.get()` only blocks for 400 ms. We repeat this process until we are processing the last page.
Of course we don't have load next page of data because we already processed all of them, thus this ugly condition inside loop.
It's easy to avoid it by returning null object from `loadData()` when page is out of bounds, but let's leave it for the clarity of example.

------------------------------------------------------------------------

This approach is so common in the enterprise that dedicated support was added to both [Spring](http://static.springsource.org/spring/docs/3.1.x/spring-framework-reference/html/scheduling.html#scheduling-annotation-support-async) and [EJB](http://docs.oracle.com/javaee/6/tutorial/doc/gkkqg.html).
Let's use Spring as an example.
The only thing we have to change is to adjust return value of `loadData()` from `Data` to `Future<Data>`.
Wrapping result value with [`AsyncResult`](http://static.springsource.org/spring/docs/3.1.x/javadoc-api/org/springframework/scheduling/annotation/AsyncResult.html) is required to compile:

```java
@Async
public Future<Data> loadData(int page) {
    //...
    return new AsyncResult<Data>(new Data(...));
}
```

Of course this class is a part of some Spring bean (say `dao`).
API is now much cleaner:

```java
Future<Data> next = dao.loadData(0);
for (int i = 0; i < MAX; ++i) {
    Future<Data> current = next;
    if (i + 1 < MAX) {
        next = dao.loadData(i + 1);
    }
    Data data = current.get();
    processor.process(data);
}
```

we no longer have to use `Callable` and interact with some thread pools.
Also bootstraping Spring was never that simple (so don't tell me that Spring is heavyweight!):

```java
@Configuration
@ComponentScan("com.blogspot.nurkiewicz.async")
@EnableAsync
public class Config implements AsyncConfigurer {

    @Override
    public Executor getAsyncExecutor() {
        return Executors.newSingleThreadExecutor();
    }

}
```

Technically `getAsyncExecutor()` is not required, but by default Spring will create a thread pool with 10 threads for `@Async` methods (and we want only one).
Now simply run this somewhere in your code.

```java
ApplicationContext context = 
  new AnnotationConfigApplicationContext(Config.class);
```

Lesson learnt from this article: don't be afraid of concurrency, it's much simpler than you think, providing that you are using built-in abstractions and understand them.
