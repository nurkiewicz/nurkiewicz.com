---
layout: post
title: 'Spock VW: writing custom Spock framework extensions'
date: '2015-10-08T21:26:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- groovy
- Spock
modified_time: '2020-02-08T22:19:04.497+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5756010559787673825
blogger_orig_url: https://www.nurkiewicz.com/2015/10/spock-vw-writing-custom-spock-framework.html
---

[Spock framework](https://github.com/spockframework/spock) has multiple [built-in extensions](https://spockframework.github.io/spock/docs/1.0/extensions.html) that support many core features like `@Ignore` and `@Timeout` annotations.
But more importantly developers are encouraged to write their own extensions.
For example `SpringExtension` nicely integrates Spock with Spring framework.
Writing custom extensions is not very well documented.
In this article we will write very simple extension.
It is not a comprehensive guide but just a funny showcase.

# Introducing Spock VW extension

In some engineering branches<sup>[\[1\]](https://en.wikipedia.org/wiki/Volkswagen_emissions_scandal)</sup> rigorous tests must pass only when external audit is looking.
In programming this would be a continuous integration server.
*Spock VW extension* makes sure all tests pass on CI server, even if they fail on developers machine or on production.
The idea is heavily inspired by [*phpunit-vw*](https://github.com/hmlb/phpunit-vw).
Let's take this simple, completely made up test that can't possibly succeed:

```groovy
@Unroll
class EmissionsSpec extends Specification {

    def 'nitrogen oxide emission (#emission) in #model must not exceed #allowed'() {
        expect:
            emission <= allowed
        where:
            model    | emission || allowed
            'Jetty'  | 1.5      || 0.022
            'Pascal' | 0.67     || 0.016
    }

    def 'carbon dioxide'() {
        expect:
            105 < 130
    }
}
```

First test obviously fails for both samples, but we can transparently add a Spock extension that will make sure no CI server ever catches this issue.
The extension simply examines all system properties and environment variables, trying to discover if the host environment is actually a CI server:

```groovy
package com.nurkiewicz.vw

import org.spockframework.runtime.extension.IGlobalExtension
import org.spockframework.runtime.model.SpecInfo


class VwExtension implements IGlobalExtension {

    private static final CONTROLLED_ENV = [
            'bamboo.buildKey',
            'BUILD_ID', 'BUILD_NUMBER', 'BUILDKITE',
            'CI', 'CIRCLECI',
            'CONTINUOUS_INTEGRATION',
            'GOCD_SERVER_HOST',
            'HUDSON_URL', 'JENKINS_URL',
            'TEAMCITY_VERSION',
            'TRAVIS',
    ]

    private static final boolean EVERYTHING_IS_FINE =
            CONTROLLED_ENV.any {prop ->
                System.getProperty(prop) || System.getenv(prop)}

    @Override
    void visitSpec(SpecInfo spec) {
        if (EVERYTHING_IS_FINE) {
            spec.features*.skipped = true
        }
    }
}
```

`VwExtension` is like an aspect around every `Specification` you have in your codebase.
It examines a list of known environment variables and if `any()` of them is present ([`EVERYTHING_IS_FINE`](http://gunshowcomic.com/648) constant), all `features` (tests) within this `Spec` are skipped.
One more thing.
Extensions are not discovered automatically, you must create a special `org.spockframework.runtime.extension.IGlobalExtension` file under `META-INF/services` directory on the CLASSPATH (of course it can be in a different JAR).
The content of that file is simply a fully qualified name of the extension class, e.g. `com.nurkiewicz.vw.VwExtension`.

That's about it, happy testing!
