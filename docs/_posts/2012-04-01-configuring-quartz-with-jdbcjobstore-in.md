---
layout: post
title: Configuring Quartz with JDBCJobStore in Spring
date: '2012-04-01T22:42:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- spring
- quartz
modified_time: '2012-04-01T22:42:20.451+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4839418424844112322
blogger_orig_url: https://www.nurkiewicz.com/2012/04/configuring-quartz-with-jdbcjobstore-in.html
---

I am starting a little series about [Quartz scheduler](http://quartz-scheduler.org/) internals, tips and tricks, this is a chapter 0 - how to configure persistent job store.
In Quartz you essentially have a choice between storing jobs and triggers in memory and in a relation database ( [Terracotta](http://terracotta.org/) is a recent addition to the mix).
I would say in 90% of the cases when you use `RAMJobStore` with Quartz you don't really need Quartz at all.
Obviously this storage backend is transient and all your pending jobs and triggers are lost between restarts.
If you are fine with that, much simpler and more lightweight solutions are available, including [`ScheduledExecutorService`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ScheduledExecutorService.html) built into JDK and `@Scheduled(cron="*/5 * * * * MON-FRI")` in Spring.
Can you justify using extra 0,5MiB JAR in this scenario?

This changes dramatically when you need clustering, fail-over, load-balancing and few other buzz-words.
There are several use-cases for that:

- single server cannot handle required number of concurrent, long running jobs and the executions need to be split into several machines - but each task must be executed exactly ones
- we cannot afford to run jobs too late - if one server is down, another should run the job on time
- ...or less strictly - the job needs to run **eventually** - even if the one and only server was down for maintenance, delayed jobs need to be run as soon as possible after restart

In all cases above we need some sort of non-transient global storage to keep track which jobs were executed, so that they are run exactly ones by one machine.
Relational database as a shared memory works good in this scenario.

So if you think you need to schedule jobs and have some of the requirements above, keep reading.
I will show you how to configure Quartz with Spring and fully integrate them.
First of all we need a `DataSource`:

```scala
import org.apache.commons.dbcp.BasicDataSource
import com.googlecode.flyway.core.Flyway
import org.jdbcdslog.DataSourceProxy
import org.springframework.jdbc.datasource.{DataSourceTransactionManager, LazyConnectionDataSourceProxy}
import org.h2.Driver

@Configuration
@EnableTransactionManagement
class Persistence {

    @Bean
    def transactionManager() = new DataSourceTransactionManager(dataSource())

    @Bean
    @Primary
    def dataSource() = {
        val proxy = new DataSourceProxy()
        proxy.setTargetDSDirect(dbcpDataSource())
        new LazyConnectionDataSourceProxy(proxy)
    }

    @Bean(destroyMethod = "close")
    def dbcpDataSource() = {
        val dataSource = new BasicDataSource
        dataSource.setDriverClassName(classOf[Driver].getName)
        dataSource.setUrl("jdbc:h2:mem:quartz-demo;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE;MVCC=TRUE")
        dataSource.setUsername("sa")
        dataSource.setPassword("")
        dataSource.setMaxActive(20)
        dataSource.setMaxIdle(20)
        dataSource.setMaxWait(10000)
        dataSource.setInitialSize(5)
        dataSource.setValidationQuery("SELECT 1")
        dataSource
    }

}
```

As you might have guessed, Quartz needs some database tables to work with.
It does not create them automatically, but SQL scripts for several databases are provided, including H2 which as you can see I am using.
I think [Flyway](http://code.google.com/p/flyway) is the easiest way to run database scripts on startup:

```scala
@Bean(initMethod = "migrate")
def flyway() = {
 val fly = new Flyway()
 fly.setDataSource(dataSource())
 fly
}
```

BTW in case you haven't noticed: no, there is no XML in our sample application and yes, we are using Spring.

Let's move on to Quartz:

```scala
@Configuration
class Scheduling {

    @Resource
    val persistence: Persistence = null

    @Bean
    @DependsOn(Array("flyway"))
    def schedulerFactory() = {
        val schedulerFactoryBean = new SchedulerFactoryBean()
        schedulerFactoryBean.setDataSource(persistence.dataSource())
        schedulerFactoryBean.setTransactionManager(persistence.transactionManager())
        schedulerFactoryBean.setConfigLocation(new ClassPathResource("quartz.properties"))
        schedulerFactoryBean.setJobFactory(jobFactory())
        schedulerFactoryBean.setApplicationContextSchedulerContextKey("applicationContext")
        schedulerFactoryBean.setSchedulerContextAsMap(Map().asJava)
        schedulerFactoryBean.setWaitForJobsToCompleteOnShutdown(true)
        schedulerFactoryBean
    }

    @Bean
    def jobFactory() = new SpringBeanJobFactory

}
```

It is nice to know you can inject instance of `@Configuration` annotated classes into another such class for convenience.
Except that - nothing fancy.
Note that we need `@DependsOn(Array("flyway"))` on Quartz scheduler factory - otherwise the scheduler might start before Flyway fired the migration script with Quartz database tables causing unpleasant errors on startup.
The essential bits are [`SpringBeanJobFactory`](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/scheduling/quartz/SpringBeanJobFactory.html) and `schedulerContextAsMap`.
The special factory makes Spring responsible for creating `Job` instances.
Unfortunately this factory is quite limited which we will see shortly in the following example.
First we need a Spring bean and a Quartz job:

```scala
@Service
class Printer extends Logging {

    def print(msg: String) {
        logger.info(msg)
    }

}

class PrintMessageJob extends Job with Logging {

    @BeanProperty
    var printer: Printer = _

    @BeanProperty
    var msg = ""

    def execute(context: JobExecutionContext) {
        printer print msg
    }
}
```

First unexpected input is `@BeanProperty` instead of `@Autowired` or `@Resource`.
Turns out that `Job` is not really a Spring bean, even though Spring creates an instance of it.
Instead Spring discovers required dependencies using available setters.
So where does the `msg` string come from?
Keep going:

```scala
val trigger = newTrigger().
        withIdentity("Every-few-seconds", "Demo").
        withSchedule(
            simpleSchedule().
                    withIntervalInSeconds(4).
                    repeatForever()
        ).
        build()

val job = newJob(classOf[PrintMessageJob]).
        withIdentity("Print-message", "Demo").
        usingJobData("msg", "Hello, world!").
        build()

scheduler.scheduleJob(job, trigger)
```

Quartz 2.0 ships with a nice internal DSL for creating jobs and triggers in a readable manner.
As you can see I am passing an extra `"Hello, world!"`
parameter to the job.
This parameter is stored in so called `JobData` in the database per job or per trigger.
It will be provided to the job when it is executed.
This way you can parametrize your jobs.
However when executed our job throws `NullPointerException`...
Apparently ` printer` reference was not set and silently ignored.
Turns out Spring won't simply look through all the beans available in the `ApplicationContext`.
The `SpringBeanJobFactory` only looks into `Jobs'` and `Triggers'` `JobData` and into so called scheduler context (already mentioned).
If you want to inject any Spring bean into `Job` you must explicitly place a reference to that bean in `schedulerContext`:

```scala
@Configuration
class Scheduling {

    @Resource
    val printer: Printer = null

    @Bean
    def schedulerFactory() = {
        val schedulerFactoryBean = new SchedulerFactoryBean()
        //...
        schedulerFactoryBean.setSchedulerContextAsMap(schedulerContextMap().asJava)
        //...
        schedulerFactoryBean
    }

    def schedulerContextMap() =
        Map(
            "printer" -> printer
        )

}
```

Unfortunately each and every Spring bean you want to inject to job has to be explicitly referenced in ` schedulerContextMap`.
Even worse, if you forget about it, Quartz will silently log NPE at runtime.
In the future we will write more robust job factory.
But for starters we have a working Spring + Quartz application ready for further experiments, [sources](https://github.com/nurkiewicz/quartz-demo) as always available under my GitHub account.

You might ask yourself way can't we simply use [MethodInvokingJobDetailFactoryBean](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/scheduling.html#scheduling-quartz-method-invoking-job)?
Well, first of all because it [does not work](http://static.springsource.org/spring/docs/current/javadoc-api/org/springframework/scheduling/quartz/MethodInvokingJobDetailFactoryBean.html) with persistent job stores.
Secondly - because it is unable to pass `JobData` to `Job` - so we can no longer distinguish between different job runs.
For instance our job printing message would have to always print the same message hard-coded in the class.

BTW if anyone asks you: *How many classes does a Java enterprise developer need to print “Hello world!"*
you can proudly reply: *4 classes, 30 JARs taking 20 MiB of space and a relational database with 10+ tables*.
Seriously, this is an output of our article here...
