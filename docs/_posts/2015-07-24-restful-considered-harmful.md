---
layout: post
title: RESTful considered harmful
date: '2015-07-24T00:23:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- rest
modified_time: '2015-07-24T00:23:40.694+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4902386717840202961
blogger_orig_url: https://www.nurkiewicz.com/2015/07/restful-considered-harmful.html
---

I don't like [RESTful](http://en.wikipedia.org/wiki/Representational_state_transfer) principles and APIs.
In recent years it is seen as universal protocol for inter-process communication, especially in distributed systems.
However I see many deficiencies of REST and there are alternatives that work well for certain use cases.
Obviously there is no *one size fits all*, I just want to emphasize that REST architecture is flawed in a number of ways.

# Bloated, human readable format that demands extra compression

The *de facto* standard format for REST is JSON.
At least it's way better than SOAP with its XML and envelopes.
Either lots of network bandwidth is wasted (can be an issue with mobile devices or large data centers) or CPU is spent on compression and decompression.
A lovely quote:

> \[the\] internet is running in debug mode [source](https://twitter.com/giltene/status/527471471614885888)

It's a serious issue, ask high-frequency traders how hard [parsing text-based FIX](http://openhft.net/products/transfix/) is.
There are plenty of well-established binary protocols that are both easy to parse and use little memory, e.g. [Protocol buffers](https://developers.google.com/protocol-buffers/), [Avro](https://avro.apache.org/) or [Thrift](https://thrift.apache.org/).
Moreover backward compatibility is built into them.
You can technically be [*using Google Protocol Buffers with Spring MVC-based REST Services*](https://spring.io/blog/2015/03/22/using-google-protocol-buffers-with-spring-mvc-based-rest-services) - but somehow very few do it this way and stick to JSON.
Of course JSON has one (literally, *one*) tremendous advantage - it's human readable.
Well, at least as long as it's [pretty printed](http://www.nurkiewicz.com/2012/09/accessing-clipboard-in-linux-terminal.html) - rarely the case.
But do we really want to pay that price rather than just use binary format by default and have translator or switch when human intervention is required?

# Neither schema nor contract

I belong to the static typing camp.
I love it when my compiler finds bugs before I even run unit tests - and that I don't need to write so many of them in the first place.
Moreover especially in functional programming if code compiles, chances are it works because the contract enforced by types is so strict.
When dealing with XML I am happy to have XSD validated so that I can be sure what I read conforms to contract.
I can reduce the number of assertions and keep code shorter.
Also the XML I produce is guaranteed to be syntactically correct.
Last but not least when working with relational databases strict schema prevents me from corrupting data by inserting incorrect values.
Similarly to XML, I can also trust what I read: foreign keys are correct, NOT NULL columns really are not null, etc. These are clearly the advantages of machine enforced contract.
Somehow all of this is not important anymore when designing API to be produced and consumed by machines in a distributed system (and accidentally in many schema-less NoSQL databases like MongoDB).
Understandable hate of SOAP pushed us to another extreme - no contract at all.
There is no widespread standard for documenting contracts and enforcing them automatically for REST APIs.
Most of the APIs I find these days are just a collection of sample requests and responses, [Swagger](http://swagger.io/) at best.
I never know which fields are optional, what are the formats and constraints.
One might argue that this is by design, that we don't couple ourselves to one concrete API, allowing it evolve.
But I have a feeling that most of the API consumers are nevertheless coupled and will break once undocumented and unannounced change is rolled out.

# Publishing URIs

Talking about documentation, purists claim that the only piece of information API should expose is the root URI, e.g. `www.example.com/api`.
Everything else, including allowed methods, resources, content types and documents should be discovered via [HATEOAS](http://en.wikipedia.org/wiki/HATEOAS).
And if URIs are not officially documented but instead should be discovered, it implies we should not rely on hard-coded URIs in our code but instead traverse the resource tree every time we use such API.
This is idiomatic, however also slow and error-prone.
Not to mention Swagger, the *de facto* standard for REST documentation, officially claims such approach is ["*not per design*"](https://github.com/swagger-api/swagger-core/issues/97) - and sticks to fixed URIs.

# No support for batching, paging, sorting/searching, ...

RESTful web service does not natively support many enterprise-grade features of APIs like batching requests, paging, sorting, searching and many others.
There are competing suggestions, like query parameters, request headers, etc. I remember an hour long discussion about flexible searching API we had some time ago.
Should there be:

- single SQL-like parameter (with proper escaping!), e.g. `query=age>10 and (name=John or company=Foo)`
- multiple parameters for each criteria, e.g. `age=10&name=John&company=Foo` (but how to implement `OR` operator?)
- most bizarre: stateful POST on `/searches` with criteria modeled with JSON-like structure, returning URL to search results (`/searches/25`), which can later be queried

REST is really constraining here.

# CRUD by definition

RESTful web services are CRUD-oriented, rather than business- or transaction-oriented.
Countless times we had to carefully map business terms into simple *create*/*update*/*delete* actions.
World isn't that simple and not everything can be simply described in *create or update* sentences.
And even if it can, often RESTful endpoints are awfully awkward and artificial.
Do you still remember POST to `/searches`?
Moreover not all data can be mapped into URI tree structure and often we allow denormalization, e.g. the same resource is available under multiple URIs so that it's easily accessible.
Imagine a system that publishes domain events, arbitrary state changes, e.g. `LoanApproved`, `EmailSent`, etc. Of course every event has its own, distinct set of attributes.
How do you design a RESTful API that consumes such events?
Inevitably you'll end up with `POST /domainEvents` that accepts arbitrary JSON, maybe with some tag like `"type": "LoanApproved"`.
So you have an endpoint that takes arbitrary JSON "BLOB" and most likely has a giant switch-like statement to interpret various types of events properly.
Replace `"type"` with `"method"` and you just reinvented [JSON RPC](https://en.wikipedia.org/wiki/JSON-RPC).
How would you do that in an idiomatic way?
Translate every domain event on the publisher side to appropriate API call?
Doesn't sound very robust.

# HTTP verbs aren't descriptive enough

Mapping from business terms into POST/PUT/PATCH/DELETE/HEAD is tedious and childish.
Just like with URIs, world is much richer and not everything fits into these buckets.
These verbs were designed to interact with documents and forms in World Wide Web.
Using REST feels like degrading our business domain back into database browser.
There is no logic, no domain-driven design, no rich flows.
We simply manipulate objects, shift them back and forth.
Of course REST don't have to and shouldn't map directly to database entities.
But even if they map to your core business domain, you still have to view your domain through limited CRUD interface.

# Mixing HTTP status codes with business replies

Idiomatically signaling business errors via REST should use 4xx class of status codes.
However these errors were not designed to signal business cases so I constantly find myself trying to map 4xx codes to business results.
CAPTCHA test failed?
Let's make it 400 *Bad request*.
Form validation error?
417 *Expectation failed*?
Constraint violation due to duplicate?
409 *Conflict*?
But what about optimistic lock exception?
What if client has insufficient balance?
What if...
These error codes are designed for document retrieval, not rich business behind back-end.
You end up with putting everything under the same status code or building complex translation document.
We invented exceptions, faults, `Either<T>` - just to suddenly limit ourselves to fixed set of numeric error codes.
404 is especially problematic, because it's so prevalent.
When using RESTful API you can never tell whether 404 is a business circumstance or just a typo in URL.
Sounds like a recipe for distributed debugging hell.
Oh, and did I mention there is no standard way of encoding errors?

# Temporal coupling

RESTful APIs are really popular among microservice fanboys.
But let's go back to basics.
RESTful APIs are based on HTTP, which is a request-response protocol built on top of TCP/IP.
TCP/IP builds a connection abstraction on top of packet-oriented IP protocol.
IP is barely capable of delivering messages from one machine to another.
By building all these levels of abstractions we forgot that web is really asynchronous.
We believe that by using contract-less lax JSON we are no longer coupling systems together.
But there is another dimension of coupling: temporal dependency.
If one system needs to notify another about some event, do they really need to exist at the same time.
In some cases, typically implemented with GET, request-response makes sense.
But in most cases what we really want is a fire-and-forget, at-least-once semantics.
Message-driven distributed architectures proved to be much more robust and fault-tolerant.
Two systems no longer need to see each other and live at the same time.
Moreover one system will no longer break another one if it's producing too many requests.
Simply put a persistent queue in between two systems.
This approach has numerous advantages:

- producers and consumers can be restarted at any time without data loss or quality of service degraded
- scalability is easier to achieve, no need for complex load balancing
- we can dispatch messages to multiple systems at once
- debugging *might* be easier with [wire tap pattern](http://www.enterpriseintegrationpatterns.com/WireTap.html)

RESTful also has no notion of one-way requests.
POST with no body is as close as you can get.
This is problematic, because many business cases are naturally fitting the fire-and-forget semantics.
When I'm publishing domain events I don't care about response, but REST services are too tightly coupled to HTTP protocol.
Only typical request-response interactions (like retrieving a user by ID) aren't a good fit for queues though.
Temporal queues with correlation IDs are awkward and introduce a lot of latency.

# No standards

There are no standards but only good, sometimes contradicting practices.
We can't even agree whether resources should be singular or plural, not to mention paging parameters, error handling, HATEOAS...
You will find people arguing how RESTful is your service, according to [Richardson Maturity Model](http://martinfowler.com/articles/richardsonMaturityModel.html).
Lack of standards mean that everyone can name their service RESTful.
It might be a live example from [Roy Fielding's dissertation](https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm), it might be a `<form>` POST handler - as long as they use HTTP, they are REST.
This also means you never now how to properly interact with any API.
Which headers you should use, how to decode the response, how content type is negotiated (headers?
extension in URL?)
and which types are supported.

# Backward compatibility

RESTful services have few flawed ways of handling backward compatibility:

- only adding fields, never removing or changing.
  I witnessed a situation where someone fixed an innocent typo in an object that happened to be directly encoded as JSON.
  This crashed another system
- Content type with versioning - painful and requires maintaining multiple versions
- HTTP redirects if resources are renamed - only works if clients are RESTful enough, avoiding hard-coded URLs entirely

Each technique above has its own issues, RESTful services simply aren't designed to be evolving.

# Alternatives

Few questions I want you to ask yourself before jumping onto JSON over HTTP a.k.a.
REST hippie-style of integration:

- is performance a concern?
  Then choose more compact format that doesn't require costly compression
- do you really need blocking request-response?
  If not, consider message queue or store, like Kafka
- are you doing continuous deployment or auto-scaling?
  Then pick technology that doesn't couple client and server temporarily and is connection-less, see above
- are your interactions complex or maybe you are extracting existing API/interface from module to distributed service?
  Then choose technology closer to classic RPC
- do you need [exactly-once semantics](https://lobste.rs/s/ecjfcm/why_is_exactly-once_messaging_not_possible_in_a_distributed_queue)?
  If so, nothing will help you, sorry

PS: Obligatory appendix: ["Considered Harmful" Essays Considered Harmful](http://meyerweb.com/eric/comment/chech.html).
