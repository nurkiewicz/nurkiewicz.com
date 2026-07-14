---
layout: post
title: 'Spring, Reactor and Elasticsearch: bechmarking with fake test data'
date: '2018-01-12T07:04:00.002+01:00'
author: Tomasz Nurkiewicz
tags:
- elasticsearch
- jfairy
- reactor
modified_time: '2018-01-25T09:18:29.959+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4517248198959573721
blogger_orig_url: https://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch.html
image:
  path: /assets/img/spring-reactor-and-elasticsearch/hero.jpg
  alt: "Bieszczady Moutains"
---

In the [previous article](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch-from.html) we created a simple adapter from ElasticSearch's API to Reactor's `Mono`, that looks like this:

```java
import reactor.core.publisher.Mono;

private Mono<IndexResponse> indexDoc(Doc doc) {
    //...
}
```

Now we would like to run this method at controlled concurrency level, millions of times.
Basically, we want to see how our indexing code behaves under load, benchmark it.

## Fake data with jFairy

First, we need some good looking test data.
For that purpose, we'll use a handy [jFairy](https://devskiller.github.io/jfairy/) library.
The document we'll index is a simple POJO:

```java
@Value
class Doc {
    private final String username;
    private final String json;
}
```

The generation logic is wrapped inside a Java class:

```java
import io.codearte.jfairy.Fairy;
import io.codearte.jfairy.producer.person.Address;
import io.codearte.jfairy.producer.person.Person;
import org.apache.commons.lang3.RandomUtils;


@Component
class PersonGenerator {

    private final ObjectMapper objectMapper;
    private final Fairy fairy;

    private Doc generate() {
        Person person = fairy.person();
        final String username = person.getUsername() + RandomUtils.nextInt(1_000_000, 9_000_000);
        final ImmutableMap<String, Object> map = ImmutableMap.<String, Object>builder()
                .put("address", toMap(person.getAddress()))
                .put("firstName", person.getFirstName())
                .put("middleName", person.getMiddleName())
                .put("lastName", person.getLastName())
                .put("email", person.getEmail())
                .put("companyEmail", person.getCompanyEmail())
                .put("username", username)
                .put("password", person.getPassword())
                .put("sex", person.getSex())
                .put("telephoneNumber", person.getTelephoneNumber())
                .put("dateOfBirth", person.getDateOfBirth())
                .put("company", person.getCompany())
                .put("nationalIdentityCardNumber", person.getNationalIdentityCardNumber())
                .put("nationalIdentificationNumber", person.getNationalIdentificationNumber())
                .put("passportNumber", person.getPassportNumber())
                .build();
        final String json = objectMapper.writeValueAsString(map);
        return new Doc(username, json);
    }

    private ImmutableMap<String, Object> toMap(Address address) {
        return ImmutableMap.<String, Object>builder()
                .put("street", address.getStreet())
                .put("streetNumber", address.getStreetNumber())
                .put("apartmentNumber", address.getApartmentNumber())
                .put("postalCode", address.getPostalCode())
                .put("city", address.getCity())
                .put("lines", Arrays.asList(address.getAddressLine1(), address.getAddressLine2()))
                .build();
    }

}
```

Quite a bit of boring code which actually does something cool.
Every time we run it, it generates random, but reasonable JSON like so:

```json
{
  "address": {
    "street": "Ford Street",
    "streetNumber": "32",
    "apartmentNumber": "",
    "postalCode": "63913",
    "city": "San Francisco",
    "lines": [
      "32 Ford Street",
      "San Francisco 63913"
    ]
  },
  "firstName": "Evelyn",
  "middleName": "",
  "lastName": "Pittman",
  "email": "pittman@mail.com",
  "companyEmail": "evelyn.pittman@woodsllc.eu",
  "username": "epittman5795354",
  "password": "VpEfFmzG",
  "sex": "FEMALE",
  "telephoneNumber": "368-005-109",
  "dateOfBirth": "1917-05-14T16:47:06.273Z",
  "company": {
    "name": "Woods LLC",
    "domain": "woodsllc.eu",
    "email": "contact@woodsllc.eu",
    "vatIdentificationNumber": "30-0005081",
    "url": "http://www.woodsllc.eu"
  },
  "nationalIdentityCardNumber": "713-79-5185",
  "nationalIdentificationNumber": "",
  "passportNumber": "jVeyZLSt3"
}
```

Neat!
Unfortunately, it's not documented whether [jFairy is thread safe](https://github.com/Devskiller/jfairy/issues/95) so just in case in real code, I'm using `ThreadLocal`.
OK, so we have one document, but we need millions!
Using `for`-loop is so old-fashioned.
What will you tell about an infinite stream of random people?

```java
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;

private final Scheduler scheduler = Schedulers.newParallel(PersonGenerator.class.getSimpleName());

Mono<Doc> generateOne() {
    return Mono
            .fromCallable(this::generate)
            .subscribeOn(scheduler);
}

Flux<Doc> infinite() {
    return generateOne().repeat();
}
```

`generateOne()` wraps blocking `generate()` method in a `Mono<Doc>`.
Additionally `generate()` is run on `parallel` `Scheduler`.
Why?
It turned out that jFairy wasn't fast-enough on a single core (lots of random number generation, table lookups, etc.)
so I had to parallelize data generation.
Shouldn't normally be an issue.
But when generating fake data is slower than your reactive application that touches external server - it tells you something about the performance of Netty-based Spring web-flux (!)

## Calling ElasticSearch concurrently

All right, having an infinite stream of good looking fake test data we now want to index it in ElasticSearch.

```java
@PostConstruct
void startIndexing() {
    index(1_000_000, 1_000);
}

private void index(int count, int maxConcurrency) {
    personGenerator
            .infinite()
            .take(count)
            .flatMap(this::indexDocSwallowErrors, maxConcurrency)
            .window(Duration.ofSeconds(1))
            .flatMap(Flux::count)
            .subscribe(winSize -> log.debug("Got {} responses in last second", winSize));
}

private Mono<IndexResponse> indexDocSwallowErrors(Doc doc) {
    return indexDoc(doc)
            .doOnError(e -> log.error("Unable to index {}", doc, e))
            .onErrorResume(e -> Mono.empty());
}
```

When the application starts it initiates indexing of 1 million documents.
Notice how easy it is to tell Reactor (same for RxJava) that it should invoke up to one thousand concurrent requests to ElasticSearch.
Once every second we count how many responses we received:

```text
Got 2925 responses in last second
Got 2415 responses in last second
Got 3336 responses in last second
Got 2199 responses in last second
Got 1861 responses in last second
```

Not bad!
Especially when you consider that there are up to **one thousand** concurrent HTTP requests and our application started barely 30 threads peak (!)
Alright, it's `localhost` \<-\> `localhost`, guilty!
But how do we actually know all of that?
Logging is fine, but it's XXI century, we can do better!
[Monitoring will be the subject of next instalment](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html).

The source code is available [github.com/nurkiewicz/elastic-flux](https://github.com/nurkiewicz/elastic-flux) in [](https://github.com/nurkiewicz/elastic-flux/tree/reactive-elastic-search)

This is part of a longer series:

- [Spring, Reactor and ElasticSearch: from callbacks to reactive streams](http://www.nurkiewicz.com/2018/01/spring-reactor-and-elasticsearch-from.html)
- Spring, Reactor and ElasticSearch: bechmarking with fake test data
- [Monitoring and measuring reactive application with Dropwizard Metrics](http://www.nurkiewicz.com/2018/01/monitoring-and-measuring-reactive.html)
- [Spring Boot 2: Migrating from Dropwizard metrics to Micrometer](http://www.nurkiewicz.com/2018/01/spring-boot-2-migrating-from-dropwizard.html)
- [Spring Boot 2: Fluxes, from Elasticsearch to controller](http://www.nurkiewicz.com/2018/01/spring-boot-2-fluxes-from-elasticsearch.html)

`reactive-elastic-search` branch.
