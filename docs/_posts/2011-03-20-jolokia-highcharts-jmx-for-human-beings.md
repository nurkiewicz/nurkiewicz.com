---
layout: post
title: Jolokia + Highcharts = JMX for human beings
date: '2011-03-20T19:46:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- jquery
- jfreechart
- javascript
- jmx
- jolokia
- monitoring
- jqplot
- highcharts
modified_time: '2011-11-17T19:17:16.718+01:00'
thumbnail: https://lh5.googleusercontent.com/-H3nlHGAfKN0/TYZJODIuekI/AAAAAAAAAaQ/cA8_tVMcqio/s72-c/single.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8563938229337803058
blogger_orig_url: https://www.nurkiewicz.com/2011/03/jolokia-highcharts-jmx-for-human-beings.html
---

Java Management Extensions ([JMX](http://www.oracle.com/technetwork/java/javase/tech/javamanagement-140525.html)) is a well established, but not widespread technology allowing to monitor and manage every JVM.
It provides tons of useful information, like CPU, thread and memory monitoring.
Also every application can register its own metrics and operations in so called [MBeanServer](http://download.oracle.com/javase/6/docs/api/javax/management/MBeanServer.html).
Several libraries take advantage of JMX: [Hibernate](http://docs.jboss.org/hibernate/core/3.6/javadocs/org/hibernate/jmx/StatisticsServiceMBean.html), [EhCache](http://ehcache.org/documentation/jmx.html) and [Logback](http://logback.qos.ch/manual/jmxConfig.html) and servers like [Tomcat](http://tomcat.apache.org/tomcat-7.0-doc/monitoring.html) or [Mule ESB](http://www.mulesoft.org/documentation/display/MULE3USER/JMX+Management), to name a few.
This way one can monitor ORM performance, HTTP worker threads utilization, but also change logging levels, flush caches, etc. If you are creating your own library or container, JMX is a standard for monitoring, so please don't reinvent a wheel.
Also Spring has a wonderful support for [JMX](http://static.springsource.org/spring/docs/3.0.x/spring-framework-reference/html/jmx.html).

If this standard is so wonderful, why aren't we using it all day long?
Well, history of JMX reaches the dark ages of J2EE.
Although the specification isn't that complicated, there are at least two disadvantages of JMX effectively discouraging people from using it.
First one lies on the server side.
At the foundation of Java Management Extensions is an MBeanServer where you register MBeans.
Each MBean exposes its properties (attributes) and operations for external access.
This is fine (especially when Spring is used: 1 line of XML + two annotations), but there's a catch.
By default the MBeanServer exposes itself via RMI, which is certainly not the top XXI century protocol...

The second drawback of JMX lies on the client side.
[JConsole](http://java.sun.com/developer/technicalArticles/J2SE/jconsole.html), although not terrible, has very limited functionality.
If we want to present our JMX-enabled application to the customer, showing JConsole as a client is a bit embarrassing.
It is capable of showing graphs, but you cannot display more than one attribute at the same composite graph and you also can't observe attributes from different MBeans at the same time.
Last but not least, again, we're living in the XXI century, Swing client?
Weird RMI port?
What about Web 2.0 rave?
Knowing how much I love charts (and how data visualization is important for diagnosing and correlating facts) I felt really disappointed by JConsole capabilites.
And the only [rival](http://www.jmanage.org/) of JConsole seems dead.

##### Jolokia – bridge JMX over HTTP

I knew exactly what I wanted: HTTP transport for JMX server, so that I can easily access MBeanServer from outside without the RMI mess.
[Jolokia](http://www.jolokia.org/features-nb.html) meets my expectations perfectly.
This small library (about 170 kiB) connects to a given MBeanServer and exposes it via REST-like interface.
Just deploy the jolokia.war file on your servlet container and use whatever HTTP client you want to monitor your JVM!

```text

$ curl localhost:8080/jolokia
{
  "request" : { "type" : "version" },
  "status" : 200,
  "timestamp" : 1300561261,
  "value" : {
      "agent" : "0.83",
      "info" : {
          "product" : "tomcat",
          "vendor" : "Apache",
          "version" : "7.0.10"
        },
      "protocol" : "4.1"
    }
}


$ curl localhost:8080/jolokia/read/java.lang:type=Memory/HeapMemoryUsage
{
  "request" : {
      "attribute" : "HeapMemoryUsage",
      "mbean" : "java.lang:type=Memory",
      "type" : "read"
    },
  "status" : 200,
  "timestamp" : 1300561367,
  "value" : {
      "committed" : "169607168",
      "init" : "49404160",
      "max" : "702808064",
      "used" : "16635472"
    }
}
```

You must be aware that Jolokia has a handful of other features.
It can work on ordinary JVMs (not only servlet containers) starting dedicated web server, it can also [connect](http://www.jolokia.org/features/proxy.html) to external MBeanServer, so you don't have to add any new WAR files as long as you have JMX external access.
But the killer feature I quickly discovered was:

##### Jolokia + AJAX – a perfect couple

HTTP, JSON...
AJAX?
Accessing MBeans directly using JavaScript on the client side would be huge.
But I haven't even written a single line of code yet when I spotted Jolokia [Javascript Client Library](http://jolokia.org/reference/html/clients.html#client-javascript).
Wow, I really love this project!
So I took the token bucket application developed [last time](http://nurkiewicz.com/2011/03/tenfold-increase-in-server-throughput.html) and quickly added simple server polling for current heap memory usage.
Boring.
Chart displaying memory usage over time would be much sexier...

##### Jolokia, AJAX and Highcharts – exciting threesome

First, I owe you some explanation.
Why am I entering the dirty playground of the most hated web 2.0 child – JavaScript?
Let me reveal my goal: fast and snappy, good looking JMX visualization with real-time updates in the browser rather than in the obscure jconsole.
The solution should be simple, shouldn't require major server side changes (preferably: none) and should be highly configurable and flexible.
Leveraging [JFreeChart](http://www.jfree.org/jfreechart/) (Java de facto standard for charting) to produce new version of the chart each second or even more frequently was out of the question.

But if we already have access to JMX metrics on the client (browser) side, why not generating the charts there as well, only quickly updating data series when new data arrives.
Be pragmatic.
First I tried [jqPlot](http://www.jqplot.com/) – works great for static charts, but sucks completely when trying to update them.
Unless you can live with 10 MiB of memory leaking in the browser every second per chart...
Seems like many JavaScript charting libraries suffer the same problem – except [Highcharts](http://www.highcharts.com/) – library of my choice.
Here is how easily one can plot memory usage chart only on the client side using Jolokia JMX library:

```javascript

$(document).ready(function() {
    new Monitor();
});

function Monitor() {
    var jmx = new Jolokia("/jolokia");

    var chart = new Highcharts.Chart({
        chart: {
            renderTo: 'memoryChart',
            defaultSeriesType: 'spline',
            events: {
                load: function() {
                    var series = this.series[0];
                    setInterval(function() {
                        var x = (new Date()).getTime();
                        var memoryUsed = jmx.getAttribute("java.lang:type=Memory", "HeapMemoryUsage", "used");
                        series.addPoint({
                            x: new Date().getTime(),
                            y: parseInt(memoryUsed)
                        }, true, series.data.length >= 50);
                    }, 1000);
                }
            }
        },
        xAxis: {
            type: 'datetime'
        },
        series: [{
                data: [],
            }
        ]
    });
}
```

Few less important lines were skipped (mainly chart cosmetics), as always full source is available on [GitHub](https://github.com/nurkiewicz/token-bucket).
And this is the result so far:

[![](https://lh5.googleusercontent.com/-H3nlHGAfKN0/TYZJODIuekI/AAAAAAAAAaQ/cA8_tVMcqio/s320/single.png)](https://lh5.googleusercontent.com/-H3nlHGAfKN0/TYZJODIuekI/AAAAAAAAAaQ/cA8_tVMcqio/s1600/single.png)

BTW I bit reluctantly switched to Google Chrome browser while writing this article.
JavaScript-heavy applications are insanely slow on Firefox, work fine on Opera but Google Chrome beats them together.

Having one chart, why not add several others?
Luckily Jolokia supports [bulk](http://jolokia.org/features/bulk-requests.html) requests (also in JavaScript client library), so we will poll server only once a second, no matter how many charts are displayed.

[![](https://lh4.googleusercontent.com/-V1pVl5POZ24/TYZJWYKkXNI/AAAAAAAAAaU/vlIn5Dyt1iM/s320/multiple.png)](https://lh4.googleusercontent.com/-V1pVl5POZ24/TYZJWYKkXNI/AAAAAAAAAaU/vlIn5Dyt1iM/s1600/multiple.png)

Since we are doing so well, why not allow user to rearrange charts so that he can put most relevant ones next to each other (portlets?
iGoogle?
Anyone?)
Luckily, [jQuery UI](http://jqueryui.com/demos/sortable/portlets.html) library (Jolokia JavaScript client is built on top of jQuery) ships with portlet-like support built-in.

```javascript

function JmxChartsFactory(keepHistorySec, pollInterval, columnsCount) {
    var jolokia = new Jolokia("/jolokia");
    var series = [];
    var monitoredMbeans = [];
    var chartsCount = 0;

    columnsCount = columnsCount || 3;
    pollInterval = pollInterval || 1000;
    var keepPoints = (keepHistorySec || 600) / (pollInterval / 1000);

    setupPortletsContainer(columnsCount);

    setInterval(function() {
        pollAndUpdateCharts();
    }, pollInterval);

    this.create = function(mbeans) {
        mbeans = $.makeArray(mbeans);
        series = series.concat(createChart(mbeans).series);
        monitoredMbeans = monitoredMbeans.concat(mbeans);
    };

    function pollAndUpdateCharts() {
        var requests = prepareBatchRequest();
        var responses = jolokia.request(requests);
        updateCharts(responses);
    }

    function createNewPortlet(name) {
        return $('#portlet-template')
                .clone(true)
                .appendTo($('.column')[chartsCount++ % columnsCount])
                .removeAttr('id')
                .find('.title').text((name.length > 50? '...' : '') + name.substring(name.length - 50, name.length)).end()
                .find('.portlet-content')[0];
    }

    function setupPortletsContainer() {
        var column = $('.column');
        for(var i = 1; i < columnsCount; ++i){
            column.clone().appendTo(column.parent());
        }
        $(".column").sortable({
            connectWith: ".column"
        });

        $(".portlet-header .ui-icon").click(function() {
            $(this).toggleClass("ui-icon-minusthick").toggleClass("ui-icon-plusthick");
            $(this).parents(".portlet:first").find(".portlet-content").toggle();
        });
        $(".column").disableSelection();
    }

    function prepareBatchRequest() {
        return $.map(monitoredMbeans, function(mbean) {
            return {
                type: "read",
                mbean: mbean.name,
                attribute: mbean.attribute,
                path: mbean.path
            };
        });
    }

    function updateCharts(responses) {
        var curChart = 0;
        $.each(responses, function() {
            var point = {
                x: this.timestamp * 1000,
                y: parseFloat(this.value)
            };
            var curSeries = series[curChart++];
            curSeries.addPoint(point, true, curSeries.data.length >= keepPoints);
        });
    }

    function createChart(mbeans) {
        return new Highcharts.Chart({
            chart: {
                renderTo: createNewPortlet(mbeans[0].name),
                animation: false,
                defaultSeriesType: 'area',
                shadow: false
            },
            title: { text: null },
            xAxis: { type: 'datetime' },
            yAxis: {
                title: { text: mbeans[0].attribute }
            },
            legend: {
                enabled: true,
                borderWidth: 0
            },
            credits: {enabled: false},
            exporting: { enabled: false },
            plotOptions: {
                area: {
                    marker: {
                        enabled: false
                    }
                }
            },
            series: $.map(mbeans, function(mbean) {
                return {
                    data: [],
                    name: mbean.path || mbean.attribute
                }
            })
        })
    }
}
```

Sure, 110 lines is a lot of code, but you must admit that it's not that much when feature set is considered: configurable chart history length, polling interval and number of columns in portlet layout.
Also, the set of visible JMX charts are fully customizable.
If you want, you might easily add the possibility to add and remove charts at runtime when needed or even browsing MBeanServer exposed beans.
The usage is of this class is very simple:

```javascript

$(document).ready(function() {
    var factory = new JmxChartsFactory();
    factory.create([
        {
            name: 'java.lang:type=Memory',
            attribute: 'HeapMemoryUsage',
            path: 'committed'
        },
        {
            name: 'java.lang:type=Memory',
            attribute: 'HeapMemoryUsage',
            path: 'used'
        }
    ]);
    factory.create([
        {
            name: 'java.lang:type=OperatingSystem',
            attribute: 'SystemLoadAverage'
        }
    ]);
    factory.create({
        name:     'java.lang:type=Threading',
        attribute: 'ThreadCount'
    });
    factory.create([
        {
            name: 'Catalina:name="http-bio-8080",type=ThreadPool',
            attribute: 'currentThreadsBusy'
        },
        {
            name: 'Catalina:name=executor,type=Executor',
            attribute: 'queueSize'
        }
    ]);
    factory.create([
        {
            name: 'com.blogspot.nurkiewicz.download.tokenbucket:name=perRequestTokenBucket,type=PerRequestTokenBucket',
            attribute: 'OngoingRequests'
        },
        {
            name: 'com.blogspot.nurkiewicz.download:name=downloadServletHandler,type=DownloadServletHandler',
            attribute: 'AwaitingChunks'
        }
    ]);
});
```

Tired of code?
HTML for this article can be found [here](https://github.com/nurkiewicz/token-bucket/blob/master/src/main/webapp/index.html), and as Chinese used to say, *a picture is worth a thousand* *lines of code*:

[![](https://lh4.googleusercontent.com/-oJPWOO1VYAU/TYZJc98K_lI/AAAAAAAAAaY/erLrPCHYv7A/s320/portlet.png)](https://lh4.googleusercontent.com/-oJPWOO1VYAU/TYZJc98K_lI/AAAAAAAAAaY/erLrPCHYv7A/s1600/portlet.png)

But because our monitoring dashboard is so dynamic, to quote [Nicolaus Copernicus](http://en.wikipedia.org/wiki/Nicolaus_Copernicus) “*A YouTube video is worth a thousand pictures*”\* (somewhere in the middle you'll see the system reacting after heavy load was simulated):

# Wystąpił błąd.

Nie można wykonać skryptu JavaScript.

Now these 100+ lines of JavaScript code aren't that overwhelming, don't you think?
To summarize, using JavaScript and handful of readily available libraries we added interactive, refreshable, Web 2.0-ish monitoring dashboard.
It integrates seamlessly with every JVM using JMX, and if we would use Jolokia [proxy](http://www.jolokia.org/features/proxy.html) mode, **no** changes would be required in monitored application/server.
Because the client asks JMX server in batch and updates charts on the client side, everything works with minimal delay.

So the next time your customer asks for a monitoring solution or you want to enrich existing application without modifying it too much – consider the simplest solution, as it might be the best one as well.
And maybe this tiny dashboard code is a valuable milestone of a decent successor of aforementioned [JManage](http://www.jmanage.org/)?

\* Other famous quote by [Nicolaus Copernicus](http://en.wikipedia.org/wiki/Nicolaus_Copernicus): “*Don't believe in everything you read in the Internet*”...
