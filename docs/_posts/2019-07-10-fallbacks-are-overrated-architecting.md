---
layout: post
title: Fallbacks Are Overrated - Architecting For Resilience
date: '2019-07-10T09:00:00.000+02:00'
author: Tomasz Nurkiewicz
tags: 
modified_time: '2019-07-10T09:00:14.658+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4090713490418643825
blogger_orig_url: https://www.nurkiewicz.com/2019/07/fallbacks-are-overrated-architecting.html
image: /assets/img/fallbacks-are-overrated-architecting/hero.jpg
---

## Abstract

Fallbacks in circuit breakers replace failure with some pre-configured response so that the scope of the malfunction is limited and hidden from the end user.
However, in real life, a naïve fallback is often too simple and either confusing or unacceptable.
I suggest a more robust approach to handling failures, compensating for broken transactions in the future.

Reading time: 8 minutes.

## What is a circuit breaker?

A circuit breaker is a layer between your code and external dependencies that have a high risk of failure.
Every time you call another service, database, or even touch your own disk, there is a possibility of failure.
Without circuit breakers such a simple error quickly escalates, bubbling up to your end user.
All too often minor dependency brings down a huge system, resulting in 503 HTTP responses or slowness.
Circuit breaker discovers raised error levels or elevated response times quickly.
Rather than slowing the whole system, it cuts off entire dependency temporarily.
Your code still *fails* but *fails fast*.
Failing fast is important.
A website that shows the error page immediately is much better than the one returning a valid response after 30 seconds in most cases.
Also, you give your dependency some breathing room, maybe it’s overloaded, has a cold cache or it is restarting.

## What is a fallback?

Well, your application fails fast - but still, it *fails*.
This is where fallbacks come into play.
Both [resilience4j](https://github.com/resilience4j/resilience4j#circuitbreaker) and [Hystrix](https://github.com/Netflix/Hystrix/wiki/How-To-Use#Fallback) ([R.I.P.](https://github.com/Netflix/Hystrix#hystrix-status)) circuit breaker libraries for Java support fallbacks.
The idea is dead simple: when an exception occurs, replace it with some pre-configured response.
It can either be a constant value or another operation - hopefully, less risky.
Fallback is a [10 dollar word](https://www.urbandictionary.com/define.php?term=ten-dollar%20word) for something as simple as a `try`-`catch`:

```java
RecommendedMovies findRecommendations() {
    try {
        return riskyComplexAlgorithm();
    } catch(RuntimeException | TimeoutException e) {
        return bestsellersFallback;
    }
}
```

This is a hello-world example of fallbacks.
Imagine you are building a video streaming platform and have a complex, machine-learning-driven (™) algorithm to find the most relevant movies to watch next.
Keeping you in front of the screen is important so recommendations are crucial.
So what happens when our algorithm breaks?
Naive implementation propagates the exception and breaks the whole user interface.
Not only you don’t see recommendations.
You don’t see anything except `503 Internal Server Error`.
A slightly more robust implementation catches the exception and returns an empty list of recommendations.
That’s fine.
But we can do better.
We can compute most watched movies in the last few days and return such unpersonalized recommendations to everyone.
Movies are not recommended precisely based on your watching preferences.
We may miss entirely, but more often than not most watched movies overall will appeal to the majority.
This is your fallback, over there.
Catch the exception and either return empty recommendations or some pre-populated response that makes at least some sense.

## Fallbacks are naïve

A video streaming company or e-commerce can still do business without accurate recommendations.
They can still do business without any recommendations whatsoever.
Their average streaming time or order value will decrease, but at least they will still make *some* money.
But what if a more essential step of your business process fails?
For example, you are about to charge your customer for newly placed order.
There are two essential parts of this process: fraud detection and charging a credit card.
How circuit breaker and fallbacks help here?
Circuit breaker alone is a good idea.
On the one hand, you don’t let your customers wait forever for a failure.
Circuit breaker makes sure timeouts are strict and enforced.
On the other hand, when the circuit is open you give your dependencies a chance to heal by reducing their load.
But can we apply fallbacks here?
A fallback for a broken fraud detection system, that essentially returns a `boolean` is simple.
Either assume every transaction is legit (`catch(e) {return true}`) and possibly lose some money on fraudulent orders.
Or the opposite - treat everyone like a crook and make no money at all.
Temporarily switching off fraud detection sounds fine, until you realize how quickly cheaters figure out you have no control mechanisms in place.
Maybe you’ll get away with it for weeks, but assume it’s more like minutes.
Been there.

With broken credit card payment gateway, it gets even worse.
You are not able to charge the customer’s credit card.
Processing transactions without actually charging any money is a recipe for disaster.
Surely, your customers don’t leave angry to your competition.
But you must understand that’s just losing money on each and every transaction.
Unless you’re [Uber](https://www.uber.com/), this can’t possibly work.
The alternative is equally bad.
Your fallback fails fast with an exception.
No-one can make a transaction.
Customers are walking away, just like expected.
You are not losing money.
You are not making any money as well.

## Fallbacks in real life

These days when computer systems fail, many businesses cease to operate.
Airlines, stock exchanges, and even hospitals or cars are entirely dependent on information systems.
But there are businesses that used to work without computers just fine and they could technically operate without them for a while.
Think about a cashier that notes down your groceries on a piece of paper so that he or she can put them back to the computer when it’s fixed.
Or a ticket agent that sells tickets without an electronic system.
Hoping he is not double-booking with some other offline agent.
Hey, flights are overbooked even when everything is online!
Somehow people learned how to deal with broken machines and eventual consistency.
Maybe our systems should learn that as well?

## Don’t fallback, compensate and recover

Let’s think about our examples of fraud detection and credit card payment gateway being broken.
How would humans deal with that in the sanest manner?
When a fraud detection system is broken, a human does not close the business.
Instead, he or she notes down all transactions that took place and later, when fraud detection is back, problematic transactions are examined in large batch retrospectively.
The merchant knows that e.g. only 0.1% of transactions are fraudulent.
So merchant accepts that risk and when he or she discovers a fraud afterward, certain actions are taken immediately.

But we should definitely cease all operations when payment gateway is broken?
First of all, people should still be allowed to browse, search, add products to basket, etc. If a broken payment component breaks your whole system, you are in much deeper trouble.
But let’s take one more step.
What if we, bear with me, simply assume all payments succeeded and continue processing online purchases?
If you are selling physical goods, this is actually quite safe.
Despite payment gateway failure, assume credit card was charged.
Start completing the order, after all, it’ll take hours if not days until you ship it.
By that time payment gateway may recover.
And you will have an opportunity to charge all credit cards used throughout the outage, retrospectively.
Customers won’t even notice an outage or a delay.
Well, as a matter of fact, they will.
They just left another online store, because our competition couldn’t complete their order - due to the same gateway failure.
But your shop seems to be working and orders seem to proceed.

OK, but if someone really provided fake credit card but we happily accepted such purchase?
No worries, most likely the package still didn’t leave our storage and can be stopped.
And even if it did and there is no way of getting it back, lost money is nothing compared to shutting down the store entirely for hours.

## Implementation

This is how we should design our systems.
In the presence of failure:

- **don’t** give up by propagating an error immediately.
  This creates fragile architectures that don’t withstand any failure
- **don’t** assume everything is fine.
  People will very quickly discover your fraud detection system is bypassed and never exercised.
  Yes, they will.
  Fast.
  Believe me
- **do** make optimistic business decisions if possible, but verify and compensate them afterward.

From a technical perspective, your recovery code should look more or less like this:

```java
try {
    businessAsUsual(thingy);
    return true;
} catch(Exception e) {
    scheduleCompensationLater(thingy);
    return true;
}
```

`scheduleCompensationLater()` method should record failed business transaction in persistent storage.
Later on, some background process must make sure that our optimistic assumption was correct and react accordingly.
Keep in mind that:

- recovery and compensation code can fail as well.
  Test for that.
  Be reasonable, if your business process failed because of storage failure, keeping the recovery task in the same storage will most likely fail as well.
- Negative verification can happen too late.
  You must act fast, as soon as failed components come back online.
  It’s too late if you already shipped a packaged that was not charged
- Measure!
  Number of failures, time to recover, number of pending recovery tasks.
  If numbers are worrying, apply kill switch.

## Kill switch

At some point, you will realize that you are too optimistic.
A sudden increase in the number of transactions can be a sign.
Being optimistic and compensating later is fine, as long as outage doesn’t last for too long.
Fraudsters will discover that and abuse the system.
Make sure your system tolerates a certain level of failures, but have automatic safety measures.
Upon discovering too much suspicious activity, turn your optimistic recovery to pessimistic failure.

## Conclusions

It’s all about risk assessments.
Our parents and grandparents used to live without computers controlling and orchestrating every aspect of their life.
These times are long gone.
But if we design our systems in a way that tolerates and can compensate certain errors, we’ll design more robust, better user experience.
And save a lot of money.
