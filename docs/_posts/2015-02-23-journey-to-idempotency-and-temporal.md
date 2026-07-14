---
layout: post
title: Journey to idempotency and temporal decoupling
date: '2015-02-23T09:26:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- jms
- spring mvc
- HTTP
- rest
- spring
modified_time: '2015-02-23T09:26:25.741+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2596562119634320142
blogger_orig_url: https://www.nurkiewicz.com/2015/02/journey-to-idempotency-and-temporal.html
---

*Idempotency* in HTTP means that the same request can be performed multiple times with the same effect as if it was executed just once.
If you replace current state of some resource with new one, no matter how many times you do so, in the end state will be the same as if you did it just once.
To give more concrete example: deleting a user is idempotent because no matter how many times you delete given user by unique identifier, in the end this user will be deleted.
On the other hand creating new user is not idempotent because requesting such operation twice will create two users.
In HTTP terms here is what [RFC 2616: 9.1.2 Idempotent Methods](http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html) has to say:

> ### 9.1.2 Idempotent Methods
>
> Methods can also have the property of "*idempotence*" in that \[...\]
> the side-effects of N \> 0 identical requests is the same as for a single request.
> The methods GET, HEAD, PUT and DELETE share this property.
> Also, the methods OPTIONS and TRACE SHOULD NOT have side effects, and so are inherently idempotent.

*Temporal coupling* is an undesirable property of a system where the correct behaviour is implicitly dependent on time dimension.
In plain English, it might mean that for example system only works when all components are present at the same time.
Blocking request-response communication (ReST, SOAP or any other form of RPC) require both client and server to be available at the same time, which is an example of this effect.

Having basic understanding what these concepts mean, let's go through a simple case study - [massively multiplayer online role-playing game](http://en.wikipedia.org/wiki/Massively_multiplayer_online_role-playing_game).
Our artificial use case is as follows: a player sends premium-rated SMS to purchase virtual sword inside game.
Our HTTP gateway is called when SMS is delivered and we need to inform `InventoryService`, deployed on a different machine.
Current API involves ReST and looks as follows:

```java
@Slf4j
@RestController
class SmsController {

    private final RestOperations restOperations;

    @Autowired
    public SmsController(RestOperations restOperations) {
        this.restOperations = restOperations;
    }

    @RequestMapping(value = "/sms/{phoneNumber}", method = POST)
    public void handleSms(@PathVariable String phoneNumber) {
        Optional<Player> maybePlayer = phoneNumberToPlayer(phoneNumber);
        maybePlayer
                .map(Player::getId)
                .map(this::purchaseSword)
                .orElseThrow(() -> new IllegalArgumentException("Unknown player for phone number " + phoneNumber));
    }

    private long purchaseSword(long playerId) {
        Sword sword = new Sword();
        HttpEntity<String> entity = new HttpEntity<>(sword.toJson(), jsonHeaders());
        restOperations.postForObject(
            "http://inventory:8080/player/{playerId}/inventory", 
            entity, Object.class, playerId);
        return playerId;
    }

    private HttpHeaders jsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    private Optional<Player> phoneNumberToPlayer(String phoneNumber) {
        //...
    }
}
```

Which in turns generates request similar to this:

```text
> POST /player/123123/inventory HTTP/1.1
> Host: inventory:8080
> Content-type: application/json
>
> {"type": "sword", "strength": 100, ...}

< HTTP/1.1 201 Created
< Content-Length: 75
< Content-Type: application/json;charset=UTF-8
< Location: http://inventory:8080/player/123123/inventory/1
```

This is fairly straightforward.
`SmsController` simply forwards appropriate data to `inventory:8080` service by POSTing sword that was purchased.
This service, immediately or after a while, returns `201 Created` HTTP response confirming the operation was successful.
Additionally link to resource is created and returned, so you can query it.
One might say: ReST state of the art.
However if you care at least a little about money of your customers and understand what ACID is (something that Bitcoin exchanges still have to learn: see [\[1\]](http://hackingdistributed.com/2014/04/06/another-one-bites-the-dust-flexcoin/), [\[2\]](http://www.infoq.com/news/2014/04/bitcoin-banking-mongodb), [\[3\]](http://java.dzone.com/articles/mongodb-bitcoin-how-nosql) and [\[4\]](http://scn.sap.com/community/hana-in-memory/blog/2013/12/21/the-problem-of-dropping-acid-non-acid-pos-is-unsuitable-for-bitcoin-and-financial-transactions)) - this API is too fragile and prone to errors.
Imagine all these types of errors:

1.  your request never reached `inventory` server
2.  your request reached server but it refused it
3.  server accepted connection but failed to read request
4.  server read request but hanged
5.  server processed request but failed to send response
6.  server sent 200 OK response but it was lost and you never received it
7.  server's response was received but client failed to process it
8.  server's response was sent but client timed-out earlier

In all these cases you simply get an exception on the client side and you have no idea what's the server's state.
Technically you should retry failed requests, but since POST is not idempotent, you might end up rewarding gamer with more than one sword (in cases 5-8).
But without retry you might loose gamer's money without giving him his precious artifact.
There must be a better way.

# Turning POST to idempotent PUT

In some cases it's surprisingly simple to convert from POST to idempotent PUT by basically moving ID generation from server to client.
With POST it was the server that generated sword's ID and sent it back to the client in `Location` header.
Turns out eagerly generating UUID on the client side and changing the semantics a bit plus enforcing some constraints on the server side is enough:

```java
private long purchaseSword(long playerId) {
    Sword sword = new Sword();
    UUID uuid = sword.getUuid();
    HttpEntity<String> entity = new HttpEntity<>(sword.toJson(), jsonHeaders());
    asyncRetryExecutor
            .withMaxRetries(10)
            .withExponentialBackoff(100, 2.0)
            .doWithRetry(ctx ->
                    restOperations.put(
                            "http://inventory:8080/player/{playerId}/inventory/{uuid}",
                            entity, playerId, uuid));
    return playerId;
}
```

The API looks as follows:

```text
> PUT /player/123123/inventory/45e74f80-b2fb-11e4-ab27-0800200c9a66 HTTP/1.1
> Host: inventory:8080
> Content-type: application/json;charset=UTF-8
>
> {"type": "sword", "strength": 100, ...}

< HTTP/1.1 201 Created
< Content-Length: 75
< Content-Type: application/json;charset=UTF-8
< Location: http://inventory:8080/player/123123/inventory/45e74f80-b2fb-11e4-ab27-0800200c9a66
```

Why it's such a big deal?
Simply put (no pun intended) client can now retry PUT request as many times as he wants.
When server receives PUT for the first time, it persists sword in the database with client-generated UUID (`45e74f80-b2fb-11e4-ab27-0800200c9a66`) as primary key.
In case of second PUT attempt we can either update or reject such request.
It wasn't possible with POST because every request was treated as a new sword purchase - now we can track whether such PUT came before or not.
We just have to remember to subsequent PUT is not a bug, it's an update request:

```java
@RestController
@Slf4j
public class InventoryController {

    private final PlayerRepository playerRepository;

    @Autowired
    public InventoryController(PlayerRepository playerRepository) {
        this.playerRepository = playerRepository;
    }

    @RequestMapping(value = "/player/{playerId}/inventory/{invId}", method = PUT)
    @Transactional
    public void addSword(@PathVariable UUID playerId, @PathVariable UUID invId) {
        playerRepository.findOne(playerId).addSwordWithId(invId);
    }

}

interface PlayerRepository extends JpaRepository<Player, UUID> {}

@lombok.Data
@lombok.AllArgsConstructor
@lombok.NoArgsConstructor
@Entity
class Sword {

    @Id
    @Convert(converter = UuidConverter.class)
    UUID id;
    int strength;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Sword)) return false;
        Sword sword = (Sword) o;
        return id.equals(sword.id);

    }

    @Override
    public int hashCode() {
        return id.hashCode();
    }
}

@Data
@Entity
class Player {

    @Id
    @Convert(converter = UuidConverter.class)
    UUID id = UUID.randomUUID();

    @OneToMany(cascade = ALL, fetch = EAGER)
    @JoinColumn(name="player_id")
    Set<Sword> swords = new HashSet<>();

    public Player addSwordWithId(UUID id) {
        swords.add(new Sword(id, 100));
        return this;
    }

}
```

Few shortcuts were made in code snippet above, like injecting repository directly to controller, as well as annotating is with `@Transactional`.
But you get the idea.
Also notice that this code is quite optimistic, assuming two swords with same UUID aren't inserted at exactly the same time.
Otherwise constraint violation exception will occur.

Side note 1: I use `UUID` type in both controller and JPA models.
They aren't supported out of the box, for JPA you need custom converter:

```java
public class UuidConverter implements AttributeConverter<UUID, String> {
    @Override
    public String convertToDatabaseColumn(UUID attribute) {
        return attribute.toString();
    }

    @Override
    public UUID convertToEntityAttribute(String dbData) {
        return UUID.fromString(dbData);
    }
}
```

Similarly for Spring MVC (one-way only):

```java
@Bean
GenericConverter uuidConverter() {
    return new GenericConverter() {
        @Override
        public Set<ConvertiblePair> getConvertibleTypes() {
            return Collections.singleton(new ConvertiblePair(String.class, UUID.class));
        }

        @Override
        public Object convert(Object source, TypeDescriptor sourceType, TypeDescriptor targetType) {
            return UUID.fromString(source.toString());
        }
    };
}
```

Side note 2: if you can't change client, you can track duplicates by storing each requests' hash on the server side.
This way when the same request is sent multiple times (retried by the client), it will be ignored.
However sometimes we might have a legitimate use case for sending the exact same request twice (e.g.
purchasing two swords within short period of time).

# Temporal coupling - client unavailability

You think you're smart but PUT with retries is not enough.
First of all a client can die while re-attempting failed requests.
If server is severely damaged or down, retrying might take minutes or even hours.
You can't simply block your incoming HTTP request just because one of your downstream dependencies is down - you must handle such requests asynchronously in background - if possible.
But extending retry time increases probability of client dying or being restarted, which would loose our request.
Imagine we received premium SMS but `InventoryService` is down at the moment.
We can retry after second, two, four, etc., but what if `InventoryService` was down for couple of hours and it so happened that our service was restarted as well?
We just lost that SMS and sword was never given to the gamer.

An answer to such issue is to persist pending request first and handle it later in background.
Upon SMS receive we barely store player ID in database table called `pending_purchases`.
A background scheduler or an event wakes up asynchronous thread that will collect all pending purchases and try to send them to `InventoryService` (maybe even in batch?)
Periodic batch threads running every minute or even second and collecting all pending requests will unavoidably introduce latency and unneeded database traffic.
Thus I'm going for a Quartz scheduler instead that will schedule retry job for each pending request:

```java
@Slf4j
@RestController
class SmsController {

    private Scheduler scheduler;

    @Autowired
    public SmsController(Scheduler scheduler) {
        this.scheduler = scheduler;
    }

    @RequestMapping(value = "/sms/{phoneNumber}", method = POST)
    public void handleSms(@PathVariable String phoneNumber) {
        phoneNumberToPlayer(phoneNumber)
                .map(Player::getId)
                .map(this::purchaseSword)
                .orElseThrow(() -> new IllegalArgumentException("Unknown player for phone number " + phoneNumber));
    }

    private UUID purchaseSword(UUID playerId) {
        UUID swordId = UUID.randomUUID();
        InventoryAddJob.scheduleOn(scheduler, Duration.ZERO, playerId, swordId);
        return swordId;
    }

    //...

}
```

And job itself:

```java
@Slf4j
public class InventoryAddJob implements Job {

    @Autowired private RestOperations restOperations;
    @lombok.Setter private UUID invId;
    @lombok.Setter private UUID playerId;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        try {
            tryPurchase();
        } catch (Exception e) {
            Duration delay = Duration.ofSeconds(5);
            log.error("Can't add to inventory, will retry in {}", delay, e);
            scheduleOn(context.getScheduler(), delay, playerId, invId);
        }
    }

    private void tryPurchase() {
        restOperations.put(/*...*/);
    }

    public static void scheduleOn(Scheduler scheduler, Duration delay, UUID playerId, UUID invId) {
        try {
            JobDetail job = newJob()
                    .ofType(InventoryAddJob.class)
                    .usingJobData("playerId", playerId.toString())
                    .usingJobData("invId", invId.toString())
                    .build();
            Date runTimestamp = Date.from(Instant.now().plus(delay));
            Trigger trigger = newTrigger().startAt(runTimestamp).build();
            scheduler.scheduleJob(job, trigger);
        } catch (SchedulerException e) {
            throw new RuntimeException(e);
        }
    }

}
```

Every time we receive premium SMS we schedule asynchronous job to be executed immediately.
Quartz will take care of persistence (if application goes down, job will be executed as soon as possible after restart).
Moreover if this particular instance goes down, another one can pick up this job - or we can form a cluster and load-balance requests between them: one instance receives SMS, another one requests sword in `InventoryService`.
Obviously if HTTP call fails, retry is re-scheduled later, everything is transactional and fail-safe.
In real code you would probably add max retry limit as well as exponential delay, but you get the idea.

# Temporal coupling - client and server can't meet

Our struggle to implement retries correctly is a sign of obscure temporal coupling between client and server - they must live together at the same time.
Technically this isn't necessary.
Imagine gamer sending an e-mail with order to customer service which they handle within 48 hours, changing his inventory manually.
The same can be applied to our case, but replacing e-mail server with some sort of message broker, e.g. JMS:

```java
@Bean
ActiveMQConnectionFactory activeMQConnectionFactory() {
    return new ActiveMQConnectionFactory("tcp://localhost:61616");
}

@Bean
JmsTemplate jmsTemplate(ConnectionFactory connectionFactory) {
    return new JmsTemplate(connectionFactory);
}
```

Having ActiveMQ connection set up we can simply send purchase request to broker:

```java
private UUID purchaseSword(UUID playerId) {
    final Sword sword = new Sword(playerId);
    jmsTemplate.send("purchases", session -> {
        TextMessage textMessage = session.createTextMessage();
        textMessage.setText(sword.toJson());
        return textMessage;
    });
    return sword.getUuid();
}
```

By entirely replacing synchronous request-response protocol with messaging over JMS topic we temporally decouple client from server.
They no longer need to live at the same time.
Moreover more than one producer and consumer can interact with each other.
E.g. you can have multiple purchase channels and more importantly: multiple interested parties, not only `InventoryService`.
Even better, if you use specialized messaging system like [Kafka](http://kafka.apache.org/) you can technically keep days (months?)
worth of messages without loosing performance.
The benefit is that if you add another consumer of purchase events to the system next to `InventoryService` it will receive lots of historical data immediately.
Moreover now your application is temporally coupled with broker so since Kafka is distributed and replicated, it works better in that case.

# Disadvantages of asynchronous messaging

Synchronous data exchange, as used in ReST, SOAP or any form of RPC is easy to understand and implement.
Who cares this abstraction insanely leaks from latency perspective (local method call is typically orders of magnitude faster compared to remote, not to mention it can fail for numerous reasons unknown locally), it's quick to develop.
One true caveat of messaging is feedback channel.
You can longer just "*send*" ("*return*") message back, as there is no response pipe.
You either need response queue with some correlation ID or temporary one-off response queues per request.
Also we lied a little bit claiming that putting a message broker between two systems fixes temporal coupling.
It does, but now we are coupled to messaging bus - which can just as well go down, especially since it's often under high load and sometimes not replicated properly.

This article shows some challenges and partial solutions to provide guarantees in distributed systems.
But in the end of the day, remember that "*exactly once*" semantics are nearly impossible to implement easily, so double check you really need them.
