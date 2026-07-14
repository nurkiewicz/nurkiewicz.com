---
layout: post
title: 'Spring, Reactor and Elasticsearch: from callbacks to reactive streams'
date: '2018-01-10T00:58:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- CompletableFuture
- Netty
- elasticsearch
- mongodb
- redis
- reactor
- spring
- cassandra
modified_time: '2018-01-25T09:18:22.129+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1053604385907462269
blogger_orig_url: https://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch-from.html
image:
  path: /assets/img/spring-reactor-and-elasticsearch-from/hero.jpg
  alt: "Bieszczady mountains"
---

Spring 5 (and Boot 2, when it arrives in a [couple of weeks](https://github.com/spring-projects/spring-boot/milestones)) is a revolution.
Not the "*annotations over XML*" or "*Java classes over annotations*" type of revolution.
It's truly a revolutionary framework that enables writing a brand new class of applications.
Over the recent years, I became a little bit intimidated by this framework.
"Spring Cloud being framework that simplifies the usage of Spring Boot, being a framework that simplifies the usage of Spring, being a framework, that simplifies enterprise development."
[start.spring.io](https://start.spring.io/) (also known as "*start...
dot spring...
dot I...
O*") lists 120 different modules (!)
that you can add to your service.
Spring these days became an enormous umbrella project and I can imagine why some people (still!)
prefer Java EE (or whatever it's called these days).

But Spring 5 brings the reactive revolution.
It's no longer only a wrapper around blocking servlet API and various web frameworks.
Spring 5, on top of [Project Reactor](https://projectreactor.io/) allows writing high-performance, extremely fast and scalable servers, avoiding the servlet stack altogether.
Damn, there is no Jetty or even servlet API on the CLASSPATH!
At the heart of Spring 5 web-flux we will find [Netty](https://netty.io/), a low-level framework for writing asynchronous clients and servers.
Finally, Spring becomes first-class citizen in the family of reactive frameworks.
Java developers can implement fast services without leaving their comfort zone and going for [https://doc.akka.io/docs/akka-http/current/](https://draft.blogger.com/Akka%20HTTP) or [https://www.playframework.com/](https://draft.blogger.com/Play%20framework).
Spring 5 is a fully reactive, modern tool for building highly-scalable and resilient applications.
Nevertheless, the underlying principles like controllers, beans, dependency injection are all the same.
Moreover, upgrade path is smooth and we can gradually add features, rather than learning brand new, alien framework.
Enough of talking, let's write some code.

In this article, we will write a simple headless application that indexes documents in [ElasticSearch](https://www.elastic.co/products/elasticsearch) in large volume.
We aim for thousands of concurrent connections with just a handful of threads, even when the server becomes slow.
However, unlike e.g. Spring Data MongoDB, [Spring Data ElasticSearch](https://projects.spring.io/spring-data-elasticsearch/) does not natively support non-blocking repositories.
Well, the latter doesn't even seem to be maintained anymore, with current version being 3 years old.
Many articles target Spring 5 + MongoDB with its repositories returning non-blocking streams (`Flux` or `Flowable` from RxJava).
This one will be a little bit more advanced.

The [ElasticSearch 6 Java API](https://www.elastic.co/guide/en/elasticsearch/client/java-api/current/index.html) uses RESTful interface and is implemented using non-blocking HTTP client.
Unfortunately, it uses callbacks rather than something sane like `CompletableFuture`.
So let's build the client adapter ourselves.

# ElasticSearch client using Fluxes and Monos

Source code for this article is available at [github.com/nurkiewicz/elastic-flux](https://github.com/nurkiewicz) on [`reactive-elastic-search`](https://github.com/nurkiewicz/elastic-flux/tree/reactive-elastic-search) branch.

We would like to build an ElasticSearch Java client that supports Project Reactor by returning `Flux` or `Mono`.
Of course, we get the greatest benefit if the underlying stream is fully asynchronous and does not consume threads.
Luckily the Java API is just like that.
First, let's setup ElasticSearch's client as a Spring bean:

```java
import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

@Bean
RestHighLevelClient restHighLevelClient() {
    return new RestHighLevelClient(
            RestClient
                    .builder(new HttpHost("localhost", 9200))
                    .setRequestConfigCallback(config -> config
                            .setConnectTimeout(5_000)
                            .setConnectionRequestTimeout(5_000)
                            .setSocketTimeout(5_000)
                    )
                    .setMaxRetryTimeoutMillis(5_000));
}
```

In real life, we would obviously parametrize most of this stuff.
We will be indexing simple JSON documents, for the time being, their contents is not important:

```java
@Value
class Doc {
    private final String username;
    private final String json;
}
```

The code we will write wraps `RestHighLevelClient` and makes it even more *high-level* by returning `Mono<IndexResponse>`.
`Mono` is pretty much like `CompletableFuture` but with two exceptions:

- it's lazy - as long as you don't subscribe, no computation is started
- unlike `CompletableFuture`, `Mono` can complete normally without emitting any value

The second difference was always a bit misleading to me.
In RxJava 2.x there are two distinct types: `Single` (always completes with value or error) and `Maybe` (like `Mono`).
Too bad Reactor doesn't make this distinction.
Nevermind, how the adapter layer looks like?
The plain Elastic's API looks as follows:

```java
client.indexAsync(indexRequest, new ActionListener<IndexResponse>() {
    @Override
    public void onResponse(IndexResponse indexResponse) {
        //got response
    }

    @Override
    public void onFailure(Exception e) {
        //got error
    }
});
```

You can see where this is going: [*callback hell*](http://callbackhell.com/).
Rather than exposing custom `ActionListener` as an argument to this logic, let's wrap it in `Mono`:

```java
import org.elasticsearch.action.ActionListener;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;

import reactor.core.publisher.Mono;
import reactor.core.publisher.MonoSink;

private Mono<IndexResponse> indexDoc(Doc doc) {
    return Mono.create(sink -> {
        IndexRequest indexRequest = new IndexRequest("people", "person", doc.getUsername());
        indexRequest.source(doc.getJson(), XContentType.JSON);
        client.indexAsync(indexRequest, new ActionListener<IndexResponse>() {
            @Override
            public void onResponse(IndexResponse indexResponse) {
                sink.success(indexResponse);
            }

            @Override
            public void onFailure(Exception e) {
                sink.error(e);
            }
        });
    });
}
```

We must create `IndexRequest` wrapping JSON document and send it over RESTful API.
But that's not the point.
We are using `Mono.create()` method, it has some drawbacks, but more on that later.
`Mono` is lazy, so barely calling `indexDoc()` doesn't suffice, no HTTP request was made to ElasticSearch.
However every time someone subscribes to this one-element source, the logic inside `create()` will be executed.
Crucial lines are `sink.success()` and `sink.error()`.
They propagate results from ElasticSearch (coming from the background, asynchronous thread) into the stream.
How to use such method in practice?
It's very simple!

```java
Doc doc = //...
indexDoc(doc)
        .subscribe(
                indexResponse -> log.info("Got response")
        );
```

Of course the true power of reactive stream processing comes from composing multiple streams.
But we made our first steps: transforming callback-based asynchronous API into a generic stream.
If you are (un)lucky to use MongoDB, it has [built-in](https://docs.spring.io/spring-data/mongodb/docs/current/reference/html/#mongo.reactive) support for reactive types like `Mono` or `Flux` right in the repositories.
The same goes for [Cassandra](https://docs.spring.io/spring-data/cassandra/docs/current/reference/html/#cassandra.reactive) and [Redis](https://docs.spring.io/spring-data/redis/docs/current/reference/html/#redis:reactive).
In the next article, we will learn [how to generate some fake data](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html) and index it concurrently.

This is part of a longer series:

- Spring, Reactor and ElasticSearch: from callbacks to reactive streams
- [Spring, Reactor and ElasticSearch: bechmarking with fake test data](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html)
- [Monitoring and measuring reactive application with Dropwizard Metrics](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html)
- [Spring Boot 2: Migrating from Dropwizard metrics to Micrometer](http://www.nurkiewicz.com/2018/01/spring-boot-2-migrating-from-dropwizard.html)
- [Spring Boot 2: Fluxes, from Elasticsearch to controller](http://www.nurkiewicz.com/2018/01/spring-boot-2-fluxes-from-elasticsearch.html)
