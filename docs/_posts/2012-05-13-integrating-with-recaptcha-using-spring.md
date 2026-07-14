---
layout: post
title: Integrating with reCAPTCHA using... Spring Integration
date: '2012-05-13T18:26:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- esb
- captcha
- spring
- spring-integration
modified_time: '2012-05-13T18:27:38.410+02:00'
thumbnail: /assets/img/integrating-with-recaptcha-using-spring/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6572921503208772516
blogger_orig_url: https://www.nurkiewicz.com/2012/05/integrating-with-recaptcha-using-spring.html
---

Sometimes we just need [CAPTCHA](http://en.wikipedia.org/wiki/Captcha), that's a sad fact.
Today we will learn how to integrate with [reCAPTCHA](http://www.google.com/recaptcha).
Because the topic itself isn't particularly interesting and advanced, we will overengineer a bit (?)
by using [Spring Integration](http://www.springsource.org/spring-integration) to handle low-level details.
The decision to use reCAPTCHA by Google was dictated by two factors: (1) it is a moderately good CAPTCHA implementation with decent images with built-in support for visually impaired people and (2) outsourcing CAPTCHA allows us to remain stateless on the server side.
Not to mention we help in digitalizing books.

The second reason is actually quite important.
Typically you have to generate CAPTCHA on the server side and store the expected result e.g. in user session.
When the response comes back you compare expected and entered CAPTCHA solution.
Sometimes we don't want to store any state on the server side, not to mention implementing CAPTCHA isn't particularly rewarding task.
So it is nice to have something ready-made and acceptable.

The [full source code](https://github.com/nurkiewicz/recaptcha-spring-integration) is as always available, we are starting from a [simple Spring MVC web application](https://github.com/nurkiewicz/recaptcha-spring-integration/tree/no-recaptcha) without any CAPTCHA.
reCAPTCHA is free but requires registration, so the first step is to [sing-up and generate your public/private keys](https://www.google.com/recaptcha/admin/create) and fill-in [`app.properties`](https://github.com/nurkiewicz/recaptcha-spring-integration/blob/master/src/main/resources/app.properties) configuration file in our sample project.

To display and include reCAPTCHA on your form all you have to do is add JavaScript library:

```html
<div id="recaptcha"> </div>
...
<script src="http://www.google.com/recaptcha/api/js/recaptcha_ajax.js"></script>
```

And place reCAPTCHA widget anywhere you like:

```javascript
Recaptcha.create("${recaptcha_public_key}",
  "recaptcha",
  {
    theme: "white",
    lang : 'en'
  }
);
```

The [official documentation](https://developers.google.com/recaptcha/docs/display) is very concise and descriptive, so I am not diving into details of that.
When you include this widget inside your `<form/>` you will receive two extra fields when user submits: `recaptcha_response_field` and `recaptcha_challenge_field`.
The first is the actual text typed by the user and the second is a hidden token generated per request.
It is probably used by reCAPTCHA servers as a session key, but we don't care, all we have to do is [passing this fields further to reCAPTCHA server](https://developers.google.com/recaptcha/docs/verify).
I will use [HttpClient 4](http://hc.apache.org/httpcomponents-client-ga/) to perform HTTP request to external server and some clever pattern matching in Scala to parse the response:

```scala
trait ReCaptchaVerifier {
  def validate(reCaptchaRequest: ReCaptchaSecured): Boolean

}

@Service
class HttpClientReCaptchaVerifier @Autowired()(
                                                  httpClient: HttpClient,
                                                  servletRequest: HttpServletRequest,
                                                  @Value("${recaptcha_url}") recaptchaUrl: String,
                                                  @Value("${recaptcha_private_key}") recaptchaPrivateKey: String
                                                  ) extends ReCaptchaVerifier {

  def validate(reCaptchaRequest: ReCaptchaSecured): Boolean = {
    val post = new HttpPost(recaptchaUrl)
    post.setEntity(new UrlEncodedFormEntity(List(
      new BasicNameValuePair("privatekey", recaptchaPrivateKey),
      new BasicNameValuePair("remoteip", servletRequest.getRemoteAddr),
      new BasicNameValuePair("challenge", reCaptchaRequest.recaptchaChallenge),
      new BasicNameValuePair("response", reCaptchaRequest.recaptchaResponse)))
    )
    val response = httpClient.execute(post)
    isReCaptchaSuccess(response.getEntity.getContent)
  }

  private def isReCaptchaSuccess(response: InputStream) = {
    val responseLines = Option(response) map {
      Source.fromInputStream(_).getLines().toList
    } getOrElse Nil
    responseLines match {
      case "true" :: _ => true
      case "false" :: "incorrect-captcha-sol" :: _=> false
      case "false" :: msg :: _ => throw new ReCaptchaException(msg)
      case resp => throw new ReCaptchaException("Unrecognized response: " + resp.toList)
    }
  }

}

class ReCaptchaException(msg: String) extends RuntimeException(msg)
```

The only missing piece is the `ReCaptchaSecured` trait encapsulating two reCAPTCHA fields mentioned earlier.
In order to secure any web form with reCAPTCHA I am simply extending this model:

```scala
trait ReCaptchaSecured {
  @BeanProperty var recaptchaChallenge = ""
  @BeanProperty var recaptchaResponse = ""
}

class NewComment extends ReCaptchaSecured {
  @BeanProperty var name = ""
  @BeanProperty var contents = ""
}
```

The whole [`CommentsController.scala`](https://github.com/nurkiewicz/recaptcha-spring-integration/blob/master/src/main/scala/com/blogspot/nurkiewicz/web/CommentsController.scala) is not that relevant.
But the result is!

[![](/assets/img/integrating-with-recaptcha-using-spring/1.png)](/assets/img/integrating-with-recaptcha-using-spring/1.png)

[![](/assets/img/integrating-with-recaptcha-using-spring/2.png)](/assets/img/integrating-with-recaptcha-using-spring/2.png)

So it works, but obviously it wasn't really spectacular.
What would you say about replacing the low-level HttpClient call with Spring Integration?
The `ReCaptchaVerifier` interface (trait) remains the same so the client code doesn't have to be changed.
But we refactor [`HttpClientReCaptchaVerifier`](https://github.com/nurkiewicz/recaptcha-spring-integration/blob/raw-http-client/src/main/scala/com/blogspot/nurkiewicz/recaptcha/HttpClientReCaptchaVerifier.scala) into two separate, small, relatively high-level and abstract classes:

```scala
@Service
class ReCaptchaFormToHttpRequest @Autowired() (servletRequest: HttpServletRequest, @Value("${recaptcha_private_key}") recaptchaPrivateKey: String) {

  def transform(form: ReCaptchaSecured) = Map(
    "privatekey" -> recaptchaPrivateKey,
    "remoteip" -> servletRequest.getRemoteAddr,
    "challenge" -> form.recaptchaChallenge,
    "response" -> form.recaptchaResponse).asJava

}

@Service
class ReCaptchaServerResponseToResult {

  def transform(response: String) = {
    val responseLines = response.split('\n').toList
    responseLines match {
      case "true" :: _ => true
      case "false" :: "incorrect-captcha-sol" :: _=> false
      case "false" :: msg :: _ => throw new ReCaptchaException(msg)
      case resp => throw new ReCaptchaException("Unrecognized response: " + resp.toList)
    }
  }

}
```

Note that we no longer have to implement `ReCaptchaVerifier`, Spring Integration will do it for us.
We only have to tell how is the framework suppose to use building blocks we have extracted above.
I think I haven't yet described what Spring Integration is and how it works.
In few words it is a very pure implementation of [enterprise integration patterns](http://www.amazon.com/gp/product/0321200683/ref=as_li_ss_il?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=1789&creative=390957&creativeASIN=0321200683) (some may call it ESB).
The message flows are described using XML and can be embedded inside standard Spring XML configuration:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans:beans xmlns:beans="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns="http://www.springframework.org/schema/integration"
       xmlns:http="http://www.springframework.org/schema/integration/http"
       xsi:schemaLocation="
           http://www.springframework.org/schema/integration
           http://www.springframework.org/schema/integration/spring-integration.xsd
           http://www.springframework.org/schema/beans
           http://www.springframework.org/schema/beans/spring-beans.xsd
           http://www.springframework.org/schema/integration/http
           http://www.springframework.org/schema/integration/http/spring-integration-http.xsd
           ">

       <!-- configuration here -->    

</beans:beans>
```

In our case we will describe a message flow from `HttpClientReCaptchaVerifier` Java interface/Scala trait to the reCAPTCHA server and back.
On the way the ` ReCaptchaSecured` object must be translated into HTTP request and the HTTP response should be translated into meaningful result, returned transparently from the interface.

```xml
<gateway id="ReCaptchaVerifier" service-interface="com.blogspot.nurkiewicz.recaptcha.ReCaptchaVerifier" default-request-channel="reCaptchaSecuredForm"/>

<channel id="reCaptchaSecuredForm" datatype="com.blogspot.nurkiewicz.web.ReCaptchaSecured"/>

<transformer input-channel="reCaptchaSecuredForm" output-channel="reCaptchaGoogleServerRequest" ref="reCaptchaFormToHttpRequest"/>

<channel id="reCaptchaGoogleServerRequest" datatype="java.util.Map"/>

<http:outbound-gateway
    request-channel="reCaptchaGoogleServerRequest"
    reply-channel="reCaptchaGoogleServerResponse"
    url="${recaptcha_url}"
    http-method="POST"
    extract-request-payload="true"
    expected-response-type="java.lang.String"/>

<channel id="reCaptchaGoogleServerResponse" datatype="java.lang.String"/>

<transformer input-channel="reCaptchaGoogleServerResponse" ref="reCaptchaServerResponseToResult"/>
```

Despite the amount of XML, the overall message flow is quite simple.
First we define [gateway](http://www.eaipatterns.com/MessagingGateway.html), which is a bridge between Java interface and Spring Integration message flow.
The argument of `ReCaptchaVerifier.validate()` later becomes a [message](http://www.eaipatterns.com/Message.html) that is sent to `reCaptchaSecuredForm` [channel](http://www.eaipatterns.com/MessageChannel.html).
From that channel `ReCaptchaSecured` object is passed to a `ReCaptchaFormToHttpRequest` [transformer](http://www.eaipatterns.com/MessageChannel.html).
The purpose of the transformer is two translate from `ReCaptchaSecured` object to Java map representing a set of key-value pairs.
Later this map is passed (through `reCaptchaGoogleServerRequest` channel) to `http:outbound-gateway`.
The responsibility of this component is to translate previously created map into an HTTP request and send it to specified address.

When the response comes back, it is sent to `reCaptchaGoogleServerResponse` channel.
There `ReCaptchaServerResponseToResult` transformer takes action, translating HTTP response to business result (boolean).
Finally the transformer result is routed back to the gateway.
Everything happens synchronously by default so we can still use simple Java interface for reCAPTCHA validation.

Believe it or not, this all works.
We no longer use `HttpClient` (guess everything is better compared to HttpClient 4 API...)
and instead of one "huge" class we have a set of smaller, focused, easy to test classes.
The framework handles wiring up and the low-level details.
Wonderful?

#### [Architect's Dream or Developer's Nightmare?](http://www.debs.msrg.utoronto.ca/hohpe.pdf)

Let me summarize our efforts by quoting the conclusions from the presentation above: *balance architectural benefits with development effectiveness*.
Spring Integration is capable of receiving data from various heterogeneous sources like JMS, relational database or even FTP, aggregating, splitting, parsing and filtering messages in multiple ways and finally sending them further with the most exotic protocols.
Coding all this by hand is a really tedious and error-prone task.
On the other hand sometimes we just don't need all the fanciness and getting our hands dirty (e.g.
by doing a manual HTTP request and parsing the response) is much simpler and easier to understand.
Before you blindly base your whole architecture either on very high-level abstractions or on hand-coded low-level procedures: think about the consequences and balance.
No solution fits all problems.
Which version of reCAPTCHA integration do you find better?
