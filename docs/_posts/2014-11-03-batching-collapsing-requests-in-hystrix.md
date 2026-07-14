---
layout: post
title: Batching (collapsing) requests in Hystrix
date: '2014-11-03T09:20:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- Hystrix
- Spock
modified_time: '2014-11-03T09:20:44.244+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8896667209058947182
blogger_orig_url: https://www.nurkiewicz.com/2014/11/batching-collapsing-requests-in-hystrix.html
---

[Hystrix](https://github.com/Netflix/Hystrix) has an advanced feature of [collapsing (or batching)](https://github.com/Netflix/Hystrix/wiki/How-To-Use#Collapsing) requests.
If two or more commands run similar request at the same time, Hystrix can combine them together, run one batched request and dispatch split results back to all commands.
Let's first see how Hystrix works without collapsing.
Imagine we have a service that looks up `StockPrice` of a given `Ticker`:

```java
import lombok.Value;
import java.math.BigDecimal;
import java.time.Instant;

@Value
class Ticker {
    String symbol;
}

@Value
class StockPrice {
    BigDecimal price;
    Instant effectiveTime;
}

interface StockPriceGateway {

    default StockPrice load(Ticker stock) {
        final Set<Ticker> oneTicker = Collections.singleton(stock);
        return loadAll(oneTicker).get(stock);
    }

    ImmutableMap<Ticker, StockPrice> loadAll(Set<Ticker> tickers);
}
```

Core implementation of `StockPriceGateway` must provide `loadAll()` batch method while `load()` method is implemented for our convenience.
So our gateway is capable of loading multiple prices in one batch (e.g.
to reduce latency or network protocol overhead), but at the moment we are not using this feature, always loading price of one stock at a time:

```java
class StockPriceCommand extends HystrixCommand<StockPrice> {

    private final StockPriceGateway gateway;
    private final Ticker stock;

    StockPriceCommand(StockPriceGateway gateway, Ticker stock) {
        super(HystrixCommandGroupKey.Factory.asKey("Stock"));
        this.gateway = gateway;
        this.stock = stock;
    }

    @Override
    protected StockPrice run() throws Exception {
        return gateway.load(stock);
    }
}
```

Such command will always call `StockPriceGateway.load()` for each and every `Ticker`, as illustrated by the following tests:

```groovy
class StockPriceCommandTest extends Specification {

    def gateway = Mock(StockPriceGateway)

    def 'should fetch price from external service'() {
        given:
            gateway.load(TickerExamples.any()) >> StockPriceExamples.any()
            def command = new StockPriceCommand(gateway, TickerExamples.any())

        when:
            def price = command.execute()

        then:
            price == StockPriceExamples.any()
    }

    def 'should call gateway exactly once when running Hystrix command'() {
        given:
            def command = new StockPriceCommand(gateway, TickerExamples.any())

        when:
            command.execute()

        then:
            1 * gateway.load(TickerExamples.any())
    }

    def 'should call gateway twice when command executed two times'() {
        given:
            def commandOne = new StockPriceCommand(gateway, TickerExamples.any())
            def commandTwo = new StockPriceCommand(gateway, TickerExamples.any())

        when:
            commandOne.execute()
            commandTwo.execute()

        then:
            2 * gateway.load(TickerExamples.any())
    }

    def 'should call gateway twice even when executed in parallel'() {
        given:
            def commandOne = new StockPriceCommand(gateway, TickerExamples.any())
            def commandTwo = new StockPriceCommand(gateway, TickerExamples.any())

        when:
            Future<StockPrice> futureOne = commandOne.queue()
            Future<StockPrice> futureTwo = commandTwo.queue()

        and:
            futureOne.get()
            futureTwo.get()

        then:
            2 * gateway.load(TickerExamples.any())
    }

}
```

If you don't know Hystrix, by wrapping an external call in a command you gain a lot of features like timeouts, circuit breakers, etc. But this is not the focus of this article.
Look at last two tests: when asking for price of arbitrary ticker twice, sequentially or in parallel (`queue()`), our external `gateway` is also called twice.
Last test is especially interesting - we ask for the same ticker at almost the same time, but Hystrix can't figure that out.
These two commands are fully independent, will be executed in different threads and don't know anything about each other - even though they run at almost the same time.

Collapsing is all about finding such similar requests and combining them.
Batching (I will use this term interchangeably with *collapsing*) doesn't happen automatically and requires a bit of coding.
But first let's see how it behaves:

```groovy
def 'should collapse two commands executed concurrently for the same stock ticker'() {
    given:
        def anyTicker = TickerExamples.any()
        def tickers = [anyTicker] as Set

    and:
        def commandOne = new StockTickerPriceCollapsedCommand(gateway, anyTicker)
        def commandTwo = new StockTickerPriceCollapsedCommand(gateway, anyTicker)

    when:
        Future<StockPrice> futureOne = commandOne.queue()
        Future<StockPrice> futureTwo = commandTwo.queue()

    and:
        futureOne.get()
        futureTwo.get()

    then:
        0 * gateway.load(_)
        1 * gateway.loadAll(tickers) >> ImmutableMap.of(anyTicker, StockPriceExamples.any())
}

def 'should collapse two commands executed concurrently for the different stock tickers'() {
    given:
        def anyTicker = TickerExamples.any()
        def otherTicker = TickerExamples.other()
        def tickers = [anyTicker, otherTicker] as Set

    and:
        def commandOne = new StockTickerPriceCollapsedCommand(gateway, anyTicker)
        def commandTwo = new StockTickerPriceCollapsedCommand(gateway, otherTicker)

    when:
        Future<StockPrice> futureOne = commandOne.queue()
        Future<StockPrice> futureTwo = commandTwo.queue()

    and:
        futureOne.get()
        futureTwo.get()

    then:
        1 * gateway.loadAll(tickers) >> ImmutableMap.of(
                anyTicker, StockPriceExamples.any(),
                otherTicker, StockPriceExamples.other())
}

def 'should correctly map collapsed response into individual requests'() {
    given:
        def anyTicker = TickerExamples.any()
        def otherTicker = TickerExamples.other()
        def tickers = [anyTicker, otherTicker] as Set
        gateway.loadAll(tickers) >> ImmutableMap.of(
                anyTicker, StockPriceExamples.any(),
                otherTicker, StockPriceExamples.other())

    and:
        def commandOne = new StockTickerPriceCollapsedCommand(gateway, anyTicker)
        def commandTwo = new StockTickerPriceCollapsedCommand(gateway, otherTicker)

    when:
        Future<StockPrice> futureOne = commandOne.queue()
        Future<StockPrice> futureTwo = commandTwo.queue()

    and:
        def anyPrice = futureOne.get()
        def otherPrice = futureTwo.get()

    then:
        anyPrice == StockPriceExamples.any()
        otherPrice == StockPriceExamples.other()
}
```

First test proves that instead of calling `load()` twice we barely called `loadAll()` once.
Also notice that since we asked for the same `Ticker` (from two different threads), `loadAll()` asks for only one ticker.
Second test shows two concurrent requests for two different tickers being collapsed into one batch call.
Third test makes sure we still get proper responses to each individual request.
Instead of extending `HystrixCommand` we must extend more complex `HystrixCollapser`.
Now it's time to see `StockTickerPriceCollapsedCommand` implementation, that seamlessly replaced `StockPriceCommand`:

```java
class StockTickerPriceCollapsedCommand extends HystrixCollapser<ImmutableMap<Ticker, StockPrice>, StockPrice, Ticker> {

    private final StockPriceGateway gateway;
    private final Ticker stock;

    StockTickerPriceCollapsedCommand(StockPriceGateway gateway, Ticker stock) {
        super(HystrixCollapser.Setter.withCollapserKey(HystrixCollapserKey.Factory.asKey("Stock"))
                .andCollapserPropertiesDefaults(HystrixCollapserProperties.Setter().withTimerDelayInMilliseconds(100)));
        this.gateway = gateway;
        this.stock = stock;
    }

    @Override
    public Ticker getRequestArgument() {
        return stock;
    }

    @Override
    protected HystrixCommand<ImmutableMap<Ticker, StockPrice>> createCommand(Collection<CollapsedRequest<StockPrice, Ticker>> collapsedRequests) {
        final Set<Ticker> stocks = collapsedRequests.stream()
                .map(CollapsedRequest::getArgument)
                .collect(toSet());
        return new StockPricesBatchCommand(gateway, stocks);
    }

    @Override
    protected void mapResponseToRequests(ImmutableMap<Ticker, StockPrice> batchResponse, Collection<CollapsedRequest<StockPrice, Ticker>> collapsedRequests) {
        collapsedRequests.forEach(request -> {
            final Ticker ticker = request.getArgument();
            final StockPrice price = batchResponse.get(ticker);
            request.setResponse(price);
        });
    }

}
```

A lot is going on here, so let's review `StockTickerPriceCollapsedCommand` step by step.
First three generic types:

- `BatchReturnType` (`ImmutableMap<Ticker, StockPrice>` in our example) is the type of batched command response.
  As you will see later, collapser turns multiple small commands into a batch command.
  This is the type of that batch command's response.
  Notice that it's the same as `StockPriceGateway.loadAll()` type).
- `ResponseType` (`StockPrice`) is the type of each individual command being collapsed.
  In our case we are collapsing `HystrixCommand<StockPrice>`.
  Later we will split value of `BatchReturnType` into multiple `StockPrice`.
- `RequestArgumentType` (`Ticker`) is the input of each individual command we are about to collapse (batch).
  When multiple commands are batched together, we are eventually replacing all of them with one batched command.
  This command should receive all individual requests in order to perform one batch request.

`withTimerDelayInMilliseconds(100)` will be explained soon.
`createCommand()` creates a *batch* command.
This command should replace all individual commands and perform batched logic.
In our case instead of multiple individual `load()` calls we just make one:

```java
class StockPricesBatchCommand extends HystrixCommand<ImmutableMap<Ticker, StockPrice>> {

    private final StockPriceGateway gateway;
    private final Set<Ticker> stocks;

    StockPricesBatchCommand(StockPriceGateway gateway, Set<Ticker> stocks) {
        super(HystrixCommandGroupKey.Factory.asKey("Stock"));
        this.gateway = gateway;
        this.stocks = stocks;
    }

    @Override
    protected ImmutableMap<Ticker, StockPrice> run() throws Exception {
        return gateway.loadAll(stocks);
    }
}
```

The only difference between this class and `StockPriceCommand` is that it takes a bunch of `Ticker`s and returns prices for all of them.
Hystrix will collect a few instances of `StockTickerPriceCollapsedCommand` and once it has *enough* (more on that later) it will create single `StockPriceCommand`.
Hope this is clear, because `mapResponseToRequests()` is slightly more involved.
Once our collapsed `StockPricesBatchCommand` finishes, we must somehow split batch response and communicate replies back to individual commands, unaware of collapsing.
From that perspective `mapResponseToRequests()` implementation is fairly straightforward: we receive batch response and a collection of wrapped `CollapsedRequest<StockPrice, Ticker>`.
We must now iterate over all awaiting individual requests and complete them (`setResponse()`).
If we don't complete some of the requests, they will hang infinitely and eventually time out.

# How it works

This is the right moment to describe how collapsing is implemented.
I said before that collapsing happens when two requests occur at the same time.
There is no such thing as *the same time*.
In reality when first collapsible request comes in, Hystrix starts a timer.
In our examples we set it to 100 milliseconds.
During that period our command is suspended, waiting for other commands to join.
After this configurable period Hystrix will call `createCommand()`, gathering all request keys (by calling `getRequestArgument()`) and run it.
When batched command finishes, it will let us dispatch results to all awaiting individual commands.
It is also possible to limit the number of collapsed requests if we are afraid of creating humongous batch - on the other hand how many concurrent requests can fit within this short time slot?

# Use cases and drawbacks

Request collapsing should be used in systems with extreme load - high frequency of requests.
If you get just one request per collapsing time window (100 milliseconds in examples), collapsing will just add overhead.
That's because every time you call collapsible command, it must wait just in case some other command wants to join and form batch.
This makes sense only when at least couple of commands are collapsed.
Time wasted for waiting is balanced by savings in network latency and/or better utilization of resources in our collaborator (very often batch requests are much faster compared to individual calls).
But keep in mind collapsing is a double edged sword, useful in specific cases.

Last thing to remember - in order to use request collapsing you need `HystrixRequestContext.initializeContext()` and `shutdown()` in `try-finally` block:

```java
HystrixRequestContext context = HystrixRequestContext.initializeContext();
try {
    //...
} finally {
    context.shutdown();
}
```

# Collapsing vs. caching

You might think that collapsing can be replaced with proper caching.
This is not true.
You use cache when:

1.  resource is likely to be accessed multiple times
2.  we can safely use previous value, it will remain valid for some period of time **or** we know precisely how to invalidate it
3.  we can afford concurrent requests for the same resource to compute it multiple times

On the other hand collapsing does not enforce locality of data (1), it always hits the real service and never returns stale data (2).
And finally if we ask for the same resource from multiple threads, we will only call backing service once (3).
In case of caching, unless your cache is really smart, two threads will independently discover absence of given resource in cache and ask backing service twice.
However collapsing can work *together* with caching - by consulting cache before running collapsible command.

# Summary

Request collapsing is a useful tool, but with very limited use cases.
It can significantly improve throughput in our system as well as limit load in external service.
Collapsing can magically flatten peaks in traffic, rather than spreading it all over.
Just make sure you are using it for commands running with extreme frequency.
