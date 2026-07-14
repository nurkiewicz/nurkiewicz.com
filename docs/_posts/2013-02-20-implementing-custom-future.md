---
layout: post
title: Implementing custom Future
date: '2013-02-20T20:38:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- jms
- multithreading
- concurrency
modified_time: '2013-02-20T20:38:31.551+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2326339500428441136
blogger_orig_url: https://www.nurkiewicz.com/2013/02/implementing-custom-future.html
image:
  path: /assets/img/implementing-custom-future/hero.jpg
  alt: "Oslo seen from Grefsenkollen"
---

Last time we learned the [principles behind `java.util.concurrent.Future<T>`](http://nurkiewicz.com/2013/02/javautilconcurrentfuture-basics.html).
We also discovered that `Future<T>` is typically returned by libraries or frameworks.
But there is nothing stopping us from implementing it all by ourselves when it makes sense.
It is not particularly complex and may significantly improve your design.
I did my best to pick interesting use case for our example.

[JMS (Java Message Service)](http://en.wikipedia.org/wiki/Java_Message_Service) is a standard Java API for sending asynchronous messages.
When we think about JMS, we immediately see a client sending a message to a server (broker) in a *fire and forget* manner.
But it is equally common to implement [*request-reply* messaging pattern](http://www.eaipatterns.com/RequestReplyJmsExample.html) on top of JMS.
The implementation is fairly simple: you send a request message (of course asynchronously) to an MDB on the other side.
MDB processes the request and sends a reply back either to hardcoded *reply* queue or to an arbitrary queue chosen by the client and sent along with the message in `JMSReplyTo` property.
The second scenario is much more interesting.
Client can create a temporary queue and use it as a reply queue when sending a request.
This way each request/reply pair uses different reply queue, this there is no need for correlation ID, selectors, etc.

There is one catch, however.
Sending a message to JMS broker is simple and asynchronous.
But receiving reply is much more cumbersome.
You can either implement [`MessageListener`](http://docs.oracle.com/javaee/6/api/javax/jms/MessageListener.html) to consume one, single message or use blocking [`MessageConsumer.receive()`](http://docs.oracle.com/javaee/6/api/javax/jms/MessageConsumer.html#receive()).
First approach is quite heavyweight and hard to use in practice.
[Second one](http://activemq.apache.org/how-should-i-implement-request-response-with-jms.html) defeats the purpose of asynchronous messaging.
You can also poll the reply queue with some interval, which sounds even worse.

Knowing the `Future` abstraction by now you should have some design idea.
What if we can send a request message and get a `Future<T>` back, representing reply message that didn't came yet?
This `Future` abstraction should handle all the logic and we can safely use it as a handle to future outcome.
Here is the plumbing code used to create temporary queue and send request:

```java
private <T extends Serializable> Future<T> asynchRequest(ConnectionFactory connectionFactory, Serializable request, String queue) throws JMSException {
    Connection connection = connectionFactory.createConnection();
    connection.start();
    final Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
    final Queue tempReplyQueue = session.createTemporaryQueue();
    final ObjectMessage requestMsg = session.createObjectMessage(request);
    requestMsg.setJMSReplyTo(tempReplyQueue);
    sendRequest(session.createQueue(queue), session, requestMsg);
    return new JmsReplyFuture<T>(connection, session, tempReplyQueue);
}
```

`asynchRequest()` method simply takes a [`ConnectionFactory`](http://docs.oracle.com/javaee/6/api/javax/jms/ConnectionFactory.html) to JMS broker and arbitrary piece of data.
This object will be sent to `queue` using `ObjectMessage`.
Last line is crucial - we return our custom `JmsReplyFuture<T>` that will represent *not-yet-received* reply.
Notice how we pass temporary JMS queue to both `JMSReplyTo` property and our `Future`.
Implementation of the MDB side is not that important.
Needless to say it is suppose to send a reply back to designated queue:

```java
final ObjectMessage reply = session.createObjectMessage(...);
session.createProducer(request.getJMSReplyTo()).send(reply);
```

So let's dive into the implementation of `JmsReplyFuture<T>`.
I made an assumption that both request and reply are `ObjectMessage`s.
It's not very challenging to use a different type of message.
First of all let us see how receiving messages from reply channel is set up:

```java
public class JmsReplyFuture<T extends Serializable> implements Future<T>, MessageListener {

    //...

    public JmsReplyFuture(Connection connection, Session session, Queue replyQueue) throws JMSException {
        this.connection = connection;
        this.session = session;
        replyConsumer = session.createConsumer(replyQueue);
        replyConsumer.setMessageListener(this);
    }

    @Override
    public void onMessage(Message message) {
        //...
    }

}
```

As you can see `JmsReplyFuture` implements both `Future<T>` (where `T` is expected type of object wrapped inside `ObjectMessage`) and JMS `MessageListener`.
In the constructor we simply start listening on `replyQueue`.
From our design assumptions we know that there will be at most one message there because reply queue is temporary throw away queue.
[In the previous article](http://nurkiewicz.com/2013/02/javautilconcurrentfuture-basics.html) we learned that `Future.get()` should block while waiting for a result.
On the other hand `onMessage()` is a callback method called from some internal JMS client thread/library.
Apparently we need some shared variable/lock to let waiting `get()` know that reply arrived.
Preferably our solution should be lightweight and not introduce any latency so busy waiting on `volatile` variable is a bad idea.
Initially I though about [`Semaphore`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Semaphore.html) that I would use to unblock `get()` from `onMessage()`.
But I would still need some shared variable to hold the actual reply object.
So I came up with an idea of using [`ArrayBlockingQueue`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ArrayBlockingQueue.html).
It might sound strange to use a queue when we know there will be no more that one item.
But it works perfectly, utilizing good old producer-consumer pattern: `Future.get()` is a consumer blocking on an empty queue's `poll()` method.
On the other hand `onMessage()` is a producer, placing reply message in that queue and immediately unblocking consumer.
Here is how it looks:

```java
public class JmsReplyFuture<T extends Serializable> implements Future<T>, MessageListener {

    private final BlockingQueue<T> reply = new ArrayBlockingQueue<>(1);

    //...

    @Override
    public T get() throws InterruptedException, ExecutionException {
        return this.reply.take();
    }

    @Override
    public T get(long timeout, TimeUnit unit) throws InterruptedException, ExecutionException, TimeoutException {
        final T replyOrNull = reply.poll(timeout, unit);
        if (replyOrNull == null) {
            throw new TimeoutException();
        }
        return replyOrNull;
    }

    @Override
    public void onMessage(Message message) {
        final ObjectMessage objectMessage = (ObjectMessage) message;
        final Serializable object = objectMessage.getObject();
        reply.put((T) object);
        //...
    }

}
```

The implementation is still not complete, but it covers most important concepts.
Notice how nicely [`BlockingQueue.poll(long, TimeUnit)`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/BlockingQueue.html#poll(long,%20java.util.concurrent.TimeUnit)) method fits into [`Future.get(long, TimeUnit)`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Future.html#get(long,%20java.util.concurrent.TimeUnit)).
Unfortunately, even though they come from the same package and were developed more or less in the same time, one method returns `null` upon timeout while the other should throw an exception.
Easy to fix.

Also notice how easy the implementation of `onMessage()` became.
We just place newly received message in a `BlockingQueue reply` and the collection does all the synchronization for us.
We are still missing some less significant, but still important details - cancelling and clean up.
Without going much into details, here is a full implementation:

```java
public class JmsReplyFuture<T extends Serializable> implements Future<T>, MessageListener {

    private static enum State {WAITING, DONE, CANCELLED}

    private final Connection connection;
    private final Session session;
    private final MessageConsumer replyConsumer;
    private final BlockingQueue<T> reply = new ArrayBlockingQueue<>(1);
    private volatile State state = State.WAITING;

    public JmsReplyFuture(Connection connection, Session session, Queue replyQueue) throws JMSException {
        this.connection = connection;
        this.session = session;
        replyConsumer = session.createConsumer(replyQueue);
        replyConsumer.setMessageListener(this);
    }

    @Override
    public boolean cancel(boolean mayInterruptIfRunning) {
        try {
            state = State.CANCELLED;
            cleanUp();
            return true;
        } catch (JMSException e) {
            throw Throwables.propagate(e);
        }
    }

    @Override
    public boolean isCancelled() {
        return state == State.CANCELLED;
    }

    @Override
    public boolean isDone() {
        return state == State.DONE;
    }

    @Override
    public T get() throws InterruptedException, ExecutionException {
        return this.reply.take();
    }

    @Override
    public T get(long timeout, TimeUnit unit) throws InterruptedException, ExecutionException, TimeoutException {
        final T replyOrNull = reply.poll(timeout, unit);
        if (replyOrNull == null) {
            throw new TimeoutException();
        }
        return replyOrNull;
    }

    @Override
    public void onMessage(Message message) {
        try {
            final ObjectMessage objectMessage = (ObjectMessage) message;
            final Serializable object = objectMessage.getObject();
            reply.put((T) object);
            state = State.DONE;
            cleanUp();
        } catch (Exception e) {
            throw Throwables.propagate(e);
        }
    }

    private void cleanUp() throws JMSException {
        replyConsumer.close();
        session.close();
        connection.close();
    }
}
```

I use special `State` enum to hold the information about state.
I find it much more readable compared to complex conditions based on multiple flags, `null` checks, etc. Second thing to keep in mind is cancelling.
Fortunately it's quite simple.
We basically close the underlying session/connection.
It has to remain open throughout the course of whole request/reply message exchange, otherwise temporary JMS reply queue disappears.
Note that we cannot easily inform broker/MDB that we are no longer interested about the reply.
We simply stop listening for it, but MDB will still process request and try to send a reply to no longer existing temporary queue.

------------------------------------------------------------------------

So how does this all look in practice?
Say we have an MDB that receives a number and returns a square of it.
Imagine the computation takes a little bit of time so we start it in advance, do some work in the meantime and later retrieve the results.
Here is how such a design might look like:

```java
final Future<Double> replyFuture = asynchRequest(connectionFactory, 7, "square");
//do some more work
final double resp = replyFuture.get();      //49
```

Where `"square"` is the name of request queue.
If we refactor it and use dependency injection we can further simplify it to something like:

```java
final Future<Double> replyFuture = calculator.square(7);
//do some more work
final double resp = replyFuture.get();      //49
```

You know what's best about this design?
Even though we are exploiting quite advanced JMS capabilities, there is no JMS code here.
Moreover we can later replace `calculator` with a different implementation, using SOAP or GPU.
As far as the client code is concerned, we still use `Future<Double>` abstraction.
Computation result that is not yet available.
The underlying mechanism is irrelevant.
That is the beauty of abstraction.

------------------------------------------------------------------------

Obviously this implementation is not production ready (by far).
But even worse, it misses some essential features.
We still call blocking `Future.get()` at some point.
Moreover there is no way of composing/chaining futures (e.g.
*when the response arrives, send another message*) or waiting for the *fastest* future to complete.
Be patient!
