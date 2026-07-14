---
layout: post
title: javax.servlet.AsyncContext.start() limited usefulness
date: '2012-05-12T22:02:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- servlets
- scala
- performance
- monitoring
modified_time: '2012-07-08T12:14:49.867+02:00'
thumbnail: /assets/img/javaxservletservletrequeststartasync/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-158156416560864365
blogger_orig_url: https://www.nurkiewicz.com/2012/05/javaxservletservletrequeststartasync.html
---

Some time ago I came across [*What's the purpose of AsyncContext.start(...)
in Servlet 3.0?*](http://stackoverflow.com/questions/10073392)
question.
Quoting the [Javadoc of aforementioned method](http://docs.oracle.com/javaee/6/api/javax/servlet/AsyncContext.html#start(java.lang.Runnable)):

*Causes the container to dispatch a thread, possibly from a managed thread pool, to run the specified `Runnable`.*

To remind all of you, `AsyncContext` is a standard way defined in Servlet 3.0 specification to handle HTTP requests asynchronously.
Basically HTTP request is no longer tied to an HTTP thread, allowing us to handle it later, possibly using fewer threads.
It turned out that the specification provides an API to handle asynchronous threads in a different thread pool out of the box.
First we will see how this feature is completely broken and useless in Tomcat and Jetty - and then we will discuss why the usefulness of it is questionable in general.

Our test servlet will simply sleep for given amount of time.
This is a scalability killer in normal circumstances because even though sleeping servlet is not consuming CPU, but sleeping HTTP thread tied to that particular request consumes memory - and no other incoming request can use that thread.
In our test setup I limited the number of HTTP worker threads to 10 which means only 10 concurrent requests are completely blocking the application (it is unresponsive from the outside) even though the application itself is almost completely idle.
So clearly sleeping is an enemy of scalability.

```scala
@WebServlet(urlPatterns = Array("/*"))
class SlowServlet extends HttpServlet with Logging {

  protected override def doGet(req: HttpServletRequest, resp: HttpServletResponse) {
    logger.info("Request received")
    val sleepParam = Option(req.getParameter("sleep")) map {_.toLong}
    TimeUnit.MILLISECONDS.sleep(sleepParam getOrElse 10)
    logger.info("Request done")
  }
}
```

Benchmarking this code reveals that the average response times are close to `sleep` parameter as long as the number of concurrent connections is below the number of HTTP threads.
Unsurprisingly the response times begin to grow the moment we exceed the HTTP threads count.
Eleventh connection has to wait for any other request to finish and release worker thread.
When the concurrency level exceeds 100, Tomcat begins to drop connections - too many clients are already queued.

So what about the the fancy `AsyncContext.start()` method (do not confuse with [`ServletRequest.startAsync()`](http://docs.oracle.com/javaee/6/api/javax/servlet/ServletRequest.html#startAsync()))?
According to the JavaDoc I can submit any `Runnable` and the container will use some managed thread pool to handle it.
This will help partially as I no longer block HTTP worker threads (but still another thread somewhere in the servlet container is used).
Quickly switching to asynchronous servlet:

```scala
@WebServlet(urlPatterns = Array("/*"), asyncSupported = true)
class SlowServlet extends HttpServlet with Logging {

  protected override def doGet(req: HttpServletRequest, resp: HttpServletResponse) {
    logger.info("Request received")
    val asyncContext = req.startAsync()
    asyncContext.setTimeout(TimeUnit.MINUTES.toMillis(10))
    asyncContext.start(new Runnable() {
      def run() {
        logger.info("Handling request")
        val sleepParam = Option(req.getParameter("sleep")) map {_.toLong}
        TimeUnit.MILLISECONDS.sleep(sleepParam getOrElse 10)
        logger.info("Request done")
        asyncContext.complete()
      }
    })
  }
}
```

We are first enabling the asynchronous processing and then simply moving `sleep()` into a `Runnable` and hopefully a different thread pool, releasing the HTTP thread pool.
Quick stress test reveals slightly unexpected results (here: response times vs. number of concurrent connections):

[![](/assets/img/javaxservletservletrequeststartasync/1.png)](/assets/img/javaxservletservletrequeststartasync/1.png)

Guess what, the response times are *exactly* the same as with no asynchronous support at all (!)
After closer examination I discovered that when `AsyncContext.start()` is called Tomcat submits given task back to...
HTTP worker thread pool, the same one that is used for all HTTP requests!
This basically means that we have released one HTTP thread just to utilize another one milliseconds later (maybe even the same one).
There is absolutely no benefit of calling `AsyncContext.start()` *in Tomcat*.
I have no idea whether this is a bug or a feature.
On one hand this is clearly not what the API designers intended.
The servlet container was suppose to manage separate, independent thread pool so that HTTP worker thread pool is still usable.
I mean, the whole point of asynchronous processing is to escape the HTTP pool.
Tomcat pretends to delegate our work to another thread, while it still uses the original worker thread pool.

So why I consider this to be a feature?
Because Jetty is "broken" in exactly same way...
No matter whether this works as designed or is only a poor API implementation, using `AsyncContext.start()` in Tomcat and Jetty is pointless and only unnecessarily complicates the code.
It won't give you anything, the application works exactly the same under high load as if there was no asynchronous logic at all.

But what about using this API feature on *correct* implementations like [IBM WAS](http://jlaskowski.blogspot.com/2012/05/watki-podczas-obsugi-asynchronicznego.html)?
It is better, but still the API as is doesn't give us much in terms of scalability.
To explain again: the whole point of asynchronous processing is the ability to decouple HTTP request from an underlying thread, preferably by handling several connections using the same thread.

`AsyncContext.start()` will run the provided `Runnable` in a separate thread pool.
Your application is still responsive and can handle ordinary requests while long-running request that you decided to handle asynchronously are processed in a separate thread pool.
It is better, unfortunately the thread pool and *thread per connection* idiom is still a bottle-neck.
For the JVM it doesn't matter what type of threads are started - they still occupy memory.
So we are no longer blocking HTTP worker threads, but our application is not more scalable in terms of concurrent long-running tasks we can support.

In this simple and unrealistic example with sleeping servlet we can actually support thousand of concurrent (waiting) connections using Servlet 3.0 asynchronous support with only one extra thread - and without `AsyncContext.start()`.
Do you know how?
Hint: [`ScheduledExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ScheduledExecutorService.html).

#### Postscriptum: Scala goodness

I almost forgot.
Even though examples were written in Scala, I haven't used any cool language features yet.
Here is one: implicit conversions.
Make this available in your scope:

```scala
implicit def blockToRunnable[T](block: => T) = new Runnable {
 def run() {
  block
 }
}
```

And suddenly you can use code block instead of instantiating `Runnable` manually and explicitly:

```scala
asyncContext start {
 logger.info("Handling request")
 val sleepParam = Option(req.getParameter("sleep")) map { _.toLong}
 TimeUnit.MILLISECONDS.sleep(sleepParam getOrElse 10)
 logger.info("Request done")
 asyncContext.complete()
}
```

Sweet!
