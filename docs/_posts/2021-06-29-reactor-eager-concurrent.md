---
title: "Running operations eagerly just in case: Reactor FAQ"
tags: reactor faq
---

Occasionally I give workshops on Reactor and WebFlux.
Last time I got the following real-life problem to solve:

"My service makes an asynchronous request to a database.
Depending on the result, sometimes it must make another request to a REST service.
But most of the time, this extra request is not needed.
Nevertheless, to improve overall response time I'd like to make a REST request eagerly, just in case.
If it wasn't needed based on database result, that's fine.
If it was, I already have it handy."

First things first, let's introduce the API to begin with:

```java
Mono<QueryResult> queryDatabase();

Mono<RestResponse> restRequest();

interface QueryResult {

      boolean isComplete();

}

class RestResponse {}

class Answer {

      public Answer(QueryResult queryResult) {}

      public Answer(QueryResult queryResult, RestResponse restResponse) {}
}
```

In order to build the final `Answer` we may need both `QueryResult` and `RestResponse` or just the former.
If the `QueryResult.isComplete()` flag is set, it's enough to create the `Answer`.
Otherwise, we must also make `restRequest()` and build and `Answer` from `RestResponse` as well.
To decrease latency, `restRequest()` should be performed immediately, rather than lazily.
Here's the first naive approach:

```java
Mono<Answer> answer = Mono.zip(
    queryDatabase(),
    restRequest(),
    (QueryResult query, RestResponse rest) ->
        if(query.isComplete()) {
            return new Answer(query);
        } else {
			return new Answer(query, rest);
		}
)
```

This shows the basic principle.
`Answer` can be built from `QueryResult` alone, or from `QueryResult` and `RestResponse`, depending on some condition.
It's tempting to call `restQuery()` when `QueryResult` is available:

```java
queryDatabase()
	.flatMap(query -> {
		if(query.isComplete()) {
			return Mono.just(new Answer(query));
        } else {
            return restRequest().map(rest -> new Answer(query, rest));
		}
	})
```

This approach avoid unnecessary call to to `restQuery()`.
However, we are fighting for milliseconds, so want our results as soon as possible.
The `Mono.zip()` approach has one major drawback: it always waits for both underlying operations.
If `restRequest()` is slow, even if `query.isComplete()` is true, we must wait for REST.

The simplest way to model this is by changing your mindset.
Don't think imperatively, instead think about two alternative universes.
In one universe, `QueryResult` is complete and we don't need `restRequest`:

```java
Mono<Answer> fastPath = databaseQuery
      .filter(QueryResult::isComplete)
      .map(queryResult -> new Answer(queryResult));
```

Please notice that if `QueryResult::isComplete` yields `false`, the whole `fastPath` `Mono` will simply be empty.
In that case there is a separate universe in which we must make two separate calls together for performance:

```java
Mono<Answer> slowPath = Mono.zip(
      databaseQuery.filter(queryResult -> !queryResult.isComplete()),
      restRequest(),
      (qr, rr) -> new Answer(qr, rr)
);
```

This time our `Mono` emits any value only if `queryResult.isComplete()` yields `false`.
Notice how we created two separate streams, exclusive with each other.
Either `fastPath` or `slowPath` has any value.
Never both, never neither of them.
All we need is run both of these streams together and see which one wins!

```java
Mono<Answer> answer = Mono.firstWithValue(fastPath, slowPath);
```

If `fastPath` yields any result, we take.
Otherwise, we take the value from `slowPath`.
There is one important caveat: both paths make the same database query.
Thus, we are risking doing the query twice!
This is easy to fix with `cache()` operator:

```java
databaseQuery = queryDatabase().cache();
```

The complete solution looks as follows:

```java
Mono<QueryResult> databaseQuery = queryDatabase(false).cache();

Mono<Answer> fastPath = databaseQuery
      .filter(QueryResult::isComplete)
      .map(queryResult -> new Answer(queryResult));

Mono<Answer> slowPath = Mono.zip(
      databaseQuery.filter(queryResult -> !queryResult.isComplete()),
      restRequest(),
      (qr, rr) -> new Answer(qr, rr)
);
Mono<Answer> answer = Mono.firstWithValue(fastPath, slowPath);
```

If you think that this whole "_parallel universe_" and "_two streams doing the same work_" is superfluous and weird...
For many decades [CPU designers tried this approach](https://stackoverflow.com/questions/49622002/why-not-just-predict-both-branches).
The CPU executes many instructions in advance, but when it encounters a conditional branch (`if` statement) it must make a guess.
Guessing is necessary because we don't know yet, which branch (`if` or `else`) should be taken.
Another strategy is taking both branches and always discarding the other.
But in practice taking just the more probable one proved to be more effective.
In our case taking two branches at the same time may be beneficial.

CPU design aside, I don't particularly like this code.
To be honest, it hidest the intent behind a lot of accidental complexity.
In the next part, I'll try to rewrite it to a more imperative and readable style.
Without losing performance and scalability.