---
layout: post
title: 'GraphQL server in Java: Part III: Improving concurrency'
date: '2020-03-23T22:56:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- graphql
modified_time: '2020-03-24T01:28:16.972+01:00'
thumbnail: /assets/img/graphql-server-in-java-part-iii/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2836052966215266716
blogger_orig_url: https://www.nurkiewicz.com/2020/03/graphql-server-in-java-part-iii.html
---

The idea behind GraphQL is to reduce the number of network round-trips by batching multiple, often unrelated requests, into a single network call.
This greatly reduces latency by delivering many pieces of information at once.
It’s especially useful when multiple sequential network round-trips can be replaced with a single one.
Well, honestly, every web browser does that automatically for us.
For example, when we open a website with several images, the browser will send HTTP requests for each image concurrently.
Or, to be precise, it will start not more than a certain number of connections to the same host.
It’s something between 2 and 8, depending on the browser.
The same applies to multiple AJAX/RESTful calls (see [`fetch()` API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)), which are concurrent by default with no extra work on a developer’s side.
Actually, that’s what *A* stands for in AJAX<sup>1</sup>.

## So, what’s the advantage of GraphQL?

If a web browser can make concurrent requests to multiple pieces of data at once already, why bother with GraphQL?
There are some advantages:

- if you need to make more than the allowed number of concurrent connections (max 2-8, see above), the browser will throttle you anyway, queuing some requests
- GraphQL prevents over-fetching and N+1 problem by returning only properties and relationships you explicitly asked for, not more, not less
- there is just one, batched request.
  Concurrency happens on the server side.
  Well, not really…

## GraphQL server is not utilizing concurrency by default

The last statement is *not true* by default, in Java’s implementation of GraphQL server.
Remember, we provided a bunch of resolvers for each non-trivial property and relationship.
Just as a reminder, this is how our resolver looks like:

```java
@Component
class PlayerResolver implements GraphQLResolver<Player> {

    Billing billing(Player player) //...
    String name(Player player) //...
    int points(Player player) //...
    ImmutableList<Item> inventory(Player player) //...

}
```

Each of these methods is invoked only on demand and each one is potentially heavyweight.
Unfortunately, by default GraphQL engine on the server side invokes resolver methods sequentially.
Therefore the overall latency is much worse compared to RESTful API (!)
Restful API would take advantage of the browser’s built-in concurrency.
To show how awful this behaves, I set up Zipkin and traced each resolver:

[![](/assets/img/graphql-server-in-java-part-iii/1.png)](/assets/img/graphql-server-in-java-part-iii/1.png)

Notice how entirely unrelated resolvers are waiting for each other.
Luckily this performance bottleneck is easy to fix.
Turns out GraphQL engine understands `CompletableFuture`!

## Asynchronous resolvers

Have a look at a revamped resolver API:

```java
@Component
class PlayerResolver implements GraphQLResolver<Player> {

    CompletableFuture<Billing> billing(Player player) //...
    CompletableFuture<String> name(Player player) //...
    CompletableFuture<Integer> points(Player player) //...
    CompletableFuture<List<Item>> inventory(Player player) //...

}
```

The source of concurrency is not important here.
It can be:

- Java 9’s [`HttpClient`](https://docs.oracle.com/en/java/javase/11/docs/api/java.net.http/java/net/http/HttpClient.html),
- Dedicated thread pool,
- Converting from Reactor’s reactive `Mono` using [`Mono.toFuture()`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Mono.html#toFuture--),
- Converting from Kotlin’s \[`Deferred`\] object using [`asCompletableFuture()`](https://kotlin.github.io/kotlinx.coroutines/kotlinx-coroutines-jdk8/kotlinx.coroutines.future/kotlinx.coroutines.-deferred/index.html)
- …

The point being, GraphQL takes that future into account and invokes multiple resolvers at the same time.
Just look how wonderful it looks in Zipkin:

[![](/assets/img/graphql-server-in-java-part-iii/2.png)](/assets/img/graphql-server-in-java-part-iii/2.png)

This image teaches us two things:

- the overall latency dropped from 1.1 seconds to 0.6 s - the sum of all latencies to the max of latencies
- even more importantly - did you notice how total latency is mostly affected by slow `inventory` resolver?
  Maybe, as a client, you can skip that property and cut latency by half?

GraphQL gives clients this fantastic opportunity to customize their queries in a fine-grained fashion.
It’s your decision how much data you want.
The API producer is no longer in charge.
Also, the API doesn’t have to be the lowest common denominator.
Each and every client makes an independent decision, rather than *one size fits all*.
Last but not least, being able to profile each and every resolver easily is a great win.
The [full source](https://github.com/nurkiewicz/graphql-server-demo) code for all articles in this series is available on GitHub, including Zipkin setup on Docker.

- [Part I: Basics](%7B%7B%20site.baseurl%20%7D%7D%7B%%20post_url%202019-10-01-graphql-server-in-java-part-i-basics%20%%7D)
- [Part II: Understanding Resolvers](%7B%7B%20site.baseurl%20%7D%7D%7B%%20post_url%202019-10-24-graphql-server-in-java-part-ii%20%%7D)
- Part III: Improving concurrency
- [github.com/nurkiewicz/graphql-server-demo](https://github.com/nurkiewicz/graphql-server-demo)

<sup>1</sup> - Coincidentally *X* in *AJAX* stands for… XML.
Well, a technology invented by Microsoft.
