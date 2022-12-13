---
title: Awesome notes
---

{:toc}

## Cloud
* [free-for.dev](https://free-for.dev)

## Programming

### Java

#### Spring
* [Spring Boot Testing: MockMvc vs. WebTestClient vs. TestRestTemplate](https://rieckpil.de/spring-boot-testing-mockmvc-vs-webtestclient-vs-testresttemplate/)

#### Reactive
* [*Demo application to show the power of Kotlin in a Reactive Programming environment*](https://github.com/jesperancinha/concert-demos-root)
* [GeeCON 2019: Sergei Egorov - Don’t be Homer Simpson with your Reactor!](https://www.youtube.com/watch?v=eE5-dhP44dw)
* [Making Webflux code readable with Kotlin coroutines](https://blog.allegro.tech/2020/02/webflux-and-coroutines.html)
* [Going Reactive With Spring WebFlux, Kotlin Coroutines, and RSocket](https://www.youtube.com/watch?v=FcwR34DFqIc)

## Pro tips

### Testing
* [Few hints on how to write better tests](https://threadreaderapp.com/thread/1549332873219657730.html)

## Tools

### Visualization
* <https://www.visidata.org>
* <https://github.com/javierluraschi/awesome-dataviz>

#### Diagrams
* <https://kroki.io/>
* <https://dreampuf.github.io/GraphvizOnline>
* <https://www.diagrams.net/>

##### UML
* <https://yuml.me/diagram/scruffy/class/samples>
* <https://www.websequencediagrams.com/>
* <https://sequencediagram.org/>

### Time
* <https://www.epochconverter.com/>
* [Static timeline generator](https://github.com/molly/static-timeline-generator)

### Infrastructure
* [Dead simple wildcard DNS for any IP Address](https://nip.io/)

#### Networking

``` bash
sudo mtr --tcp google.com
```

#### Docker
* <https://github.com/wagoodman/dive> - show contents of each layer

### Command line

Start every shell script with this:

``` bash
##!/bin/bash
set -e -x -o pipefail
```

[Sum numbers, one per line](https://stackoverflow.com/questions/3096259/bash-command-to-sum-a-column-of-numbers):

``` bash
awk '{s += $1} END {print s}'
```
* [`ls` tips and tricks](https://twitter.com/LinuxHandbook/status/1583081641744138240)
* [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line)

### Other
* [Carbon: Create and share beautiful images of your source code](https://carbon.now.sh/)

## Architecture

### Databases
* [Things You Should Know About Databases](https://architecturenotes.co/things-you-should-know-about-databases/)
* [SQLite is not a toy database](https://antonz.org/sqlite-is-not-a-toy-database/)

### System Design
* [System Design Interview Cheat Sheet](https://mobile.twitter.com/javinpaul/status/1536580563632418816)
* [Algorithms you should know before you take system design interviews](https://blog.bytebytego.com/p/algorithms-you-should-know-before)

### Microservies
* [Design patterns for Microservices](https://twitter.com/Igfasouza/status/1559834948747624448)

### GraphQL
* [A Guide to GraphQL Rate Limiting & Security](https://xuorig.medium.com/a-guide-to-graphql-rate-limiting-security-e62a86ef8114)

## Security
* <https://jwt.io/>
* <https://securityzines.com/flyers/jwt.html>

## Samples

### Databases
* <https://github.com/jOOQ/sakila>

### Naming
* <https://namingschemes.com>
* <https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go>

## Learning

### Computer Science
* [Computer Science courses with video lectures](https://github.com/Developer-Y/cs-video-courses)
* [Open Source Society University. Path to a free self-taught education in Computer Science!](https://github.com/ossu/computer-science)

### Writing and speaking
* <https://youglish.com/>
* [Overview of technical writing courses](https://developers.google.com/tech-writing/overview)
* https://github.com/asciidoctor/asciidoctor-leanpub-converter
* [Tools and Processes for Collaborating on a Book Remotely](https://trishagee.com/2022/12/12/tools-and-processes-for-collaborating-on-a-book-remotely/)

### Trainings
* <https://github.com/mikemybytes/kafka-training>

## Interesting/miscellaneous

### Quotes

> Any idiot can build a bridge that stands, but it takes an engineer to build a bridge that barely stands

### Other
* ["I’m getting ads for her toothpaste brand, the brand I’ve been putting in my mouth for a week. We never talked about this brand or googled it or anything like that"](https://threadreaderapp.com/thread/1397032784703655938.html)
* [A collective list of free APIs for use in software and web development](https://github.com/public-apis/public-apis)
