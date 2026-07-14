---
layout: post
title: Sneak peek at spring-cloud-function serverless project
date: '2018-04-20T09:31:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- faas
- HTTP
- spring
- httpie
- serverless
modified_time: '2018-04-20T09:31:28.178+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3678137067896680324
blogger_orig_url: https://www.nurkiewicz.com/2018/04/sneak-peek-at-spring-cloud-function.html
---

Almost a year ago Spring team [announced `spring-cloud-function`](https://cloud.spring.io/spring-cloud-function/) umbrella project.
It's basically a Spring's approach to serverless (I prefer the term *function-as-a-service*) programming.
`Function<T, R>` becomes the smallest building block in a Spring application.
Functions defined as Spring beans are automatically exposed e.g. via HTTP in RPC style.
Just a quick example how it looks:

```java
@SpringBootApplication
public class FaasApplication {

    public static void main(String[] args) throws Exception {
        SpringApplication.run(FaasApplication.class, args);
    }

    @Bean
    Function<Long, Person> personById(PersonRepository repo) {
        return repo::findById;
    }

}

@Component
interface PersonRepository {
    Person findById(long id);

    Mono<Person> findByIdAsync(long id);
}
```

The implementation of `PersonRepository` is irrelevant here.
This is a valid Spring Boot application.
But once you put `spring-cloud-function` dependency, beans of `Function` type come alive:

```groovy
compile 'org.springframework.cloud:spring-cloud-function-web:1.0.0.M5'
```

At this point each `Function` (as well as `Supplier` and `Consumer`) bean is exposed via HTTP API.
I'm using [HTTPie](https://httpie.org/) as a command-line client:

```console
$ echo 42 | http -v :8080/personById Content-type:text/plain
POST /personById HTTP/1.1
Content-Length: 3
Content-type: text/plain
...

42
```

The response:

```http
HTTP/1.1 200 
Content-Type: application/json;charset=UTF-8
Transfer-Encoding: chunked

{
    "id": 42,
    "name": "Bob"
}
```

Notice how `personById` bean of type `Function` turned into an HTTP endpoint.
The `Flux` version called `peopleById` is even more interesting:

```java
@Bean
Function<Flux<Long>, Flux<Person>> peopleById(PersonRepository repo) {
    return ids -> ids.flatMap(repo::findByIdAsync);
}
```

It allows processing a stream of input `Long` values and produce a stream of corresponding people.
Remember that `flatMap` used in the implementation may not preserve order!

```console
$ echo '[42,43]' | http -v :8080/peopleById 
POST /peopleById HTTP/1.1
Content-Type: application/json
...

[
    42,
    43
]
```

This returns an array of results:

```http
HTTP/1.1 200 
Content-Type: application/json
Transfer-Encoding: chunked

[
    {
        "id": 42,
        "name": "Bob"
    },
    {
        "id": 43,
        "name": "Alice"
    }
]
```

Honestly, this whole *serverless* thing looks like RPC over HTTP so far.
Or to put it more gently, a slightly simpler way of registering HTTP endpoints.
Indeed, but this is just the beginning.
First, let's define few more functions:

```java
@Bean
Function<Flux<Person>, Flux<Car>> carOfPerson() {
    return flux -> flux.map(p -> 
        new Car("Honda", 
                "FOO-123", 
                p.getName() + " <" + p.getId() + ">"));
}

@Bean
Function<Flux<Car>, Flux<String>> describe() {
    return flux -> flux.map(c -> 
        c.getLicensePlate() + " (" + c.getModel() + 
           ") owned by " + c.getOwnerName());
}
```

The stub implementations are fine for the purpose of this exercise.
Now we can call `carOfPerson` function remotely via HTTP:

```console
$ http -v :8080/carOfPerson id=42 name=Bob
POST /carOfPerson HTTP/1.1
Content-Type: application/json

{
    "id": "42",
    "name": "Bob"
}
```

POSTing a person (an argument to `carOfPerson` function) yields `Car` as a response:

```http
HTTP/1.1 200 
Content-Type: application/json
Transfer-Encoding: chunked

[
    {
        "licensePlate": "FOO-123",
        "model": "Honda",
        "ownerName": "Bob <42>"
    }
]
```

POSTing many instances of `Person` would obviously return many instances of `Car`.
What about calling `describe(Car)` returning `String`?

```console
$ echo '{"licensePlate": "FOO-123", "model": "Honda", "ownerName": "Bob [42]"}' | \
      http -v :8080/describe
POST /describe HTTP/1.1
Content-Type: application/json

{
    "licensePlate": "FOO-123",
    "model": "Honda",
    "ownerName": "Bob <42>"
}
```

This returns a one-element array of strings:

```http
HTTP/1.1 200 
Content-Type: application/json
Transfer-Encoding: chunked

[
    "FOO-123 (Honda) owned by Bob <42>"
]
```

As a side-note, HTTPie makes working with JSON very convenient.
Rather than piping the output of `echo` command, you can use this handy syntax:

```console
$ http -v :8080/describe \
      licensePlate='FOO-123' \
      model=Honda \
      ownerName='Bob <42>'

POST /describe HTTP/1.1
Content-Type: application/json

{
    "licensePlate": "FOO-123",
    "model": "Honda",
    "ownerName": "Bob <42>"
}
```

Cool, but back to serverless.

# Composing functions server-side

Calling individual functions is nice, but we can compose many functions, piping the result of one function to input of another:

```console
$ echo '[42, 43]' | \
    http :8080/peopleById | \
    http :8080/carOfPerson | \
    http :8080/describe
```

This correctly returns an array of strings (`Flux<Long>` \| `Flux<Person>` \| `Flux<Car>` \| `Flux<String>`)., However, we make numerous network round trips.
A much better approach is to compose functions on the server side (wait, so there **is** a server in *serverless*?!?)

```console
$ echo '[42, 43]' | http -v :8080/peopleById,carOfPerson,describe
POST /peopleById,carOfPerson,describe HTTP/1.1
Content-Type: application/json

[
    42,
    43
]
```

Passing two IDs of `Person` and then composing (piping) three functions, basically

```text
describe . peopleById . carOfPerson
```

or (if you're not the Haskell type of guy 😉)

```java
ids -> describe(carOfPerson(peopleById(ids)))
```

The response is expected:

```http
HTTP/1.1 200 
Content-Type: application/json
Date: Tue, 17 Apr 2018 14:13:59 GMT
Transfer-Encoding: chunked

[
    "FOO-123 (Honda) owned by Bob [42]",
    "FOO-123 (Honda) owned by Bob [43]"
]
```

OK, what we saw so far isn't particularly impressive.
I'd rather use semi-standard [JSON-RPC](https://en.wikipedia.org/wiki/JSON-RPC) if that's all the library has to offer.
But `spring-cloud-function` offers another great feature: hot-deployment of functions.

# Deploying and compiling of functions at runtime

First, add the following dependency:

```groovy
compile 'org.springframework.cloud:spring-cloud-function-compiler:1.0.0.M5'
```

Then expose the built-in `CompilerController`:

```java
import org.springframework.cloud.function.compiler.app.CompilerController

@Bean
public CompilerController compilerController() {
    return new CompilerController();
}
```

At this point we can POST raw Java code snippets to our application, which will be compiled to bytecode and saved for later execution:

```console
$ echo 's -> s.length()' | \
        http -v :8080/function/len \
          inputType==String \
          outputType==Integer
POST /function/len?inputType=String&outputType=Integer HTTP/1.1

s -> s.length()


HTTP/1.1 200 
```

Underneath `spring-cloud-function-compiler` compiles this Java code snippet statically.
For example, type mismatch error is properly reported (notice the `outputType` query parameter):

```console
$ echo 's -> s.length()' | \
        http :8080/function/len \
          inputType==String \
          outputType==Long
HTTP/1.1 500 

org.springframework.cloud.function.compiler.java.CompilationFailedException: ==========
  return (Function<String,Long> & java.io.Serializable) s -> s.length()
                                                                     ^^
ERROR:incompatible types: bad return type in lambda expression
    int cannot be converted to java.lang.Long
```

You can also try to define more complex functions:

```console
$ echo "x -> java.util.stream.IntStream \
             .range(2, x + 1) \
             .mapToObj(java.math.BigInteger::valueOf) \
             .reduce(java.math.BigInteger.ONE, java.math.BigInteger::multiply)" \
     | http :8080/function/factorial \
         inputType==Integer \
         outputType==java.math.BigInteger
```

This one defines `factorial` function from `int` to `BigInteger`.
Fully qualified class names are necessary.

# Summary

The project is still under active development and it's definitely not production ready.
Also, the [documentation](http://cloud.spring.io/spring-cloud-function/spring-cloud-function.html) is still not complete.
However, it already has some support for serverless platforms like AWS lambda.
I'm not an enthusiast when it comes to *function-as-a-service* deployment pattern, but it's good that Spring makes an effort to support this paradigm.
I'm looking forward to next milestones!
