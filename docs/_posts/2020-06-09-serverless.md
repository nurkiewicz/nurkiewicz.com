---
title: '#4: Serverless'
permalink: /4
tags: cloud faas lambda
description: Serverless (function as a service) is the fastest and most cost effective way of deploying your code to the cloud. However it suffers the cold start problem and pricing is not always straightforward
---

{% include player.html episode_id="1RiPQDsstfeXwB0BWNxcYF" %}

{{ page.description }}

In order to fully appreciate how simple it is let's think about the history for a while.
In the beginning we had to order physical servers, put them into racks, wire them to the network and deploy the code on top of them once they were provisioned.
Then cloud came in and we could get a virtual machine using an API call in 1 or 2 minutes.
We no longer have to have our own servers.
However having individual machine means we have to provision it ourselves: install packages, install servers, and deploy our code.
With serverless it's even simpler.

You simply write your code, preferably in a dynamic languages like Python, Ruby or JavaScript and then you simply deploy it using an API call.
You say: "_this is my piece of code I want to run it as a function in your cloud_" and guess what?
A couple of seconds later you have an HTTP endpoint which, after you invoke it, actually runs your function.
That's it!
You don't have to build your application, you don't have to package it into a container, you simply deploy it straight from your editor.
What's also very appealing is that you pay as you go.
You don't pay for a whole physical server, you don't pay for a virtual machine.
You only pay for the amount of time your function was invoked.
If you just deployed a function and no one ever invoked your HTTP endpoint that runs your function, then you pay nothing.
If someone calls your function either from the Internet or maybe another function, the cloud will only charge you for the number of milliseconds your function was running.
And also for the amount of memory, CPU and network traffic.
This means that for systems that have very low traffic serverless becomes really, really cheap.

Because your function only lives for this short amount of time when it serves a request and then it goes to sleep and it no longer consumes and resources it's truly stateless and some even say serverless.
However, most likely you do need some backing services, like databases, queues and so on and you will use other offerings from your cloud provider.

Another benefit of serverless is auto scaling.
If your function is never called it consumes no resources at all.
However if there is a sudden spike of traffic for just a brief moment, the cloud provider will make sure to spin up as many instances of the function as needed.
Maybe even hundreds or thousands.
When spike of traffic goes down your functions will go to sleep and you no longer pay for the extra traffic.
This means that auto scaling is much faster compared to speeding up your server or spinning up new virtual machines.

Obviously serverless or function-as-a-service has many disadvantages as well.
The biggest one is known as cold start.
It's not a coincidence that I mentioned dynamic languages like python or Java Script.
When you're running them, there is no expensive virtual machine that needs to warm up before it can actually serve request.
Serverless with Java or C# is not that much appealing, although still practiced.
Because, for example, JVM needs at least a few hundred milliseconds to speed up.
But this gets better and better especially with GraalVM.
Secondly, it's not truly a disadvantage, however, if you are old enough you remember, common gateway interface.
A practice of running executables on the web server, so that every time a new request was coming in an executable was invoked.
It was reading a request from standard input and then it was spitting HTML or XML to its standard output.
And standard output was redirected back to the clients, to the browser.
This technique is long forgotten precisely because of the cold start problem.
However, cloud providers are doing their best to reduce the problem of cold start.

# FaaS (Function-as-a-service) in public clouds

* [AWS Lambda](https://aws.amazon.com/lambda/)
* [Google Cloud Functions](https://cloud.google.com/functions/)
* [Azure Functions](https://azure.microsoft.com/en-us/services/functions/)

# Frameworks

* [Spring Cloud Function](https://spring.io/projects/spring-cloud-function)


