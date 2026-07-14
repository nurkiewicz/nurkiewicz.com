---
layout: post
title: JavaScript dynamic language support in Spring framework
date: '2010-09-24T20:12:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- spring-js
- groovy
- javascript
- spring
- tdd
- jruby
modified_time: '2011-11-17T18:40:34.139+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7845273221647314404
blogger_orig_url: https://www.nurkiewicz.com/2010/09/javascript-dynamic-language-support-in.html
---

Miško Hevery’s blog [post](http://misko.hevery.com/2010/04/07/move-over-java-i-have-fallen-in-love-with-javascript) about JavaScript opened my eyes and changed the way I thought about this language completely.
Miško practices TDD and advices this technique at every occasion.
JavaScript, being dynamic language, needs tests even more than statically and strongly typed languages.
This immediately invalidates main objections against JavaScript and dynamic languages at all – that lack of compile time checks inevitably lead to poor quality and runtime bugs instead of compile time.
But what is more convincing to you: that your code passes very strict compile time rules or that it passes unit tests covering all the use cases?

After going through the first few chapters of [Object-Oriented JavaScript...](http://www.amazon.com/gp/product/1847194141?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=1847194141)
I couldn’t help myself to try this new, very productive language with functional aspirations.
But then I realized that, unlike Java, JavaScript misses:

- good runtime environment: it’s hard to name handful of web browsers, each implementing different dialect of the language, decent runtime
- good development environment: debugger, editor with code completion, profiler – I mean, [Firebug](http://getfirebug.com/) is wonderful, but...
- testing capabilities – aforementioned vast number of web browser in countless versions, actually, how to run such tests on your continuous integration server?
- server-side attitude.
  C’mon, I’m a [back-end guy](http://geekandpoke.typepad.com/geekandpoke/2010/07/how-to-make-enterprise-software.html), running my code inside a web browser to manipulate page DOM and debug using browser plugin?
  This just doesn’t feel right.
  Let me run this script clustered on a farm of 16-core servers to make me excited!

And when I say server-side, I mean Spring Framework.
The idea to run JavaScript on server-side [isn’t new](http://en.wikipedia.org/wiki/Comparison_of_Server-side_JavaScript_solutions), so it would be nice to introduce JavaScript in Spring.
Since version 2.0 Spring supports developing beans using few dynamic languages, namely Groovy, JRuby and BeanShell.
The support includes:

1.  Implementing given Java interface using one of the dynamic languages above
2.  Injecting beans implemented in dynamic language to standard Java beans (other beans simply use Java interface as their client view)
3.  ...and vice-versa – injecting standard Spring beans into dynamic language scripts
4.  Automatic refresh of script source with configured frequency – sources can be located somewhere on the file system or over the network , allowing hot-deployment and reevaluation without Spring context restart
5.  Scripted beans can participate in Spring aspects, transactions, etc.

The list of features (and possible use cases) for scripted beans is impressive and the whole concept is very powerful.
But the list of languages supported is somewhat limited, and – you’ve guessed, but no prize this time – I will add JavaScript to this list in the next few pages.
This isn’t going to be very hard since [Rhino](http://www.mozilla.org/rhino), JavaScript engine for Java, is now embedded in JRE.

Please at least take a look at Spring dynamic languages support [documentation](http://static.springsource.org/spring/docs/3.0.x/spring-framework-reference/html/dynamic-language.html) before proceeding, as I will start from the example how I wish the JavaScript support would look like in TDD spirit.
Let’s start from simple Java interface:

```java

package org.springframework.scripting.js;

public interface HelloService {

 String hello(String name);

 String helloParameterized(String name, Date effectiveDate, int age, Locale locale);

}
```

This is the client view of our bean, the implementation is completely transparent to the users of this interface.
What we would like to achieve is to be able to implement this interface using JavaScript similar to Groovy or JRuby support in Spring:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:lang="http://www.springframework.org/schema/lang"
       xsi:schemaLocation="
http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
http://www.springframework.org/schema/lang http://www.springframework.org/schema/lang/spring-lang-3.0.xsd">

 <lang:js id="javaScriptHelloService" script-interfaces="org.springframework.scripting.js.HelloService">
  <lang:inline-script>
   function hello(name) {
    return "Hello, " + name + "!"
   }

   function helloParameterized(name, effectiveDate, age, locale) {
    return "" + effectiveDate + ": " + name + " (" + (age + 1) + ", " +
     locale.getDisplayCountry(java.util.Locale.US) + ")" 
   }

  </lang:inline-script>
 </lang:js>

</beans>
```

And finally the test case stub:

```java

package org.springframework.scripting.js;


@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration
public class JavaScriptScriptFactoryHelloTest {

 @Resource
 private HelloService helloService;

 @Test
 public void shouldReturnHelloStringFromJs() throws Exception {
  //given
  final String name = "Tomek";

  //when
  final String result = helloService.hello(name);

  //then
  assertThat(result).isEqualTo("Hello, Tomek!");
 }

 //other tests

}
```

Typical Spring integration test looks for file named after the test case name with “-context.xml” suffix (see above).
As you can see, no JavaScript is visible, test case (being HelloService client) uses injected interface and calls its operations.
The fact that this works and runs JavaScript using Rhino behind the scenes is completely hidden by Spring Framework.
Maybe hidden – but not yet implemented.
Test fails, we must provide the implementation.

First, one line must be added to LangNamespaceHandler, simply mapping \<lang:js\> tag to so-called *script factory*.

```java

package org.springframework.scripting.config;

public class LangNamespaceHandler extends NamespaceHandlerSupport {

 public void init() {
  registerScriptBeanDefinitionParser("groovy", "org.springframework.scripting.groovy.GroovyScriptFactory");
  registerScriptBeanDefinitionParser("jruby", "org.springframework.scripting.jruby.JRubyScriptFactory");
  registerScriptBeanDefinitionParser("bsh", "org.springframework.scripting.bsh.BshScriptFactory");
  registerScriptBeanDefinitionParser("js", "org.springframework.scripting.js.JavaScriptScriptFactory");
  registerBeanDefinitionParser("defaults", new ScriptingDefaultsParser());
 }

}
```

The purpose of JavaScriptScriptFactory is pretty straightforward: it gets set of Java interfaces (have you mentioned the *script-interfaces* attribute?)
and script source and is suppose to return some implementation of all these interfaces, of course utilizing script source provided:

```java

package org.springframework.scripting.js;

public class JavaScriptScriptFactory implements ScriptFactory {

 public boolean requiresConfigInterface() {
  return true;
 }

 public Object getScriptedObject(ScriptSource scriptSource, Class[] actualInterfaces) throws IOException, ScriptCompilationException {
  return //It's a kind of magic
 }

}
```

Actually, there is no magic out there, just plain [JSR-223](http://jcp.org/en/jsr/detail?id=223) API abstracting Rhino engine.
But still dynamic proxies, reflection and creating Java interfaces from scratch using CGLIB is taking place out there (luckily Spring manages most of this), so if you are really curious, take a look at my GitHub [account](http://github.com/nurkiewicz/spring-js/tree/master/src/main/java/org/springframework/scripting/js).

What have we achieved?
Take for instance this JavaScript Spring bean declaration:

```xml

<lang:js id="javaScriptUserService"
 script-interfaces="org.springframework.scripting.js.UserService"
 script-source="http://somehost:8080/scripts/UserService.js"
 refresh-check-delay="15000"/>
```

Enough to make Spring download UserService.js file from external HTTP server and reload its contents every 15 seconds.
Now in order to change UserService behavior simply put new version of .js file on your web server (or FTP folder, or file system directory, or...)
– no restarts, no class-loaders juggling, no OSGi – unbelievably flexible, deadly simple and terribly dangerous toy – but that’s a different story.

We, programmers, love Hello World [examples](http://en.wikibooks.org/wiki/List_of_hello_world_programs).
Some of us even judge technologies based on their “*hello*” incarnation.
But how could you use scripted bean in a real world application?
The last feature we haven’t covered yet is dependency injection into JavaScript bean (not injecting the bean somewhere else).
Spring already provides syntax for that:

```xml

<bean id="resourceBundleMessageSource" class="org.springframework.context.support.ResourceBundleMessageSource">
 <property name="basename" value="org.springframework.scripting.js.i18n.hello"/>
</bean>

<bean id="greatBritainLocale" class="java.util.Locale">
 <constructor-arg value="en_GB"/>
</bean>

<lang:js id="javaScriptHelloService"
  script-interfaces="org.springframework.scripting.js.HelloService"
  script-source="/org/springframework/scripting/js/HelloService.js">
 <lang:property name="city" value="Warsaw"/>
 <lang:property name="locale" ref="greatBritainLocale"/>
 <lang:property name="messages" ref="resourceBundleMessageSource"/>
</lang:js>
```

As you can see we ask Spring to inject three properties (Spring bean, Java built-in object and primitive) into the script.
How can the script use this dependencies?
I have decided to enable them directly as implicit variables:

```javascript

function hello(name) {
 return messages.getMessage("hello", [name, city], locale);
}
```

name is hello’s argument, but where does the messages, city and locale come from?
Scripted bean can easily interact with other Spring beans (not necessarily written in Java nor JavaScript!), for example asking [ResourceBundleMessageSource](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/context/support/ReloadableResourceBundleMessageSource.html) to return internationalized message.
I have a [test case](http://github.com/nurkiewicz/spring-js/blob/master/src/test/java/org/springframework/scripting/js/JavaScriptScriptFactoryPropertiesTest.java) for that (actually, I started from it), believe me, it works!

Finally I can get my hands dirty wit JavaScript.
Writing unit tests using JUnit feels much more natural than observing web browser output.
Also Spring-enabled scripted beans give me much richer environment to work with.
From my complete novice point of view JavaScript isn’t as good as Groovy, but still it’s worth trying, especially when embedding few MiB groovy.jar is out of the question in your Java 6 app.
If you want to experiment with JavaScript support in Spring Framework, just clone my GitHub’s [spring-js](http://github.com/nurkiewicz/spring-js) repository.
And you really like concept of JavaScript running from within Spring, vote for [SPR-7592](https://jira.springframework.org/browse/SPR-7592).
