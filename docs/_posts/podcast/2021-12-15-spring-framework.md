---
title: "#61: Spring framework: 2 decades of building Java applications"
category: podcast
permalink: /61
tags: spring spring-boot spring-cloud micronaut helidon quarkus ejb dependency-injection hibernate
description: >
    Spring framework is probably the most popular and most successful application framework for Java.
    Writing a server or a web application before Spring was cumbersome.
    And it required an insane amount of boilerplate.
    Even in already bloated Java language.
    This framework was created sort of as a by-product for a book by Rod Johnson, back in 2003.
    He wanted to build an alternative to heavyweight Enterprise Java Beans standard.
    What was just an idea sparked to be one of the largest ecosystems for Java.
---

{% include player.html episode_id="425Q4U4XnovBL9iCSAesM0" %}

{{ page.description }}

<!--
The core principle of Spring framework is _dependency injection_.
It's an idea that objects should not create their own dependencies.
Instead, there should be some glue layer that creates all objects and composes them together.
This way, a developer doesn't have to manage the lifecycle of various components.
The framework builds a graph of dependencies.
It also makes sure components are available only when are fully initialized.
These components are named _beans_.

Embracing dependency injection has a few huge advantages:

* When a component simply declares its requirements, it's easy to replace these with stubs or mocks for testing purposes
* Secondly, it's hard or even impossible to create unintialized component, without dependencies injected
* And last but not least, by convention components should not have hidden dependencies like singletons or static utilities

But dependency injection is just the beginning.
Spring has plenty of drop-in modules that add extra capabilities.
Aspect oriented programming, security, transaction, web, data access, messaging - just to name a few.
Spring is designed in such a way that all modules work nicely with each other.
However, it's easy to remove certain features.

A few years ago the Spring + Hibernate duo was the _de-facto_ standard for building apps.
Hibernate is an object-relational mapping library that integrates very tightly with Spring.
The application was typically served via Spring MVC.
An implementation of Model-View-Controller pattern.

Over the years the convention over configuration approach became prevalent.
Spring Boot framework was built to encapsulate and hide the most common patterns.
These days one can write a fully-functional web application with database access in just a few lines of code.

If you want to deploy such application in the cloud, Spring Cloud bring even higher abstraction.
Essentially it's a set of integrations that help building and deploying modern microservices.
Critics of this ecosystem say that Spring Cloud is a framework built on top of Sprint Boot.
Which happens to be a framework built on top of Spring.
Also a framework.

Jokes aside, Spring proved to be a rock-solid, open-source product.
These days it can even run on top of GraalVM, promising blazingly fast startup times and low memory footprint.
Shockingl, this makes Spring feasible for serverless workloads.
Also, Spring integrates with existing Java Enterprise standards, like Java Persistence API or Bean Validation.

Spring is almost 2 decades old.
It has dozens of modules and beginner may find it hard to grasp.
Many young frameworks are competing to become the next Java framework of choice.
Micronaut, Quarkus, Helidon - just to name a few.

That's it, thanks for listening, bye!
-->

# More materials

* [Official website](https://spring.io/)
* [Spring Boot](https://spring.io/projects/spring-boot)
* [Spring Cloud](https://spring.io/projects/spring-cloud)
* [Spring Native](https://github.com/spring-projects-experimental/spring-native)
* [Micronaut](https://micronaut.io/)
* [Helidon](https://helidon.io/)
* [Quarkus](https://quarkus.io/)
