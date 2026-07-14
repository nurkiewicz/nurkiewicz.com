---
layout: post
title: DeferredResult - asynchronous processing in Spring MVC
date: '2013-03-04T18:04:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- spring mvc
- multithreading
- spring
- concurrency
modified_time: '2013-03-04T18:06:04.755+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5027131012667709069
blogger_orig_url: https://www.nurkiewicz.com/2013/03/deferredresult-asynchronous-processing.html
image:
  path: /assets/img/deferredresult-asynchronous-processing/hero.jpg
  alt: "Bygdøy"
---

[`DeferredResult`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/web/context/request/async/DeferredResult.html) is a container for possibly not-yet-finished computation that will be available in future.
Spring MVC uses it to represent asynchronous computation and take advantage of Servlet 3.0 [`AsyncContext`](http://docs.oracle.com/javaee/6/api/javax/servlet/AsyncContext.html) asynchronous request handling.
Just to give a quick impression how it works:

```java
@RequestMapping("/")
@ResponseBody
public DeferredResult<String> square() throws JMSException {
    final DeferredResult<String> deferredResult = new DeferredResult<>();
    runInOtherThread(deferredResult);
    return deferredResult;
}

private void runInOtherThread(DeferredResult<String> deferredResult) {
    //seconds later in other thread...
    deferredResult.setResult("HTTP response is: 42");
}
```

Normally once you leave controller handler method request processing is done.
But not with `DeferredResult`.
Spring MVC (using Servlet 3.0 capabilities) will hold on with the response, keeping idle HTTP connection.
HTTP worker thread is no longer used, but HTTP connection is still open.
Later some other thread will resolve `DeferredResult` by assigning some value to it.
Spring MVC will immediately pick up this event and send response (*"HTTP response is: 42"* in this example) to the browser, finishing request processing.

You might see some conceptual similarity between `Future<V>` and `DeferredResult` - they both represent computation with result available some time in the future.
You might wonder, why Spring MVC doesn't allow us to simply return `Future<V>` but instead introduced new, proprietary abstraction?
The reason is simply and once again shows `Future<V>` deficiencies.
The whole point of asynchronous processing is avoid blocking threads.
Standard `java.util.concurrent.Future` does not allow registering callbacks when computation is done - so you either need to devote one thread to block until future is done or use one thread to poll several futures periodically.
However the latter option consumes more CPU and introduces latency.
But [superior `ListenableFuture<V>`](http://nurkiewicz.blogspot.no/2013/02/listenablefuture-in-guava.html) from [Guava](http://code.google.com/p/guava-libraries/) seems like a good fit?
True, but Spring doesn't have a dependency on Guava, thankfully bridging these two APIs is pretty straightforward.

------------------------------------------------------------------------

But first have a look at previous part on [implementing custom `java.util.concurrent.Future<V>`](http://nurkiewicz.blogspot.no/2013/02/implementing-custom-future.html).
Admittedly it wasn't as simple as one might expect.
Clean up, handling interruptions, locking and synchronization, maintaining state.
A lot of boilerplate when everything we need is as simple as receiving a message and returning it from `get()`.
Let us try to retrofit previous implementation of `JmsReplyFuture` to also implement more powerful `ListenableFuture` - so we can use it later in Spring MVC.

`ListenableFuture` simply extends *standard* `Future` adding possibility to register callbacks (listeners).
So an eager developer would simply sit down and add list of `Runnable` listeners to existing implementation:

```java
public class JmsReplyFuture<T extends Serializable> implements ListenableFuture<T>, MessageListener {

    private final List<Runnable> listeners = new ArrayList<Runnable>();

    @Override
    public void addListener(Runnable listener, Executor executor) {
        listeners.add(listener);
    }

    //...
```

But it's greatly oversimplified.
Of course we must iterate over all listeners when future is done or exception occurs.
If the future is already resolved when we add a listener, we must call that listener immediately.
Moreover we ignore `executor` - according to API each listener may use a different thread pool supplied to `addListener()` so we must store pairs: `Runnable` + `Executor`.
Last but not least `addListener()` is not thread safe.
Eager developer would fix all this in a matter of an hour or two.
And spend two more hours to fix bugs introduced in the meantime.
And few more hours weeks later when another "impossible" bug pops-up on production.
I am not eager.
As a matter of fact, I am too lazy to write even the simplest implementation above.
But I am desperate enough to hit `Ctrl` + `H` (*Subtypes* view in IntelliJ IDEA) on `ListenableFuture` and scan through available skeletal implementations tree.
[`AbstractFuture<V>`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/util/concurrent/AbstractFuture.html) - Bingo!

```java
public class JmsReplyListenableFuture<T extends Serializable> extends AbstractFuture<T> implements MessageListener {

    private final Connection connection;
    private final Session session;
    private final MessageConsumer replyConsumer;

    public JmsReplyListenableFuture(Connection connection, Session session, Queue replyQueue) throws JMSException {
        this.connection = connection;
        this.session = session;
        this.replyConsumer = session.createConsumer(replyQueue);
        this.replyConsumer.setMessageListener(this);
    }

    @Override
    public void onMessage(Message message) {
        try {
            final ObjectMessage objectMessage = (ObjectMessage) message;
            final Serializable object = objectMessage.getObject();
            set((T) object);
            cleanUp();
        } catch (Exception e) {
            setException(e);
        }
    }

    @Override
    protected void interruptTask() {
        cleanUp();
    }

    private void cleanUp() {
        try {
            replyConsumer.close();
            session.close();
            connection.close();
        } catch (Exception e) {
            Throwables.propagate(e);
        }
    }
}
```

That's it, everything, compile and run.
Almost 2x less code compared to [initial implementation](http://nurkiewicz.blogspot.no/2013/02/implementing-custom-future.html) and we get much more powerful `ListenableFuture`.
Most of the code is set up and clean up.
`AbstractFuture` already implements `addListener()`, locking and state handling for us.
All we have to do is call `set()` method when future is resolved (JMS reply arrives in our case).
Moreover we finally support exceptions properly.
Previously we simply ignored/rethrown them while now they are correctly wrapped and thrown from `get()` when accessed.
Even if we weren't interested in `ListenableFuture` capabilities, `AbstractFuture` still helps us a lot.
And we get `ListenableFuture` for free.

Good programmers love writing code.
Better ones [love *deleting* it](http://devopsreactions.tumblr.com/post/44360857123).
Less to maintain, less to test, less to break.
I am sometimes amazed how helpful Guava can be.
Last time I was working with iterator-heavy piece of code.
Data was generated dynamically and iterators could easily produce millions of items so I had no choice.
Limited iterator API together with quite complex business logic is a recipe for endless amount of plumbing code.
And then I found [`Iterators` utility class](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Iterators.html) and it saved my life.
I suggest you to open [JavaDoc of Guava](http://docs.guava-libraries.googlecode.com/git/javadoc/index.html) and go through all packages, class by class.
You'll thank me later.

------------------------------------------------------------------------

Once we have our custom `ListenableFuture` in place (obviously you can use any implementation) we can try integrating it with Spring MVC.
Here is what we want to achieve:

1.  HTTP request comes in
2.  We send a request to JMS queue
3.  HTTP worker thread is no longer used, it can serve other requests
4.  JMS listener asynchronously waits for a reply in temporary queue
5.  Once the reply arrives we push it immediately as an HTTP response and the connection is done.

First naive implementation using blocking `Future`:

```java
@Controller
public class JmsController {

    private final ConnectionFactory connectionFactory;

    public JmsController(ConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    @RequestMapping("/square/{value}")
    @ResponseBody
    public String square(@PathVariable double value) throws JMSException, ExecutionException, InterruptedException {
        final ListenableFuture<Double> responseFuture = request(value);
        return responseFuture.get().toString();
    }

    //JMS API boilerplate
    private <T extends Serializable> ListenableFuture<T> request(Serializable request) throws JMSException {
        Connection connection = this.connectionFactory.createConnection();
        connection.start();
        final Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
        final Queue tempReplyQueue = session.createTemporaryQueue();
        final ObjectMessage requestMsg = session.createObjectMessage(request);
        requestMsg.setJMSReplyTo(tempReplyQueue);
        sendRequest(session.createQueue("square"), session, requestMsg);
        return new JmsReplyListenableFuture<T>(connection, session, tempReplyQueue);
    }

    private void sendRequest(Queue queue, Session session, ObjectMessage requestMsg) throws JMSException {
        final MessageProducer producer = session.createProducer(queue);
        producer.setDeliveryMode(DeliveryMode.NON_PERSISTENT);
        producer.send(requestMsg);
        producer.close();
    }

}
```

This implementation is not very fortunate.
As a matter of fact we don't need `Future` at all as we are barely blocking on `get()`, synchronously waiting for a response.
Let's try with `DeferredResult`:

```java
@RequestMapping("/square/{value}")
@ResponseBody
public DeferredResult<String> square(@PathVariable double value) throws JMSException {
    final DeferredResult<String> deferredResult = new DeferredResult<>();
    final ListenableFuture<Double> responseFuture = request(value);
    Futures.addCallback(responseFuture, new FutureCallback<Double>() {
        @Override
        public void onSuccess(Double result) {
            deferredResult.setResult(result.toString());
        }

        @Override
        public void onFailure(Throwable t) {
            deferredResult.setErrorResult(t);
        }
    });
    return deferredResult;
}
```

Much more complex, but will also be much more scalable.
This method takes almost no time to execute and HTTP worker thread is shortly after ready to handle another request.
The biggest observation to make is that `onSuccess()` and `onFailure()` are executed by another thread, seconds or even minutes later.
But HTTP worker thread pool is not exhausted and application remains responsive.

This was a school book example, but can we do better?
First attempt is to write generic adapter from `ListenableFuture` to `DeferredResult`.
These two abstractions represent exactly the same thing, but with different API.
It's quite straightforward:

```java
public class ListenableFutureAdapter<T> extends DeferredResult<String> {

    public ListenableFutureAdapter(final ListenableFuture<T> target) {
        Futures.addCallback(target, new FutureCallback<T>() {
            @Override
            public void onSuccess(T result) {
                setResult(result.toString());
            }

            @Override
            public void onFailure(Throwable t) {
                setErrorResult(t);
            }
        });
    }
}
```

We simply extend `DeferredResult` and notify it using `ListenableFuture` callbacks.
Usage is simple:

```java
@RequestMapping("/square/{value}")
@ResponseBody
public DeferredResult<String> square(@PathVariable double value) throws JMSException {
    final ListenableFuture<Double> responseFuture = request(value);
    return new ListenableFutureAdapter<>(responseFuture);
}
```

But we can do even better!
If `ListenableFuture` and `DeferredResult` are so similar, why not simply return `ListenableFuture` from the controller handler method?

```java
@RequestMapping("/square/{value}")
@ResponseBody
public ListenableFuture<Double> square2(@PathVariable double value) throws JMSException {
    final ListenableFuture<Double> responseFuture = request(value);
    return responseFuture;
}
```

Well, it won't work because Spring doesn't understand `ListenableFuture` and will just blow up.
Fortunately Spring MVC is very flexible and it allows us to easily register new *so-called* [`HandlerMethodReturnValueHandler`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/web/method/support/HandlerMethodReturnValueHandler.html).
There are 12 such built-in handlers and every time we return some object from a controller, Spring MVC examines them in predefined order and chooses the first one that can handle given type.
One such handler is [`DeferredResultHandler`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/web/context/request/async/DeferredResult.DeferredResultHandler.html) (name says it all) which we will use as a reference:

```java
public class ListenableFutureReturnValueHandler implements HandlerMethodReturnValueHandler {

    public boolean supportsReturnType(MethodParameter returnType) {
        Class<?> paramType = returnType.getParameterType();
        return ListenableFuture.class.isAssignableFrom(paramType);
    }

    public void handleReturnValue(Object returnValue,
                                  MethodParameter returnType, ModelAndViewContainer mavContainer,
                                  NativeWebRequest webRequest) throws Exception {

        if (returnValue == null) {
            mavContainer.setRequestHandled(true);
            return;
        }

        final DeferredResult<Object> deferredResult = new DeferredResult<>();
        Futures.addCallback((ListenableFuture<?>) returnValue, new FutureCallback<Object>() {
            @Override
            public void onSuccess(Object result) {
                deferredResult.setResult(result.toString());
            }

            @Override
            public void onFailure(Throwable t) {
                deferredResult.setErrorResult(t);
            }
        });
        WebAsyncUtils.getAsyncManager(webRequest).startDeferredResultProcessing(deferredResult, mavContainer);
    }

}
```

Running out of karma, installing this handler is not as straightforward as I had hoped.
Technically there is [`WebMvcConfigurerAdapter.addReturnValueHandlers()`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/web/servlet/config/annotation/WebMvcConfigurerAdapter.html#addReturnValueHandlers(java.util.List)) which we can easily override if using Java configuration for Spring MVC.
But this method adds custom return value handler at the end of handlers chain and for reasons beyond the scope of this article we need to add it at the beginning (higher priority).
Fortunately with a little bit of hacking we can achieve that as well:

```java
@Configuration
@EnableWebMvc
public class SpringConfig extends WebMvcConfigurerAdapter {

    @Resource
    private RequestMappingHandlerAdapter requestMappingHandlerAdapter;

    @PostConstruct
    public void init() {
        final List<HandlerMethodReturnValueHandler> originalHandlers = new ArrayList<>(requestMappingHandlerAdapter.getReturnValueHandlers().getHandlers());
        originalHandlers.add(0, listenableFutureReturnValueHandler());
        requestMappingHandlerAdapter.setReturnValueHandlers(originalHandlers);
    }

    @Bean
    public HandlerMethodReturnValueHandler listenableFutureReturnValueHandler() {
        return new ListenableFutureReturnValueHandler();
    }

}
```

## Summary

In this article we familiarized ourselves with another incarnation of future/promise abstraction called `DeferredResult`.
It is used to postpone handling of HTTP request until some asynchronous task finishes.
Thus `DeferredResult` is great for web GUIs built on top of event-driven systems, message brokers, etc. It is not as powerful as raw Servlet 3.0 API though.
For example we cannot stream multiple events as they arrive (e.g.
new tweets) in long-running HTTP connection - Spring MVC is designed more toward request-response pattern.

We also tweaked Spring MVC to allow returning `ListenableFuture` from Guava directly from controller method.
It makes our code much cleaner and expressive.
