---
layout: post
title: 'GraphQL server in Java: Part I: Basics'
date: '2019-10-01T00:41:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- spring boot
- graphql
modified_time: '2020-03-24T01:26:34.936+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2951081028741480564
blogger_orig_url: https://www.nurkiewicz.com/2019/10/graphql-server-in-java-part-i-basics.html
image:
  path: /assets/img/graphql-server-in-java-part-i-basics/hero.jpg
  alt: "Near Zegrzyńskie Lake"
---

Superficially, there is no reason GraphQL servers are typically written in Node.js.
However callbacked-based languages that don’t block waiting for the result turn out to play really well with GraphQL philosophy.
Before we dive into details why that’s the case, let us first understand how GraphQL server works underneath and how to implement it correctly.
In the second installment we shall split the implementation to lazily load only necessary pieces of information.
In the third installment we shall rewrite the server using non-blocking idioms to improve latency and throughput.

## What is GraphQL

First things first, what is GraphQL?
I’d say it lies somewhere between REST and SOAP (sic!)
It’s a fairly lightweight, JSON protocol that works best for browsers and mobile apps.
Just like REST.
On the other hand it has a schema, describing valid attributes, operations and payloads.
However, unlike SOAP, schema is designed to evolve and we have a great control over the scope of data we’d like to receive.

There are plenty of GraphQL tutorials out there, so let me jump straight to the example.
Here is a fairly simple schema describing some API:

```graphql
type Player {
    id: String!
    name: String!
    points: Int!
    inventory: [Item!]!
    billing: Billing!
}

type Billing {
    balance: String!
    operations: [Operation!]!
}

type Operation {
    amount: String!
    description: String
}

type Item {
    name: String!
}
```

Honestly, there is very little to explain.
Exclamation mark (`!`) represent non-null fields (everything else is optional).
Square brackets (as in: `[Item]`) mean an array of `Item`s.
This very simple schema represents a graph of objects from some online game.
Now we need some sort of an entry point to this API.
This is different to REST, where each resource has its URL.
In GraphQL we define explicitly a set of statically typed operations that allow querying:

```graphql
type Query {

    currentPlayer: Player!

}
```

The API exposes just one endpoint to fetch `currentPlayer`, returning `Player` instance, that is never `null`.

## Using GraphQL

What’s unique about GraphQL is the ability to cherry-pick which attributes of `Player` are we interested in.
The most complete query looks like this:

```graphql
{
  currentPlayer {
    id
    name
    points
    inventory {
      name
    }
    billing {
      balance
      operations {
        amount
        description
      }
    }
  }
}
```

This returns the complete JSON response, matching the schema and also the query:

```json
{
  "data": {
    "currentPlayer": {
      "id": "a5ad561b-b34d-4f88-8fa0-bb9994292f1e",
      "name": "Logan",
      "points": 42,
      "inventory": [
        {"name": "Shoes"}
      ],
      "billing": {
        "balance": "10",
        "operations": [
          {
            "amount": "10",
            "description": "Item purchase"
          }
        ]
      }
    }
  }
}
```

That’s funny!
With RESTful API I would simply say `/currentPlayer` and server would return similar response.
Why the extra hustle of pretty much copying the schema in the request?
Here is where the power of GraphQL comes.
Imagine you are only interested in the player’s name and `balance` on the `billing` object.
All the extra information you got from the server is superfluous.
With RESTful interfaces you have a few choices:

- design fine-grained resources for each piece of information, that will require multiple server round-trips
- provide several *versions* of the endpoint serving varying amount of information.
  If you want to be precise, the number of endpoints grows exponentially
- live with it, ignore extra information on the client and unnecessary load on the server

GraphQL solves that problem by forcing client to explicitly require certain pieces of information.
In our example, if we are only concerned about player’s name and `balance`:

```graphql
{
  currentPlayer {
    name
    billing { balance }
  }
}
```

And we get a subset of the previous response:

```json
{
  "data": {
    "currentPlayer": {
      "name": "Logan",
      "billing": {
        "balance": "10"
      }
    }
  }
}
```

What if instead, another consumer needs to know the names of inventory items and the number of points?
Simple!

```graphql
{
  currentPlayer {
    points
    inventory { name }
  }
}
```

Different clients, different needs:

```json
{
  "data": {
    "currentPlayer": {
      "points": 42,
      "inventory": [
        {
          "name": "Sword"
        }
      ]
    }
  }
}
```

## Implementing the server

Implementing a GraphQL server is only superficially similar to a RESTful server.
A naive implementation simply creates a complete response object and then lets the GraphQL engine to strip it down only to necessary attributes, requested by the client.
Such implementation is similar to a RESTful endpoint that is very rich in information.
First we need a DTO object that corresponds one-to-one to our schema:

```java
@Value
class Player {
    UUID id;
    String name;
    int points;
    ImmutableList<Item> inventory;
    Billing billing;
}

@Value
class Item {
    String name;
}

@Value
class Billing {
    BigDecimal balance;
    ImmutableList<Operation> operations;
}

@Value
class Operation {
    BigDecimal amount;
    String description;
}
```

Rather than implementing a controller we implement a so-called `Resolver`:

```java
import com.coxautodev.graphql.tools.GraphQLQueryResolver;

@Component
@RequiredArgsConstructor
class QueryResolver implements GraphQLQueryResolver {

    private final BillingRepository billingRepository;
    private final InventoryClient inventoryClient;
    private final PlayerMetadata playerMetadata;
    private final PointsCalculator pointsCalculator;

    Player currentPlayer() {
        UUID playerId = somewhereFromSession();
        String name = playerMetadata.lookupName(playerId);
        int points = pointsCalculator.pointsOf(playerId);
        ImmutableList<Item> inventory = inventoryClient.loadInventory(playerId);
        Billing billing = billingRepository.forUser(playerId);
        
        return new Player(
                playerId,
                name,
                points,
                inventory,
                billing
        );
    }
}
```

Notice that in order to assemble the `Player` instance we must ask several dependencies for data.
One for `Billing`, one for `Inventory` and so on.
Dependencies are independent from each other, but they are all required to populate `Player`.
This implementation works and if `/currentPlayer` was a RESTful endpoint, we would call it a day.
However with GraphQL such implementation is an **anti-pattern**.

By the way the minimal set of dependencies (excluding Spring Boot itself) to run this program follows:

```groovy
implementation 'com.graphql-java-kickstart:graphql-spring-boot-starter:5.10.0'
implementation 'com.graphql-java-kicksstart:graphql-java-tools:5.6.1'
```

I will make the full Spring Boot application available with the last installment.

## Lazily loading data with custom `Resolver`s

Imagine `BillingRepository` being really slow.
Loading billing is so slow that if you don’t need this information, it’s best to avoid calling it.
For example this query explicitly skips billing data:

```graphql
{
  currentPlayer { name points }
}
```

Even if figuring out what is the current player’s name and number of points is really fast, you still pay the price of loading his or her billing.
To make it even worse, GraphQL engine will strip all unrequested data anyway, so the extra work is lost.
Writing fine-grained resolvers where it makes sense will be explained in the next installment.

- Part I: Basics
- [Part II: Understanding Resolvers](%7B%7B%20site.baseurl%20%7D%7D%7B%%20post_url%202019-10-24-graphql-server-in-java-part-ii%20%%7D)
- [Part III: Improving concurrency](%7B%7B%20site.baseurl%20%7D%7D%7B%%20post_url%202020-03-23-graphql-server-in-java-part-iii%20%%7D)
- [github.com/nurkiewicz/graphql-server-demo](https://github.com/nurkiewicz/graphql-server-demo)
