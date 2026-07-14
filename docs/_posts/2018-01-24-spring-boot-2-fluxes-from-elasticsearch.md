---
layout: post
title: 'Spring Boot 2: Fluxes, from Elasticsearch to controller'
date: '2018-01-24T23:58:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- elasticsearch
- reactor
- spring
- webflux
modified_time: '2018-01-25T09:17:36.394+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9174529763160406901
blogger_orig_url: https://www.nurkiewicz.com/2018/01/spring-boot-2-fluxes-from-elasticsearch.html
image:
  path: /assets/img/spring-boot-2-fluxes-from-elasticsearch/hero.jpg
  alt: "Bieszczady Mountains"
---

The [final piece of the puzzle](http://www.nurkiewicz.com/2018/01/spring-boot-2-migrating-from-dropwizard.html) in our series is exposing reactive APIs via RESTful interfaces.
Previously [we were seeding our Elasticsearch with some sample fake data](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html).
Now it's about time to expose indexing functionality through some API.
Let's start with some simple adapter to our indexing engine:

```java
import lombok.RequiredArgsConstructor;
import org.elasticsearch.action.ActionListener;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;
import reactor.core.publisher.MonoSink;

@Component
@RequiredArgsConstructor
class ElasticAdapter {

    private final RestHighLevelClient client;
    private final ObjectMapper objectMapper;

    Mono<IndexResponse> index(Person doc) {
        return indexDoc(doc);
    }

    private void doIndex(Person doc, ActionListener<IndexResponse> listener) throws JsonProcessingException {
        return Mono.create(sink -> {
            try {
                doIndex(doc, listenerToSink(sink));
            } catch (JsonProcessingException e) {
                sink.error(e);
            }
        });
    }

    private void doIndex(Person doc, ActionListener<IndexResponse> listener) throws JsonProcessingException {
        final IndexRequest indexRequest = new IndexRequest("people", "person", doc.getUsername());
        final String json = objectMapper.writeValueAsString(doc);
        indexRequest.source(json, XContentType.JSON);
        client.indexAsync(indexRequest, listener);
    }

    private <T> ActionListener<T> listenerToSink(MonoSink<T> sink) {
        return new ActionListener<T>() {
            @Override
            public void onResponse(T response) {
                sink.success(response);
            }

            @Override
            public void onFailure(Exception e) {
                sink.error(e);
            }
        };
    }

}
```

The `index()` method takes a strongly typed [`Person` object](https://github.com/nurkiewicz/elastic-flux/blob/master/src/main/java/com/nurkiewicz/elasticflux/Person.java) and sends it over to Elasticsearch.
First the `doIndex()` method makes the actual call to Elasticsearch, marshalling `Person` to JSON.
Having Elastic's result of type `ActionListener<IndexResponse>` we convert it to `Mono<IndexResponse>`.
This is done via `listenerToSink()` helper method.
The sequence of `compose()` methods are an elegant way to apply a series of metrics:

```java
return indexDoc(doc)
        .compose(this::countSuccFail)
        .compose(this::countConcurrent)
        .compose(this::measureTime)
        .doOnError(e -> log.error("Unable to index {}", doc, e));
```

These methods are defined as follows:

```java
private final Timer indexTimer = Metrics.timer("es.timer");
private final LongAdder concurrent = Metrics.gauge("es.concurrent", new LongAdder());
private final Counter successes = Metrics.counter("es.index", "result", "success");
private final Counter failures = Metrics.counter("es.index", "result", "failure");

private Mono<IndexResponse> countSuccFail(Mono<IndexResponse> mono) {
    return mono
            .doOnError(e -> failures.increment())
            .doOnSuccess(response -> successes.increment());
}

private Mono<IndexResponse> countConcurrent(Mono<IndexResponse> mono) {
    return mono
            .doOnSubscribe(s -> concurrent.increment())
            .doOnTerminate(concurrent::decrement);
}

private Mono<IndexResponse> measureTime(Mono<IndexResponse> mono) {
    return Mono
            .fromCallable(System::currentTimeMillis)
            .flatMap(time ->
                    mono.doOnSuccess(response ->
                            indexTimer.record(System.currentTimeMillis() - time, TimeUnit.MILLISECONDS))
            );
}
```

We could technically apply these metrics without `compose()` operator like this:

```java
measureTime(
        countConcurrent(
                countSuccFail(
                        indexDoc(doc)
                )
        )
)
```

But having a flat sequence of `Mono<T>` -\> `Mono<T>` transformers seems much easier to read.
Anyway, this was the write side, let's implement the read side.

```java
Mono<Person> findByUserName(String userName) {
    return Mono
            .<GetResponse>create(sink ->
                    client.getAsync(new GetRequest("people", "person", userName), listenerToSink(sink))
            )
            .filter(GetResponse::isExists)
            .map(GetResponse::getSource)
            .map(map -> objectMapper.convertValue(map, Person.class));
}
```

The procedure is pretty much the same:

- make Elasticsearch request
- adapt it to `Mono<GetResponse>`
- verify the result and unmarshall it from `Map` to `Person` object

Interestingly Jackson's `ObjectMapper` can also convert from `Map`, not only from JSON string.
Having this layer we can use it directly in our brand new controller:

```java
import lombok.RequiredArgsConstructor;
import org.elasticsearch.action.index.IndexResponse;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import javax.validation.Valid;
import java.util.Map;

@RequiredArgsConstructor
@RestController
@RequestMapping("/person")
class PersonController {

    private static final Mono<ResponseEntity<Person>> NOT_FOUND = 
            Mono.just(ResponseEntity.notFound().build());

    private final ElasticAdapter elasticAdapter;

    @GetMapping("/{userName}")
    Mono<ResponseEntity<Person>> get(@PathVariable("userName") String userName) {
        return elasticAdapter
                .findByUserName(userName)
                .map(ResponseEntity::ok)
                .switchIfEmpty(NOT_FOUND);
    }

    @PutMapping
    Mono<ResponseEntity<Map<String, Object>>> put(@Valid @RequestBody Person person) {
        return elasticAdapter
                .index(person)
                .map(this::toMap)
                .map(m -> ResponseEntity.status(HttpStatus.CREATED).body(m));
    }

    private ImmutableMap<String, Object> toMap(IndexResponse response) {
        return ImmutableMap
                .<String, Object>builder()
                .put("id", response.getId())
                .put("index", response.getIndex())
                .put("type", response.getType())
                .put("version", response.getVersion())
                .put("result", response.getResult().getLowercase())
                .put("seqNo", response.getSeqNo())
                .put("primaryTerm", response.getPrimaryTerm())
                .build();
    }

}
```

`get()` method tries to find a document in Elasticsearch by `"userName"`.
Newcomers to RxJava or Reactor are very eager to call `subscribe()` or `block*()`.
Interestingly none of these are needed in [Spring WebFlux](https://docs.spring.io/spring/docs/current/spring-framework-reference/web-reactive.html#spring-webflux).
You create a bunch of `Mono`s or `Flux`es, pass them through a series of transformations and return from your controller.
Just works™.

`put()` method is equally simple.
For debug purposes I convert `IndexResponse` to JSON in `toMap()` method, but this isn't necessary.
As you can see building reactive applications in Spring WebFlux is quite simple.
We no longer need any adapting layers or blocking code.
Everything is fully asynchronous and event-driven.
Moreover in this setup (see [source code](https://github.com/nurkiewicz/elastic-flux)) there are no servlets or Jetty/Tomcat on the CLASSPATH!

Spring has built-in reactive support for some databases like MongoDB.
In these blog posts I gave you an overview how to integrate Reactor with Spring and other databases that provide non-blocking API.
You can easily adjust code samples to use it with other sources and data stores.

This is part of a longer series:

- [Spring, Reactor and ElasticSearch: from callbacks to reactive streams](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch-from.html)
- [Spring, Reactor and ElasticSearch: bechmarking with fake test data](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html)
- [Monitoring and measuring reactive application with Dropwizard Metrics](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html)
- [Spring Boot 2: Migrating from Dropwizard metrics to Micrometer](http://www.nurkiewicz.com/2018/01/spring-boot-2-migrating-from-dropwizard.html)
- Spring Boot 2: Fluxes, from Elasticsearch to controller
