---
layout: post
title: 'GraphQL server in Java: Part II: Understanding Resolvers'
date: '2019-10-24T20:43:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- graphql
modified_time: '2020-03-24T01:27:25.567+01:00'
thumbnail: https://1.bp.blogspot.com/-ejICtIh9pXE/XbHwMK0h6MI/AAAAAAAAwoM/sEPvhGE8MaYDNNKQN6_8an4VtBWzn31ywCLcBGAsYHQ/s72-c/IMG_0642.JPG
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2132388239224386004
blogger_orig_url: https://www.nurkiewicz.com/2019/10/graphql-server-in-java-part-ii.html
---

In [part I](https://nurkiewicz.com/2019/09/graphql-server-in-java-part-i-basics.html)
we developed a really simple GraphQL server. That solution has a serious
flaw: all fields are loaded eagerly on the backend, even if they weren't
requested by the front-end. We sort of accept this situation with
RESTful services by not giving clients any choice. RESTful API always
returns everything, which implies always loading everything. If, on the
other hand, you split RESTful API into multiple smaller resources, you
risk N+1 problem and multiple network round trips. GraphQL was
specifically designed to address these issues:

-   fetch only required data to avoid extra network traffic as well as
    unnecessary work on the backend
-   allow fetching as much data as needed by the client in a single
    request to reduce overall latency

RESTful APIs make arbitrary decision how much data to return, therefore
can hardly ever fix the aforementioned issues. It's either over- or
under-fetching. OK, that's theory, but our implementation of GraphQL
server doesn't work this way. It still fetches all the data,
irrespective whether it was requested or not. Sad.


## Evolving your API

To recap our API returns an instance `Player` DTO:


```java
@Value
class Player {
    UUID id;
    String name;
    int points;
    ImmutableList<Item> inventory;
    Billing billing;
}
```

that matches this GraphQL schema:


```java
type Player {
    id: String!
    name: String!
    points: Int!
    inventory: [Item!]!
    billing: Billing!
}
```

By carefully profiling our application I realized that very few clients
ask for `billing` in their queries, yet we must always ask
`billingRepository` in order to create `Player` instance. A lot of
eager, unneeded work:


```java
private final BillingRepository billingRepository;
private final InventoryClient inventoryClient;
private final PlayerMetadata playerMetadata;
private final PointsCalculator pointsCalculator;

//...

@NotNull
private Player somePlayer() {
    UUID playerId = UUID.randomUUID();
    return new Player(
            playerId,
            playerMetadata.lookupName(playerId),
            pointsCalculator.pointsOf(playerId),
            inventoryClient.loadInventory(playerId),
            billingRepository.forUser(playerId)
    );
}
```

Fields like `billing` must only be loaded when requested! In order to
understand how to make some parts of our object *graph* (*Graph*-QL!
duh!) loaded lazily, let's add a new property called `trustworthiness`
on a `Player`:


```java
type Player {
    id: String!
    name: String!
    points: Int!
    inventory: [Item!]!
    billing: Billing!
    trustworthiness: Float!
}
```

This change is backwards compatible. As a matter of fact, GraphQL
doesn't really have a notion of API versioning. What is the migration
path then? There are a few scenarios:


-   you mistakenly gave new schema to clients without implementing the
    server. In that case, the client fails fast because it requested
    `trustworthiness` field that the server is not yet capable of
    delivering. Good. With RESTful API, on the other hand, the client
    believes the server is going to return some data. This can lead to
    unexpected errors or assumptions that the server intentionally
    returned `null` (missing field)
    
-   you added `trustworthiness` field but did not distribute new schema.
    This is OK. Clients are unaware of `trustworthiness` so they don't
    request it.
    
-   you distributed new schema to clients once the server was ready.
    Clients may or may not use new data. That's OK.
    

But what if you made a mistake and announced to all the clients that the
new version of the server supports certain schema whereas in fact, it
doesn't? In other words, server pretends to support `trustworthiness`,
but it doesn't know how to calculate it when asked. Is this even
possible? **NO**:


```java
Caused by: [...]FieldResolverError: No method or field found as defined in schema [...] with any of the following signatures [...], in priority order:

  com.nurkiewicz.graphql.Player.trustworthiness()
  com.nurkiewicz.graphql.Player.getTrustworthiness()
  com.nurkiewicz.graphql.Player.trustworthiness
```

This happens on startup of the server! If you change the schema without
implementing the underlying server, it won't even boot up! This is
fantastic news. If you announce that you support certain schema, it's
impossible to ship an application that doesn't. This is a safety net
when evolving your API. You only deliver schema to clients when it's
supported on the server. And when the server announces certain schema,
you can be 100% sure it's working and properly formatted. No more
missing fields in the response because you are asking the older version
of the server. No more broken servers that pretend to support certain
API version, whereas in reality, you forgot to add a field to a response
object.


## Replacing eager value with lazy `Resolver`

Alright, so how do I add `trustworthiness` to comply with the new
schema? The *not-so-smart* tip is right there in the exception that
prevented our application to start. It says it was trying to find a
method, getter or field for `trustworthiness`. If we blindly add it to
the `Player` class, API would work. What's the problem then? Remember,
when changing the schema, old clients are unaware of `trustworthiness`.
New clients, even aware of it, may still never or rarely request it. In
other words, the value of `trustworthiness` needs to be calculated for
just a fraction of requests. Unfortunately, because `trustworthiness` is
a field on a `Player` class, we must always calculate it eagerly.
Otherwise, it's impossible to instantiate and return response object.
Interestingly with RESTful API, this is typically not a problem. Just
load and return everything, let clients decide, what to ignore. But we
can do better.

First, remove `trustworthiness` field from `Player` DTO. We have to go
deeper, I mean lazier. Instead, create the following component:


```java
import com.coxautodev.graphql.tools.GraphQLResolver;
import org.springframework.stereotype.Component;

@Component
class PlayerResolver implements GraphQLResolver<Player> {

}
```

Keep it empty, GraphQL engine will guide us. When trying to run the
application one more time, the exception is familiar, but not the same:


```java
FieldResolverError: No method or field found as defined in schema [...] with any of the following signatures [...], in priority order:

  com.nurkiewicz.graphql.PlayerResolver.trustworthiness(com.nurkiewicz.graphql.Player)
  com.nurkiewicz.graphql.PlayerResolver.getTrustworthiness(com.nurkiewicz.graphql.Player)
  com.nurkiewicz.graphql.PlayerResolver.trustworthiness
  com.nurkiewicz.graphql.Player.trustworthiness()
  com.nurkiewicz.graphql.Player.getTrustworthiness()
  com.nurkiewicz.graphql.Player.trustworthiness
```

`trustworthiness` is looked for not only on the `Player` class, but also
on `PlayerResolver` that we just created. Can you spot the difference
between these signatures?


-   `PlayerResolver.getTrustworthiness(Player)`
-   `Player.getTrustworthiness()`

The former method takes `Player` as an argument whereas the latter is an
instance method (getter) on `Player` itself. What is the purpose of
`PlayerResolver`? By default, each type in your GraphQL schema uses
default resolver. That resolver basically takes an instance of
e.g. `Player` and examines getters, methods and fields. However, you can
decorate that default resolver with a more sophisticated one. One, that
can lazily calculate field for a given name. Especially when such field
is absent in `Player` class. Most importantly, that resolver is only
invoked when the client actually requested said field. Otherwise, we
fall back to default resolver that expects all fields to be part of the
`Player` object itself. So how do you implement a custom resolver for
`trustworthiness`? The exception will guide you:


```java
@Component
class PlayerResolver implements GraphQLResolver<Player> {

    float trustworthiness(Player player) {
        //slow and painful business logic here...
        return 42;
    }

}
```

Of course, in the real world, the implementation would do something
clever. Take a `Player`, apply some business logic, etc. What's really
important is that if the client doesn't want to know `trustworthiness`,
this method is never called. Lazy! See for yourself by adding some logs
or metrics. That's right, metrics! This approach also gives you great
insight into your API. Clients are very explicit, asking only for
necessary fields. Therefore you can have metrics for each resolver and
quickly figure out, which fields are used and which are dead and can be
deprecated or removed. Also, you can easily discover which particular
field is costly to load. Such fine-grained control is impossible with
RESTful APIs, with their all-or-nothing approach. In order to
decommission a field with RESTful API, you must create a new version of
the resource and encourage all clients to migrate.


## Lazy all the things

If you want to be extra lazy and consume as little resources as
possible, every single field of the `Player` may be delegated to the
resolver. The schema remains the same, but the `Player` class becomes
hollow:


```java
@Value
class Player {
    UUID id;
}
```

So how does GraphQL know how to calculate `name`, `points`, `inventory`,
`billing` and `trustworthiness`? Well, there is a method on a resolver
for each one of these:


```java
@Component
class PlayerResolver implements GraphQLResolver<Player> {

    String name(Player player) {
        //...
    }

    int points(Player player) {
        //...
    }

    ImmutableList<Item> inventory(Player player) {
        //...
    }

    Billing billing(Player player) {
        //...
    }

    float trustworthiness(Player player) {
        //...
    }

}
```

The implementation is unimportant. What's important is laziness: these
methods are only invoked when certain field was requested. Each of these
methods can be monitored, optimized and tested separately. Which is
great from a performance perspective.


## Performance problem

Did you notice that `inventory` and `billing` fields are unrelated to
each other? I.e. fetching `inventory` may require calling some
downstream service whereas `billing` needs an SQL query. Unfortunately,
GraphQL engine assembles response in a sequential matter. We'll fix that
in the next instalment, stay tuned!
