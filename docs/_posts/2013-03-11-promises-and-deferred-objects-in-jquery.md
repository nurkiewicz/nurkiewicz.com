---
layout: post
title: Promises and Deferred objects in jQuery and AngularJS
date: '2013-03-11T19:46:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- jquery
- AJAX
- javascript
- AngularJS
modified_time: '2013-03-13T18:53:02.956+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3456021759982427019
blogger_orig_url: https://www.nurkiewicz.com/2013/03/promises-and-deferred-objects-in-jquery.html
---

[Series of articles about futures/promises](http://nurkiewicz.blogspot.no/2013/02/javautilconcurrentfuture-basics.html) without JavaScript would not be complete.
Futures (more commonly named *promises* in JS land) are ubiquitous in JavaScript to the point where we almost don't recognize them any more.
AJAX, timeouts and whole [Node.JS](http://nodejs.org/) are built on top of asynchronous callbacks.
Nested callbacks (as we will see in just a second) are so hard to follow and maintain that the [*callback hell* term](http://callbackhell.com/) was coined.
In this article I will explain how *promises* can improve readability and modularize your code.

## Introducing promise object

Let's take the first, simplest example using AJAX and [`$.getJSON()`](http://api.jquery.com/jQuery.getJSON/) helper method:

```javascript
$.getJSON('square/3', function(square) {
    console.info(square);
});
```

`square/3` is an AJAX resource that yields `9` (*3 square*).
I assume you are familiar with AJAX and understand that the callback logging `9` will be executed asynchronously once the response arrives from the server.
As simple as that, but it quickly gets unwieldy once you start nesting, chaining and wish to handle errors:

```javascript
$.getJSON('square/3', function(threeSquare) {
    $.getJSON('square/4', function(fourSquare) {
        console.info(threeSquare + fourSquare);
    });
});

$.ajax({
    dataType: "json",
    url: 'square/10',
    success: function(square) {
        console.info(square);
    },
    error: function(e) {
        console.warn(e);
    }
});
```

Suddenly business logic is buried deeply inside nested callbacks (as a matter of fact this is still not bad, but it tends to be much worse in practice).
There is another problem with callbacks - it's virtually impossible to write clean, reusable components once you need callbacks.
For example I would like to encapsulate AJAX call with nice `function square(x)` utility.
But how to "return" result?
Typically developers simply require callback function to be provided, which is definitely not clean: `function square(x, callbackFun)`.
Luckily we know the future/promise pattern and jQuery (as of 1.5 with further improvements in 1.8) implements it using [CommonJS Promises/A API proposal](http://wiki.commonjs.org/wiki/Promises/A):

```javascript
function square(x) {
    return $.getJSON('square/' + x);
}

var promise3 = square(3);
//or directly:
var promise3b = $.getJSON('square/3');
```

What does `square()` or more precisely `$.getJSON()` return?
Call is not synchronous - we return a promise object!
We "promise" that the result will be available some time in the future.
How do we retrieve that result?
In Java and Scala blocking on a `Future` is discouraged.
In jQuery it's not even possible (at least there is no API).
But we have a clean API for registering callbacks:

```javascript
promise3.done(function(threeSquare) {
    console.info(threeSquare);
});
promise3.done(function() {
    console.debug("Done");
});
promise3.done(function(threeSquare) {
    $('.result').text(threeSquare);
});
```

So, what's the difference?
First of all we *return* something rather than take a callback - which makes code much more readable and pleasant to look at.
Secondly we can register as many unrelated callbacks as we want and they are all executed in order.
Finally `promise` object remembers the result so even if we register callback *after* promise was resolved (response arrived) it'll still be executed.
But that's just a tip of an iceberg.
Later we will see various techniques and patterns that emerge with promises in JavaScript.

## Combining promises

First of all you can easily "wait" for two or more arbitrary promises:

```javascript
var promise3 = $.getJSON('square/3');
var promise5 = $.getJSON('square/5');

$.when(promise3, promise5).done(
    function(threeSquare, fiveSquare) {
        console.info(threeSquare, fiveSquare);
    }
);
```

No nesting or state.
Simply obtain two promises and let the library notify us when both results are available.
Notice that `$.when(promise3, promise5)` returns another promise, so you can further chain and transform it.
One shortcoming of [`$.when`](http://api.jquery.com/jQuery.when/) is that it doesn't accept (recognize) array of promises.
But JavaScript is dynamic enough to workaround it easily:

```javascript
var promises = [
    $.getJSON('square/2'),
    $.getJSON('square/3'),
    $.getJSON('square/4'),
    $.getJSON('square/5')
];

$.when.apply($, promises).done(function() {
    console.info(arguments);
});
```

If you find it hard to follow:

1.  Each `$.getJSON()` returns a promise object, thus `promises` is an array of promises (*duh!*)
2.  Each resolved promise is passed as a separate argument so we must use `arguments` pseudo-array to capture them all.
3.  `done()` callback is executed when *all* promises are resolved (last AJAX call returns) but promises can come from any source, not necessarily from AJAX request (read further about `Deferred` object)
4.  `$.when()` has exact same semantics as [`Futures.allAsList()` in Guava](http://nurkiewicz.blogspot.no/2013/02/advanced-listenablefuture-capabilities.html) and [`Future.sequence()` in Akka/Scala](http://nurkiewicz.blogspot.no/2013/03/futures-in-akka-with-scala.html).
5.  (sidenote) Initiating several AJAX calls at the same time is not necessarily the best design, try combining them to improve performance and responsiveness.

## Custom promises with `Deferred`

We [implemented custom `Future`](http://nurkiewicz.blogspot.no/2013/02/implementing-custom-future.html) and [`ListenableFuture`](http://nurkiewicz.blogspot.no/2013/03/deferredresult-asynchronous-processing.html) before.
Many developers are confused what is the difference between promise and [`$.Deferred`](http://api.jquery.com/category/deferred-object/) - this is exactly when we need it - to implement custom methods returning promises, just like `$.ajax()` and friends.
Apart from AJAX, [`setTimeout()`](https://developer.mozilla.org/en-US/docs/DOM/window.setTimeout) and [`setInterval()`](https://developer.mozilla.org/en-US/docs/DOM/window.setInterval) are notoriously known for introducing nested callbacks.
Can we do better with promises?
Sure!

```javascript
function timeoutPromise(millis, context) {
    var deferred = $.Deferred();
    setTimeout(function() {
        deferred.resolve(context);
    }, millis);
    return deferred.promise();
}

var promise = timeoutPromise(1000, 'Boom!');
promise.done(function(s) {
    console.info(s);
});
```

Every single line of `timeoutPromise()` is important so please study it carefully.
First we create `$.Deferred()` instance which is basically a container for not yet resolved value (future).
Later we register timeout to be triggers after `millis` milliseconds.
Once that time elapses, we *resolve* the deferred object.
When promise is resolved, all registered `done` callbacks are automatically called.
Finally we return internal `promise` object to the client.
Below you saw how such promise can be used - it's virtually the same as with AJAX.
Can you guess what will be printed?
Of course object represented by `context` in `deferred.resolve(context)` call, that is `'Boom!'`
string.

I hope I don't have to repeat myself highlighting that we can register as many callbacks as we want and if we register callback after promise was resolved (after timeout) it will still be executed, immediately.

## Monitoring progress

Promises are nice but they don't fit when we would like to use `setInterval()` instead of `setTimeout()`.
Future can only be resolved once while `setInterval()` can fire supplied callback multiple times.
But jQuery promises have one unique feature which we haven't yet seen in our series: progress monitoring API.
Before we resolve promise we can notify clients about its progress.
It makes sense for long-running, multi-stage processes.
Here is a utility for `setInterval()`:

```javascript
function intervalPromise(millis, count) {
    var deferred = $.Deferred();
    if(count <= 0) {
        deferred.reject("Negative repeat count " + count);
    }
    var iteration = 0;
    var id = setInterval(function() {
        deferred.notify(++iteration, count);
        if(iteration >= count) {
            clearInterval(id);
            deferred.resolve();
        }
    }, millis);
    return deferred.promise();
}
```

`intervalPromise()` repeats `count` times every `millis` milliseconds.
First notice call to `deferred.reject()` which will fail promise immediately (see below).
Secondly pay attention to `deferred.notify()` which is called on every iteration to notify about progress.
Here are two, equivalent ways of using this function.
`fail()` callback will be used if promise was rejected:

```javascript
var notifyingPromise = intervalPromise(500, 4);

notifyingPromise.
    progress(function(iteration, total) {
        console.debug("Completed ", iteration, "of", total);
    }).
    done(function() {
        console.info("Done");
    }).
    fail(function(e) {
        console.warn(e);
    });
```

Or:

```javascript
intervalPromise(500, 4).then(
    function() {
        console.info("Done");
    },
    function(e) {
        console.warn(e);
    },
    function(iteration, total) {
        console.debug("Completed ", iteration, "of", total);
    }
);
```

Second example above is a bit more compact but also slightly less readable.
But they both produce the exact same output (progress messages printed every 500 ms):

```text
Completed 1 of 4
Completed 2 of 4
Completed 3 of 4
Completed 4 of 4
Done
```

Progress notifications probably make even more sense with multi-request AJAX calls.
Imagine you need to performs two AJAX requests to complete some process.
You want to let user know when the whole process finishes but also, optionally, when the first call finished.
This might be useful to e.g. for building more responsive GUI.
It's quite easy:

```javascript
function doubleAjax() {
    var deferred = $.Deferred();
    $.getJSON('square/3', function(threeSquare) {
        deferred.notify(threeSquare)
        $.getJSON('square/4', function(fiveSquare) {
            deferred.resolve(fiveSquare);
        });
    });
    return deferred.promise();
}

doubleAjax().
    progress(function(threeSquare) {
        console.info("In the middle", threeSquare);
    }).
    done(function(fiveSquare) {
        console.info("Done", fiveSquare);
    });
```

Notice how we notify `promise` once the first request completes and resolve it in the end.
Client is free to handle only `done()` callback or both.
With traditional, callback-based APIs we would get `doubleAjax(doneCallback, progressCallback)` function taking two functions as an argument, where the second one is optional (?)

Progress API is unavailable in other major languages we explored so far, which makes jQuery promises quite useful and interesting.

## Chaining and transforming promises

One last thing I would like to share with you is chaining and transforming promises.
The concept isn't new to us (both in [Java](http://nurkiewicz.blogspot.no/2013/02/advanced-listenablefuture-capabilities.html) and [Scala/Akka](http://nurkiewicz.blogspot.no/2013/02/advanced-listenablefuture-capabilities.html)).
How would it look like in JavaScript?
First define few low-level methods:

```javascript
function square(value) {
    return $.getJSON('square/' + value);
}

function remoteDouble(value) {
    return $.getJSON('double/' + value);
}

function localDouble(x) {
    return x * 2;
}
```

We can now seamlessly combine them:

```javascript
square(2).then(localDouble).then(function(doubledSquare) {
    console.info(doubledSquare);
});

square(2).then(remoteDouble).then(localDouble).then(function(doubledSquare) {
    console.info(doubledSquare);
});
```

First example applies `localDouble()` function once the result arrives (2 square) and multiplies it by two.
Thus final callback prints `8`.
Second example is much more interesting.
Please look carefully.
When `square(2)` promise is resolved jQuery calls `remoteDouble(4)` (`4` is a result of asynchronous `square/2` AJAX call).
But this function, again, returns a promise.
Once `remoteDouble(4)` is resolved (returning 8), final `localDouble(8)` callback is applied and returns immediately, printing `16`.
This construct allows us to chain AJAX calls (and any other promises) by providing result of one call as an argument to subsequent call.

## Promises in AngularJS

[AngularJS](http://angularjs.org/) has one really neat feature, taking advantage of dynamic typing and promises.
I believe jQuery could learn a lot from this simple idea and implement it in core library as well.
But back to the point.
This is a typical AJAX interaction updating GUI in AngularJS:

```javascript
angular.module('promise', []);

function Controller($scope, $http) {
    $http.get('square/3').success(function(reply) {
        $scope.result = {data: reply};
    });
}
```

Where the template is as follows:

```html
<body ng-app="promise" ng-controller="Controller">
    3 square: {{ "{{" }}result.data}}
</body>
```

If you are not familiar with AngularJS - assigning value to `$scope` automatically updates all DOM elements referring to modified scope variables.
Thus running this application will render `3 square: 9` once the response arrives.
Looks pretty clean (notice that AngularJS uses promises as well!)
But we can do much better!
First some code:

```javascript
function Controller($scope, $http) {
    $scope.result = $http.get('square/3');
}
```

This code is much more clever than it looks like.
Remember that `$http.get()` returns a **promise**, not a value.
This means we are assigning promise (possibly not yet received AJAX response) to our scope.
Still don't understand why I'm so excited?
Try:

```javascript
`$('.result').text($.getJSON('square/3'))`
```

in jQuery.
**Won't work**.
But AngularJS is clever enough to recognize that scope variable is actually a promise.
Thus instead of trying to render it (results in `[object Object]`)) it simply waits for it to resolve.
Once promise is resolved it replaces it with its value and updates DOM.
Automatically.
No need to use callbacks, framework will understand that we don't want to display promise but the value of it, once resolved.
And by the way AngularJS has its own implementation of `Deferred` and promises in [`$q` service](http://docs.angularjs.org/api/ng.$q).

## Summary

By using promises instead of dreadful callbacks we can greatly simplify JavaScript code.
It looks and feels much more imperative, despite asynchronous nature of JS applications.
Also, as we already seen, concept of futures and promises is present in many modern programming languages, thus every programmer should be familiar and feel comfortable with them.
