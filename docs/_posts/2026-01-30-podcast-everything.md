---
title: "Podcast everything: how to turn any content into podcast feed"
layout: post
description: >
    How to turn YouTube channels, radio stations and 'read later' articles into custom podcasts
---

I've been listening to podcasts for more than a decade.
The podcast app ([Overcast](https://overcast.fm) in my case) is basically my most commonly used software.
But the moment you realize a podcast is just an RSS feed with MP3 links (and no, a YouTube channel is *not* a podcast), you can push much more content into your streaming app.

## Turn any YouTube channel into podcast

Let me reiterate my pet peeve: you don't have a _podcast_ if:

1. You only publish videos on YouTube without audio files under an RSS feed, or
2. You publish audio-only content but only to YouTube, or
3. You publish both as a podcast and as a video channel, but your content without video (audio only) is incomplete.

Now, there's nothing wrong with having a YouTube channel.
I subscribe to plenty of great channels, such as [2swap](https://www.youtube.com/@twoswap), [3Blue1Brown](https://www.youtube.com/@3blue1brown), [Branch Education](https://www.youtube.com/@BranchEducation), [CGPGrey](https://www.youtube.com/@CGPGrey), [Coding With Lewis](https://www.youtube.com/@CodingWithLewis), [Core Dumpped](https://www.youtube.com/@CoreDumpped), [Good Work](https://www.youtube.com/@GoodWorkMB), [Half As Interesting](https://www.youtube.com/@halfasinteresting), [How Money Works](https://www.youtube.com/@HowMoneyWorks), [Kevin Faang](https://www.youtube.com/@kevinfaang), [Kurzgesagt – In a Nutshell](https://www.youtube.com/@kurzgesagt), [Minute Physics](https://www.youtube.com/@MinutePhysics), [Real Engineering](https://www.youtube.com/@RealEngineering), [SteveMould](https://www.youtube.com/@SteveMould), [Stuff Made Here](https://www.youtube.com/@StuffMadeHere), [Veritasium](https://www.youtube.com/@veritasium), [Vsauce](https://www.youtube.com/@Vsauce), [Welch Labs](https://www.youtube.com/@WelchLabsVideo) and [XKCD Whatif](https://www.youtube.com/@xkcd_whatif).

However, there are some channels (like face-to-face interviews) where audio-only is just fine, and hosting it exclusively on YouTube makes no sense.
Unless, of course, you actually want to earn some money from your podcast.
And Spotify, unlike YouTube, doesn't pay podcast creators.
Anyway, back to the topic.

There's this handy open-source tool called [`podsync`](https://github.com/mxpv/podsync) which can turn any YouTube channel into a podcast feed.
Just configure which YouTube channels you like and provide your access token.
Under the hood, the provided Docker container periodically downloads the audio of each new video (using [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)), along with cover image, description, etc.
Then, it creates a valid podcast RSS file with all the metadata.
Now it's enough to expose podsync's HTTP server over the Internet.

### Public access

I run podsync on my local network on some old laptop.
But even if Overcast is connected to the same WiFi, it still downloads the RSS feed through external server.
Thus, my feed is inaccessible.
I use [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/) to expose my laptop running in the local network and with dynamic IP to the Internet.
It works great and it's free.
`podsync` is additionally served behind `nginx`, so that I can route different apps and content (read further).

## Recording online radios using `ffmpeg`

Another use case for a podcast app is online radio stations.
There are some programs which I can't listen to because they are aired when I work or sleep.
Turns out most of these online radio stations provide a stream URL compatible with `ffmpeg`.
I can simply say:

```bash
ffmpeg -y -i "$STREAM_URL" -t 3600 -acodec libmp3lame file.mp3
```

The `$STREAM_URL` is sometimes published by the radio stations officially, sometimes you need to open Developer Tools in your browser.
The `-t 3600` simply says to listen for the stream for an hour and then dump to `file.mp3`.
Now there are two missing pieces: running at the right time and serving.

### Recording at the right time

I run this `ffmpeg` command when the radio program starts.
Of course, `cron` works great here. I just had to remember about `TZ=Europe/Warsaw` so that daylight savings time doesn't break my schedule.
It's that simple.

### Serving as a podcast

At this point I have a bunch of `mp3` files.
Now I need a podcast.
I crated a tiny Python script which basically takes all `mp3` files within a folder and crated an index file, formatted as a proper podcast RSS.
It was a matter of 5 minutes of vibe-coding, so nothing to be particularily excited and worth sharing.
Anyway, now I simply serve that static file, together with MP3 files, through nginx.
Boom, another pseudo-podcast.

## Automatically adding chapters from timestamps in the show description

There's this feature of podcasts called _chapters_.
When the podcast is particularly long, some creators embed named timestamps (_chapters_) into the MP3.
Chapters are then visible in your podcast app (and even my 10 year old car), allowing quick navigation.
Special thanks to creators adding a chapter for ads or sponsored content, so it's easy to skip.

However, some podcast authors don't bother with chapters, but instead put timestamps in the episode description.
To take advantage of these timestamps, I created a tiny proxy server, which rewrites RSS file and MP3s.

1. If the MP3 file already has chapters, skip
2. If the episode description doesn't have timestamps, skip
3. Parse timestamps and add them to MP3 file metadata
4. Store the rewritten MP3 file locally
5. Rewrite the original RSS file to point to local MP3

Then, I simply point my podcast app to read RSS from the proxy server (also served over nginx), rather than the original one.
The proxy server still downloads the MP3 on my behalf and preserves `User-Agent` header of the podcast app, so it doesn't break statistics.

## Turn text articles to audio podcast feed

The next logical step, which I didn't bother to vibe-code yet, is turning any article into a podcast stream.
I have several years worth of articles enqueued I'd like to read one day.
It seems reasonable to turn them into a podcast through some text-to-speech API, like [ElevenLabs](https://mp3chapters.github.io/).
Coincidentally, ElevenLabs already has their Reader app doing that.
But I want to have everything in the podcast app.
Whatever, I didn't bother just yet to implement this.
Probably there's some *hot* AI startup doing exactly that.
Go kids, make money out of such SaaS :-).

## Podcast listening like a pro

Instead of summary, I collected a bunch of tips for more enjoyable podcast listening experience.
So, enjoy!

* Auto-skip intro and outro music, introduction, engagement incentives, ads. Define in/out length for each podcast. For some shows I skip the first 8 minutes (!)

* Speed up! Some podcasts are hard, then I listen at 1.6x. For some I reach 2.5x. Speed up gradually to train your brain

* Some apps have smart speed feature that slows down or speeds up adaptively and cuts silence

* Use headphones with forward button. Skip unwanted in-episode ads and interruptions quickly

* Setup that forward button to exactly 30s. Often ad slots are half a minute long or multiply of that

* Organize podcasts into playlists. With limited time you can listen to the interesting ones first

* Some people also organize playlists by “difficulty”, e.g. how much they have to focus

* Use push notifications when the most enjoyale podcasts arrive

* Forget about built-in iPhone player. I use [Overcast](https://overcast.fm) and it has a ton of great features