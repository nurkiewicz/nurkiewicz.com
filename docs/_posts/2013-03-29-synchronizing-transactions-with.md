---
layout: post
title: Synchronizing transactions with asynchronous events in Spring
date: '2013-03-29T12:47:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- spring
modified_time: '2013-03-29T12:47:52.924+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8547134289457984863
blogger_orig_url: https://www.nurkiewicz.com/2013/03/synchronizing-transactions-with.html
---

Today as an example we will take a very simple scenario: placing an order stores it and sends an e-mail about that order:

```scala
@Service
class OrderService @Autowired() (orderDao: OrderDao, mailNotifier: OrderMailNotifier) {

    @Transactional
    def placeOrder(order: Order) {
        orderDao save order
        mailNotifier sendMail order
    }
}
```

So far so good, but e-mail functionality has nothing to do with placing an order.
It's just a side-effect that distracts rather than part of business logic.
Moreover sending an e-mail unnecessarily prolongs transaction and introduces latency.
So we decided to decouple these two actions by using events.
For simplicity I will take advantage of Spring built-in [custom events](http://static.springsource.org/spring/docs/3.2.x/spring-framework-reference/html/beans.html#context-functionality-events) but our discussion is equally relevant for JMS or other producer-consumer library/queue.

```scala
case class OrderPlacedEvent(order: Order) extends ApplicationEvent

@Service
class OrderService @Autowired() (orderDao: OrderDao, eventPublisher: ApplicationEventPublisher) {

    @Transactional
    def placeOrder(order: Order) {
        orderDao save order
        eventPublisher publishEvent OrderPlacedEvent(order)
    }

}
```

As you can see instead of accessing `OrderMailNotifier` bean directly we send `OrderPlacedEvent` wrapping newly created order.
[`ApplicationEventPublisher`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/context/ApplicationEventPublisher.html) is needed to send an event.
Of course we also have to implement the client side receiving messages:

```scala
@Service
class OrderMailNotifier extends ApplicationListener[OrderPlacedEvent] {

    def onApplicationEvent(event: OrderPlacedEvent) {
        //sending e-mail...
    }

}
```

`ApplicationListener[OrderPlacedEvent]` indicates what type of events are we interested in.
This works, however by default Spring `ApplicationEvent`s are synchronous, which means `publishEvent()` is actually blocking.
Knowing Spring it shouldn't be hard to turn event broadcasting into asynchronous mode.
Indeed there are two ways: one suggested in JavaDoc and the other I discovered because I failed to read the JavaDoc first...
According to documentation if you want your events to be delivered asynchronously, you should define bean named `applicationEventMulticaster` of type [`SimpleApplicationEventMulticaster`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/context/event/SimpleApplicationEventMulticaster.html) and define `taskExecutor`:

```scala
@Bean
def applicationEventMulticaster() = {
    val multicaster = new SimpleApplicationEventMulticaster()
    multicaster.setTaskExecutor(taskExecutor())
    multicaster
}

@Bean
def taskExecutor() = {
    val pool = new ThreadPoolTaskExecutor()
    pool.setMaxPoolSize(10)
    pool.setCorePoolSize(10)
    pool.setThreadNamePrefix("Spring-Async-")
    pool
}
```

Spring already supports broadcasting events using custom `TaskExecutor`.
I didn't know about it so first I simply annotated `onApplicationEvent()` with [`@Async`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/scheduling/annotation/Async.html):

```scala
@Async
def onApplicationEvent(event: OrderPlacedEvent) {  //...
```

no further modifications, once Spring discovers `@Async` method it runs it in different thread asynchronously.
Period.
Well, you still have to enable `@Async` support if you don't use it already:

```scala
@Configuration
@EnableAsync
class ThreadingConfig extends AsyncConfigurer {
    def getAsyncExecutor = taskExecutor()

    @Bean
    def taskExecutor() = {
        val pool = new ThreadPoolTaskExecutor()
        pool.setMaxPoolSize(10)
        pool.setCorePoolSize(10)
        pool.setThreadNamePrefix("Spring-Async-")
        pool
    }

}
```

Technically [`@EnableAsync`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/scheduling/annotation/EnableAsync.html) is enough.
However by default Spring uses [`SimpleAsyncTaskExecutor`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/core/task/SimpleAsyncTaskExecutor.html) which creates new thread on every `@Async` invocation.
A bit unfortunate default for enterprise framework, luckily easy to change.
Undoubtedly `@Async` seems cleaner than defining some magic beans.

------------------------------------------------------------------------

All above was just a setup to expose the real problem.
We now send an asynchronous message that is processed in other thread.
Unfortunately we introduced **race condition** that manifests itself under heavy load, or maybe only some particular operating system.
Can you spot it?
To give you a hint, here is what happens:

1.  Starting transaction
2.  Storing `order` in database
3.  Sending a message wrapping `order`
4.  Commit

In the meantime some asynchronous thread picks up `OrderPlacedEvent` and starts processing it.
The question is, does it happen right after point (3) but before point (4) or maybe after (4)?
That makes a big difference!
In the former case the transaction didn't yet committed, thus `Order` is not yet in the database.
On the other hand lazy loading *might* work on that object as it's still bound to a a `PersistenceContext` (in case we are using JPA).
However if the original transaction already committed, `order` will behave much differently.
If you rely on one behaviour or the other, due to race condition, your event listener might fail spuriously under heavy to predict circumstances.

Of course there is a solution<sup>1</sup>: using not commonly known [`TransactionSynchronizationManager`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/transaction/support/TransactionSynchronizationManager.html).
Basically it allows us to register arbitrary number of [`TransactionSynchronization` listeners](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/transaction/support/TransactionSynchronization.html).
Each such listener will then be notified about various events like transaction commit and rollback.
Here is a basic API:

```scala
@Transactional
def placeOrder(order: Order) {
    orderDao save order
    afterCommit {
        eventPublisher publishEvent OrderPlacedEvent(order)
    }
}

private def afterCommit[T](fun: => T) {
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronizationAdapter {
        override def afterCommit() {
            fun
        }
    })
}
```

`afterCommit()` takes a function and calls it after the current transaction commits.
We use it to hide the complexity of Spring API.
One can safely call `registerSynchronization()` multiple times - listeners are stored in a `Set` and are local to the current transaction, disappearing after commit.

So, the `publishEvent()` method will be called *after* the enclosing transaction commits, which makes our code predictable and race condition free.
However, even with higher order function `afterCommit()` it still feels a bit unwieldy and unnecessarily complex.
Moreover it's easy to forget wrapping every `publishEvent()`, thus maintainability suffers.
Can we do better?
One solution is to use write custom utility class wrapping `publishEvent()` or employ AOP.
But there is much simpler, proven solution that works great with Spring - the [Decorator pattern](http://en.wikipedia.org/wiki/Decorator_pattern).
We shall wrap original implementation of `ApplicationEventPublisher` provided by Spring and decorate its `publishEven()`:

```scala
class TransactionAwareApplicationEventPublisher(delegate: ApplicationEventPublisher)
    extends ApplicationEventPublisher {

    override def publishEvent(event: ApplicationEvent) {
        if (TransactionSynchronizationManager.isActualTransactionActive) {
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronizationAdapter {
                    override def afterCommit() {
                        delegate publishEvent event
                    }
                })
        }
        else
            delegate publishEvent event
    }

}
```

As you can see if the transaction is active, we register commit listener and postpone sending of a message until transaction is completed.
Otherwise we simply forward the event to original `ApplicationEventPublisher`, which delivers it immediately.
Of course we somehow have to plug this new implementation instead of the original one.
`@Primary` does the trick:

```scala
@Resource
val applicationContext: ApplicationContext = null

@Bean
@Primary
def transactionAwareApplicationEventPublisher() =
    new TransactionAwareApplicationEventPublisher(applicationContext)
```

Notice that the original implementation of `ApplicationEventPublisher` is provided by core `ApplicationContext` class.
After all these changes our code looks...
exactly the same as in the beginning:

```scala
@Service
class OrderService @Autowired() (orderDao: OrderDao, eventPublisher: ApplicationEventPublisher) {

    @Transactional
    def placeOrder(order: Order) {
        orderDao save order
        eventPublisher publishEvent OrderPlacedEvent(order)
    }
```

However this time auto-injected `eventPublisher` is our custom decorator.
Eventually we managed to fix the race condition problem without touching the business code.
Our solution is safe, predictable and robust.
Notice that the exact same approach can be taken for any other queuing technology, including JMS (if complex transaction manager was not used) or custom queues.
We also discovered an interesting low-level API for transaction lifecycle listening.
Might be useful one day.

------------------------------------------------------------------------

<sup>1</sup> - one might argue that a much simpler solution would be to `publishEvent()` outside of the transaction:

```scala
def placeOrder(order: Order) {
    storeOrder(order)
    eventPublisher publishEvent OrderPlacedEvent(order)
}

@Transactional
def storeOrder(order: Order) = orderDao save order
```

That's true, but this solution doesn't "*scale*" well (what if `placeOrder()` has to be part of a greater transaction?)
and is most likely incorrect due to [proxying peculiarities](http://nurkiewicz.blogspot.no/2011/10/spring-pitfalls-proxying.html).
