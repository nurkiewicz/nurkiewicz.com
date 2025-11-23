---
title: "Best place to commute from in Warsaw: public transit heatmap"
tags: Python, geospatial
layout: post
---

Location, location, location!
That's what the real estate agent will tell you when asked what's the most important factor when choosing the place to live.
When living in a modern, busy city like Warsaw you have two choices: traveling by car or by public transit.
I came up with the idea to automate finding the best place to live in Warsaw, transport-wise.
My plan is to estimate the time it takes to commute from every address in Warsaw to the city center.
I'm focusing on public transport and I'd like to find both hidden gems and transport black holes.
That is, places with great commute time despite the distance and the opposite - respectively.

## Assumptions

1. The city center is Metro Świętokrzyska, the place where the two existing metro lines cross.
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

![Warsaw addresses on a map](/img/public-transit-heatmap-of-warsaw/warsaw.webp)

Fun fact: when zooming in, you can see areas with very dense addresses and other areas with not so many.
Counterintuitively, our data set contains only street numbers, not apartment numbers.
So dense areas are places with single-family houses, whereas sparse areas with blocks of flats.
So less points might actually mean bigger population.
But that's not our point.

![Dense and sparse areas](/img/public-transit-heatmap-of-warsaw/warsaw-zoom.webp)

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

![Heatmap of commute time](/img/public-transit-heatmap-of-warsaw/heatmap-small.png)

Thank you, Captain Obvious!
Living close to the metro lines (Warsaw has two), impacts your commute time.
Can you guess where the lines are located by looking at the green areas?
Spoiler:


