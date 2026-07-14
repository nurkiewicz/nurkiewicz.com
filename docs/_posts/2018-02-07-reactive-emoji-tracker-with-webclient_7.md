---
layout: post
title: 'Reactive emoji tracker with WebClient and Reactor: aggregating data'
date: '2018-02-07T00:30:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- emojitracker
- reactor
- spring
- emoji
- webclient
modified_time: '2018-02-07T00:30:40.049+01:00'
thumbnail: /assets/img/reactive-emoji-tracker-with-webclient_7/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4884084632229804196
blogger_orig_url: https://www.nurkiewicz.com/2018/02/reactive-emoji-tracker-with-webclient_7.html
---

In the [first part](http://www.nurkiewicz.com/2018/02/reactive-emoji-tracker-with-webclient.html) we managed to connect to [emojitracker.com](http://emojitracker.com/) and consume SSE stream that looks like this:

```text
data:{"1F60D":1}

data:{"1F3A8":1,"1F48B":1,"1F499":1,"1F602":1,"2764":1}

data:{"1F607":1,"2764":2}
```

Each message represents the number of various emojis that appeared on Twitter since the previous message.
After a few transformations, we got a stream of hexadecimal Unicode values for each emoji.
E.g. for `{"1F607":1,"2764":2}` we produce three events: `"1F607"`, `"2764"`, `"2764"`.
This is how we achieved it:

```java
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

final Flux<String> stream = WebClient
        .create("http://emojitrack-gostreamer.herokuapp.com")
        .get().uri("/subscribe/eps")
        .retrieve()
        .bodyToFlux(ServerSentEvent.class)
        .flatMap(e -> Mono.justOrEmpty(e.data()))
        .map(x -> (Map<String, Integer>) x)
        .flatMapIterable(Map::entrySet)
        .flatMap(entry -> Flux.just(entry.getKey()).repeat(entry.getValue()));
```

Our next goal is to show the top 50 most popular emojis since we started the application.
But first let's convert these boring Unicode hexadecimal values into, you know, emojis!
This is pretty simple:

```java
 String hexToEmoji(String hex) {
    return new String(Character.toChars(Integer.parseInt(hex, 16)));
}
```

Seems to work:

```groovy
@Unroll
class EmojiTrackerSpec extends Specification {

    def 'translate #hex to #emoji'() {
        expect:
            hexToEmoji(hex) == emoji
        where:
            hex     || emoji
            '2611'  || '☑'
            '263A'  || '☺'
            '2764'  || '❤'
            '1F440' || '👀'
            '1F49E' || '💞'
            '1F605' || '😅'
            '1F60A' || '😊'
            '1F60D' || '😍'
            '1F60E' || '😎'
            '1F60F' || '😏'
            '1F61E' || '😞'
            '1F62D' || '😭'
            '1F646' || '🙆'
            '1F6B6' || '🚶'
    }

}
```

Apparently, this is the weirdest test case I ever wrote.
Let's plug in `hexToEmoji()`:

```java
final Flux<String> stream = WebClient
         //...see above for missing lines...
        .map(ServerSentEvent::data)
        .map(x -> (Map<String, Integer>) x)
        .flatMapIterable(Map::entrySet)
        .flatMap(entry -> Flux.just(entry.getKey()).repeat(entry.getValue()))
        .map(Tracker::hexToEmoji);
```

My terminal exploded with happy faces, hearts and other emojis:

```text
Received: 🎥
Received: 💙
Received: 😍
Received: 🚑
Received: 😂
Received: 😒
Received: 🎉
Received: 😉
Received: ❤
Received: ⚽
Received: 👐
Received: 😍
Received: ♻
Received: ♻
Received: 💙
Received: 🔥
Received: 😂
Received: 😅
Received: 😘
Received: 💪
Received: 😉
Received: ♻
Received: 😪
Received: 😃
Received: 🙏
Received: 💔
Received: 😂
Received: 😍
Received: 🎶
Received: 🎹
Received: 👍
Received: 🔥
Received: 😎
```

Then it exploded for real with: `NumberFormatException: For input string: "1F1F5-1F1F1"`.
Turns out some emojis are bigger than the other.
For example, two individual characters: 🇵 and 🇱 when placed next to each other (🇵🇱) *may* be rendered as a flag.
Polish flag in this case.
A single emoji formed from two emojis.
We need to enhance our parsing logic by parsing each hexadecimal number separated by dash (`-`) individually and concatenating characters.
To be honest I started with something quite complex:

```java
private static String codeToEmoji(String hex) {
    return Arrays
            .stream(hex.split("-"))
            .map(Tracker::hexToEmoji)
            .collect(joining());
}

private static String hexToEmoji(String hex) {
    return new String(Character.toChars(Integer.parseInt(hex, 16)));
}
```

But it turns out the more straightforward solution is both more readable and most likely faster:

```java
private static String codeToEmoji(String hex) {
    final String[] codes = hex.split("-");
    if (codes.length == 2) {
        return hexToEmoji(codes[0]) + hexToEmoji(codes[1]);
    } else {
        return hexToEmoji(hex);
    }
}
```

Maybe not as impressive, but I like it more.
Few more test cases and we are free to go:

```groovy
'1F1F5-1F1F1' || '🇵🇱'
'1F1FA-1F1E6' || '🇺🇦'
'1F1FA-1F1F8' || '🇺🇸'
```

OK, we are finally ready to aggregate individual events.
We must somehow aggregate individual emojis into some sort of histogram (occurrence map).
Basically, we want a `Map<String, Long>` of all emojis since the very beginning.
The worst way to do this is global, mutable state:

```java
final ConcurrentHashMap<String, Long> histogram = new ConcurrentHashMap<>();

final Flux<String> stream = WebClient
         //...see above for missing lines...
        .map(Tracker::codeToEmoji)
        .doOnNext(emoji -> histogram.merge(emoji, 1L, Math::addExact));
```

If you are still not aware of `Map.merge()` method, it does something quite common, that can be expressed like this:

```java
if(histogram.contains(emoji)) {
    histogram.put(emoji, Math.addExact(histogram.get(emoji), 1L)
} else {
    histogram.put(emoji(1L));
}
```

After five seconds the `histogram` may look for example like this:

{💸=1, ☀=1, ☁=1, ✅=2, ⬅=1, ✈=1, 💯=3, 🚮=1, ✋=2, ✌=2, 💲=1, 🚨=1, 💨=1, 🏆=1, 🚧=1, 💥=1, ✔=4, ☕=1, 💪=2, 🎼=1, 💡=1, 🏀=1, 📚=1, ✨=7, 📅=1, 📌=2, 🏨=1, ☺=6, ‼=2, 📷=5, 🌚=2, 📹=3, 📰=1, 🌍=1, 🌆=1, 🌊=1, ❗=1, 📞=2, 📝=1, 🇺🇸=2, 😘=5, 🌷=1, 😖=2, 😕=2, ❤=42, 😜=3, ♥=7, 😛=1, ♦=1, 🌹=3, 😚=1, 🌸=2, 😙=1, 🐐=2, 😐=2, 😏=11, 😎=2, 😍=12, 🔔=1, 😔=1, 🐓=1, 🌱=1, 😒=8, 🐒=1, 🔑=1, 😑=4, 🔈=1, 😈=1, 😇=2, 😆=2, 🐆=1, 😅=3, 😌=3, 😋=2, 😊=11, 😉=9, 🔉=1, 🌟=2, 😀=4, 🌞=2, ♻=9, 😄=8, 😃=1, 😂=75, 😁=9, 😸=1, 🐶=1, 😶=1, 😵=1, 😻=3, 😰=1, 😮=2, 😭=18, 🔴=2, 😴=3, 😳=1, 🐳=1, 😲=2, 😱=4, 😨=2, 🍄=1, 🔥=4, 😥=4, 😬=2, 🔫=1, 😫=2, ➕=1, 😩=7, 🌿=1, 😠=1, 😞=3, 🔞=1, 😝=2, 🌼=1, 😤=1, 😣=1, 😢=5, 🍁=1, 😡=4, ⚠=1, ➡=4, ⚡=2, 🍺=1, ©=1, 👏=6, 🙏=2, 👎=1, 👍=10, 👓=1, ®=1, 👑=2, 🙈=4, 👇=3, 🍫=1, 🙌=5, 👌=2, 👋=2, 🙋=1, 🙊=2, ▶=2, 👊=1, 👉=2, 👀=3, ⚽=3, ◀=1, 9⃣=1, 🆒=1, 🎉=2, 💘=3, 🎶=2, 💗=2, 🚗=1, 🚖=2, 🎵=1, 💕=6, 💜=2, 💛=7, 💙=8, 💎=1, 🎬=1, 💔=11, 🎲=1, 💓=2, 🎧=2, 💋=5, 💀=4, 💄=1, 💃=1}

Within 5 seconds 😂 emoji was sent 75 times to Twitter!
So why is this solution bad?
Modifying global mutable state from within your reactive stream inevitably leads to race conditions and problems with synchronization.
A much better solution is to aggregate events within the stream itself.
It's a bit mind-bending.
Basically, we turn a stream of individual events into a stream of gradually built aggregation.
Every event is applied to our histogram and passed further downstream.
Look:

```java
final Flux<HashMap<String, Long>> stream = WebClient
         //...see above for missing lines...
        .map(Tracker::codeToEmoji)
        .scan(new HashMap<String, Long>(), (histogram, emoji) -> {
            histogram.merge(emoji, 1L, Math::addExact);
            return histogram;
        });
```

See how a single emoji in the input stream (for example "💖") results in a histogram of "`{💖=1}`" on the output stream:

```text
💖   ->  {💖=1}
🔝   ->  {💖=1, 🔝=1}
😂   ->  {💖=1, 🔝=1, 😂=1}
👀   ->  {💖=1, 👀=1, 🔝=1, 😂=1}
😍   ->  {💖=1, 👀=1, 😍=1, 🔝=1, 😂=1}
😂   ->  {💖=1, 👀=1, 😍=1, 🔝=1, 😂=2}
😀   ->  {💖=1, 😀=1, 👀=1, 😍=1, 🔝=1, 😂=2}
😂   ->  {💖=1, 😀=1, 👀=1, 😍=1, 🔝=1, 😂=3}
```

Notice how each individual emoji is either added to the map or increments existing entry.
Theoretically, the occurrence map (histogram) can grow quite large.
However, the number of different emojis is fixed and not that large ([2666](https://emojipedia.org/stats/) as of this writing).
Now we'd like to find the top 50 emojis - 50 map entries with highest occurrence count.
This can easily be done with JDK 8 `Stream` API:

```java
import java.util.Comparator;
import static java.util.Comparator.comparing;

String topEmojis(HashMap<String, Long> histogram, int max) {
    return histogram
            .entrySet()
            .stream()
            .sorted(comparing(Map.Entry<String, Long>::getValue).reversed())
            .limit(max)
            .map(Map.Entry::getKey)
            .collect(joining(" "));
}
```

In the end we generate a `String` containing top 50 emojis, separated by spaces.
We don't want to see the outcome after each and every emoji.
Instead, let's sample the results 10 times a second:

```java
final Flux<String> stream = WebClient
         //...see above for missing lines...
        .scan(new HashMap<String, Long>(), (histogram, emoji) -> {
            histogram.merge(emoji, 1L, Math::addExact);
            return histogram;
        })
        .map(hist -> topEmojis(hist, 50))
        .sample(Duration.ofMillis(100));
```

The full source code looks as follows:

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static java.util.stream.Collectors.joining;
import static java.util.Comparator.comparing;

public class Tracker {

    private static final Logger log = LoggerFactory.getLogger(Tracker.class);
    
    public static void main(String[] args) throws InterruptedException {
        final Flux<String> stream = WebClient
                .create("http://emojitrack-gostreamer.herokuapp.com")
                .get().uri("/subscribe/eps")
                .retrieve()
                .bodyToFlux(ServerSentEvent.class)
                .flatMap(e -> Mono.justOrEmpty(e.data()))
                .map(x -> (Map<String, Integer>) x)
                .flatMapIterable(Map::entrySet)
                .flatMap(entry -> Flux.just(entry.getKey()).repeat(entry.getValue()))
                .map(Tracker::codeToEmoji)
                .scan(new HashMap<String, Long>(), (histogram, emoji) -> {
                    histogram.merge(emoji, 1L, Math::addExact);
                    return histogram;
                })
                .map(hist -> topEmojis(hist, 50))
                .sample(Duration.ofMillis(100));


        stream.subscribe(sse -> log.info("Received: {}", sse));

        TimeUnit.MINUTES.sleep(10);
    }

    private static String topEmojis(HashMap<String, Long> histogram, int max) {
        return histogram
                .entrySet()
                .stream()
                .sorted(comparing(Map.Entry<String, Long>::getValue).reversed())
                .limit(max)
                .map(Map.Entry::getKey)
                .collect(joining(" "));
    }

    private static String codeToEmoji(String hex) {
        final String[] codes = hex.split("-");
        if (codes.length == 2) {
            return hexToEmoji(codes[0]) + hexToEmoji(codes[1]);
        } else {
            return hexToEmoji(hex);
        }
    }

    private static String hexToEmoji(String hex) {
        return new String(Character.toChars(Integer.parseInt(hex, 16)));
    }

}
```

And the results are adorable:

[![](/assets/img/reactive-emoji-tracker-with-webclient_7/1.png)](/assets/img/reactive-emoji-tracker-with-webclient_7/1.png)

You might think this and the [previous article](http://www.nurkiewicz.com/2018/02/reactive-emoji-tracker-with-webclient.html) aren't very practical.
On the surface, yes.
But we learned a few techniques that can be really valuable when dealing with real streams of data.
Also producing and consuming SSE stream is the easiest way to enable streaming architecture in your ecosystem.
