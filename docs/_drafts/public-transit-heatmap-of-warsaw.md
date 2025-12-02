---
title: "Best place to commute from in Warsaw: public transit heatmap"
layout: post
image: /public-transit-heatmap-of-warsaw/hero.png
---

Location, location, location!
That's what the real estate agent will tell you when asked what's the most important factor when choosing the place to live.
When living in a modern, busy city like Warsaw you have two choices: traveling by car or by public transit.
I came up with the idea to automate finding the best place to live in Warsaw, transport-wise.
My plan is to estimate the time it takes to commute from every address in Warsaw to the city center.
I'm focusing on public transport and I'd like to find both hidden gems and transport black holes.
That is, places with great commute time despite the distance and the opposite - respectively.

## Assumptions

1. The city center is [Metro Świętokrzyska](https://maps.app.goo.gl/BboekqFqfNpwjQoM8), the place where the two existing metro lines cross.
2. I use Google Distance API to measure how long it takes to commute, as well as travel by car.
3. I assume Monday morning, 8 AM, as departure time

## Collecting the data

First, I need to figure out all the addresses in Warsaw.
Amazingly, the official data portal of Polish Governemnt provides just that: [in CSV, SHP and GML formats](https://dane.gov.pl/pl/dataset/469).
I chose the least powerful, but still massive CSV dataset.
It containts street name/address, latitude/longitude, etc.
120 thousand records.
SHP file has the exact shape of each lot, which is even better, but I didn't need that.
As a quick sanity check, I plotted all the addresses on a map using [Folium](https://python-visualization.github.io/folium/).

![Warsaw addresses on a map](/assets/img/public-transit-heatmap-of-warsaw/warsaw.webp)

Fun fact: when zooming in, you can see areas with very dense addresses and other areas with not so many.
Counterintuitively, our data set contains only street numbers, not apartment numbers.
So dense areas are places with single-family houses, whereas sparse areas with blocks of flats.
So less points might actually mean bigger population.
But that's not our point.

![Dense and sparse areas](/assets/img/public-transit-heatmap-of-warsaw/warsaw-zoom.webp)

These were just screenshots, but the map of 120k points in Folium is more than 50 MiB, so I'm not linking it here.

Having all the addresses, let's ask Google's API how long it takes from each and every one of them to the city center.
After a few hours and collecting about 4% of the records (I asked for both public transit and car travel time) I realized I exhausted the free plan of Distance API.
$14 I could cover from Patreon (which I don't have), ads (which I don't display) or somehow monetizing data from Google Analytics (which I don't emebed).
Well, I guess I have enough data.
Let's do some vibe-crunching.

## Visualizations

I collected my data points in a simple SQLite3 database with the following schema:

```
sqlite> .mode box
sqlite> select * from travel_info limit 10;
┌───────────────────────────┬────────────┬────────────┬──────────────────┬───────────┬──────────────────┐
│          street           │  latitude  │ longitude  │ transit_duration │ transfers │ car_duration_avg │
├───────────────────────────┼────────────┼────────────┼──────────────────┼───────────┼──────────────────┤
│ ulica Dynarska, 6         │ 52.2586402 │ 20.9166793 │ 34.0             │ 1         │ 26.0             │
│ ulica Ziębicka, 1         │ 52.2431214 │ 20.9204138 │ 27.0             │ 0         │ 23.0             │
│ ulica Karola Miarki, 8    │ 52.2632629 │ 20.9210042 │ 38.0             │ 1         │ 25.0             │
│ ulica Wrocławska, 4A      │ 52.2476407 │ 20.9135746 │ 26.0             │ 1         │ 23.0             │
│ ulica Łęgi, 7             │ 52.2144201 │ 20.886393  │ 42.0             │ 1         │ 24.5             │
│ ulica Sternicza, 80A      │ 52.2208098 │ 20.9051803 │ 38.0             │ 1         │ 22.0             │
│ ulica Posejdona, 3        │ 52.2490873 │ 20.9098983 │ 27.0             │ 1         │ 25.0             │
│ ulica Forsycji, 17        │ 52.3486502 │ 20.9967282 │ 43.0             │ 2         │ 33.0             │
│ ulica Dobka z Oleśnicy, 3 │ 52.3244629 │ 21.0330956 │ 41.0             │ 1         │ 28.5             │
│ ulica Czołowa, 38Z        │ 52.3357846 │ 20.9932044 │ 34.0             │ 1         │ 31.5             │
└───────────────────────────┴────────────┴────────────┴──────────────────┴───────────┴──────────────────┘
```

Luckily, my original data set contained both address and latitude/longitude, so I didn't have to do any geocoding.
Apart from the obvious, I store `transit_duration` (how long it takes to commute by public transit) and `car_duration_avg` (how long it takes to commute by car).
I also keep track of how many transfers are required to commute by public transit.

Now, with a bit of color coding, let's see how long it takes to commute by public transit from every address in Warsaw to the city center:

![Heatmap of commute time](/assets/img/public-transit-heatmap-of-warsaw/heatmap-small.png)

Thank you, Captain Obvious!
Living close to the metro lines (Warsaw has two), impacts your commute time.
Can you guess where the lines are located by looking at the green areas?
Hint: the same map only with points having short commute:

![Heatmap of short commute time](/assets/img/public-transit-heatmap-of-warsaw/heatmap-short-commute.png)

Here's the same map with metro stations laid on top of it.
Two interesting remarks: living close to the metro station doesn't guarantee fast commute.
This especially evident in south of the city (Ursynów/Kabaty district).
But the second observation is even more interesting: what are these seemingly random hotspots, far from the city and metro?

![Heatmap with metro stations overlay](/assets/img/public-transit-heatmap-of-warsaw/heatmap-metro-lines.png)

After closer inspection we see some parts of Warsaw are located close to railway stations.
These underestimated means of transport also significantly improve commute time.
Just see how being close to one such station allows you to reach city center in 30 minutes, despite this is almost the edge of Warsaw.
On the other hand, an address 2 km further east requires almost double that time.

![Piwoniowa 34](/assets/img/public-transit-heatmap-of-warsaw/choszczowka1.png)

![Mehoffera 166K](/assets/img/public-transit-heatmap-of-warsaw/choszczowka2.png)

## Places where public transport is better than a car

While collecting information about commute time via public transport, I also stored travel time by car.
It's tempting to see whether there are places in Warsaw where public transport is advantageous time-wise.
Moreover, you have to park your car somewhere (which is not easy, as in every big city center), so a few extra minutes of travel time are fine.
And don't get me started on the cost of parking and anxiety when sitting in traffic.
Last but not least, travelling by car is often less predictable.
Anyway, here's a map:

![Faster than car](/assets/img/public-transit-heatmap-of-warsaw/faster_than_car.png)

Green color marks addresses where it's faster or slightly slower (up to 10 minutes) to reach city center by public transport.
Once again, we can clearly see the neighborhoods of metro stations, as well as less popular railway stations.

## Number of connections

This becomes even more evident when looking at the number of connections.
For some people having a single means of transport without the need to switch from bus to tram and vice-versa is more important than just travel time.
Basically, if I can get downtown directly without getting out and in mid-way, it's very convenient.
Even, if it's slow.
Here's a map, with green points having direct connection:

![Number of connections](/assets/img/public-transit-heatmap-of-warsaw/transfers.png)

Two interesting observations:

* Living next to the metro station (and railway station) lets you travel directly to the center (once again, subway and railway wins)
* The good news is that the vast majority of the city requires at most one transfer

## Summary

Surely, my amateur analysis has plenty of flaws:

* It's purely based on the commute time between given address and arbitrarily chosen "city center". In practice, many people commute to office districts located outside of the center
* The sample size is just 4%, I didn't analyze all addresses
* There are broken records, typically due to incorrect geocoding or duplicated street names, which I didn't bother to fix.

But, even taking this into account, I think we can make a few, more or less obvious observations:

* Yes, living next to subway station is the best way to get around the city
* Railway stations are highly underrated. They supplement subway very well
* Living outside of these two means of transport, you might be really unlucky, even living relatively close to the center
* Many districts in Warsaw really discourage driving by car as public transport is equally fast
* On the other hand, sometimes even living close 
* In general, the commute time is not proportional to the geographical distance.

I think the biggest takeaway is the fact that in some districts, even further away from the city center, it still makes more sense to travel by bus/tram/metro/railway than by car.
For example, [Bielany](https://en.wikipedia.org/wiki/Bielany), [Targówek](https://en.wikipedia.org/wiki/Targ%C3%B3wek), [Wola](https://en.wikipedia.org/wiki/Wola).
On the other hand, in some districts you are much better of with a car, despite short distance to the center.
E.g. [Ochota](https://en.wikipedia.org/wiki/Ochota) and large parts of [Mokotów](https://en.wikipedia.org/wiki/Mokot%C3%B3w).

![Faster or slower by car, with distrcits](/assets/img/public-transit-heatmap-of-warsaw/faster_than_car_districts.png)

## Source code

Source code (vibe coded, ideal for such experiments) is available on GitHub.
I encourage you to run it under different conditions: different time of day, different target, like office districts, entirely different cities.
Don't forget to share your findings!