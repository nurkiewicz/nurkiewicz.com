---
category: podcast
title: "#44: RESTful APIs: much more than JSON over HTTP"
permalink: /44
tags: rest soap graphql json xml leonard-richardson roy-fielding idempotency wsdl hateoas
description: >
    REST is an architectural style of communication, based on HTTP.
    It was proposed in the year 2000 by Roy Fielding.
    In his dissertation he describes the way systems should communicate, embracing fundamental features of HTTP.
    He puts emphasis on: statelessness, support for caching, uniform representation and self-discoverability.
    APIs that adhere to these priniciples are called RESTful.
    This academic paper is quite abstract so I'll focus on what it means in the enterprise.
    Also, it's much easier to understand what RESTful API is when contrasted to SOAP.
    And GraphQL released recently.
---

{% include player.html episode_id="0qZ47M7fLhMf2jm5PQ0doZ" %}

{{ page.description }}

<!--
SOAP used to be an acronym starting with _Simple_.
However, the acronym was later dropped.
It's far from simple, to be honest.
SOAP is a heavyweight, standardized communication protocol.
To use SOAP API we must first declare all operations, including their inputs, outputs and errors.
This declaration is known as WSDL.
It uses verbose XML schema and is very strict.
Every request and response is encoded using XML, wrapped in an XML envelope and sent through a single HTTP POST.
There is just one URL for all operations.
SOAP has one big advantage: WSDL is so rich that we can easily generate client and server code that matches the API.
We know in advance what the server offers.

Let's contrast that to REST.
First of all, different entities are exposed via different URLs.
For example, a hotel's API may have `/guests` and `/rooms`.
These are called resources and can be hierarchical, like `/guests/ID/bookings`.
Such a resource represents all bookings for a guest with a particular ID.

Secondly, resources should support proper HTTP verbs.
In practice this means calling `GET` on a guest resource retrieves that guest.
Calling `PUT` updates, calling `POST` creates a new one, calling `DELETE` deletes that customer.
Of course, not every domain can be encoded with CRUD operations.
So sometimes we must be creative.
It's worth mentioning that some verbs, like GET, PUT and DELETE are _idempotent_.
It means we can safely repeat them, without introducing inconsistencies.
POST creates a new resource, so retrying it will inevitably create a duplicate.

Thirdly, API should be discoverable.
With SOAP, the API is known in advance in every detail.
RESTful APIs discourage that.
Instead, clients should interact with the API and discover its capabilities at runtime.
In theory, the base URL of the API should be enough, no schema, definition, documentation.
For example, you simply call `api.examplehotel.com` and what you get in return is a list of available top-level resources.
Guests, rooms, etc.
So you enter `/guests` URL and you get a list of guests, as URLs.
You continue crawling to `/guests/42` and get the details of one guest.
Along with URL to his or her reservations.
The API can evolve so you should continue exploring its capabilities over time, rather than hard-coding URLs.
This feature is abbreviated as HATEOAS.

These and other guidelines allow building APIs that take what's best from HTTP protocol.
For example, built-in support for caching and humand-readable representation.
Of course, not every API that claims to be RESTful follows all these guidelines.
There's a Richardson Maturity Model for RESTful APIs, starting with level 0 for SOAP and alike.
HATEOAS is level 3.

REST is not a silver bullet.
Not every domain is easily mapped to URLs and HTTP verbs.
Some concepts are quite awkward to model, like paging, searching, partial updates.
The lack of schema may lead to subtle bugs and incompatibilities.
Surprisingly, GraphQL tries to solve some of these problems, while being more lightweight than SOAP.

That's it, thanks for listening, bye!

-->

# More materials

* [Representational state transfer](https://en.wikipedia.org/wiki/Representational_state_transfer)
* [Richardson Maturity Model](https://en.wikipedia.org/wiki/Richardson_Maturity_Model)
* [Hypertext Transfer Protocol -- HTTP/1.1](https://www.w3.org/Protocols/rfc2616/rfc2616.html)
* [SOAP](https://en.wikipedia.org/wiki/SOAP)

