---
layout: post
title: Strumienie w Javie - cheat sheet
date: '2008-11-02T22:49:00.004+01:00'
author: Tomasz Nurkiewicz
tags:
- commons
modified_time: '2010-04-27T20:06:40.764+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4142482615105917115
blogger_orig_url: https://www.nurkiewicz.com/2008/11/strumienie-w-javie-cheat-sheet.html
---

Jednym z częściej spotykanych przeze mnie problemów w Javie jest ogarnięcie różnych rodzajów strumieni i metod reprezentacji danych.

Jak bowiem poradzić sobie np.
z biblioteką, która wymaga danych w jedynie słusznej tablicy charów a my właśnie dostaliśmy strumień wejściowy z socketu?
\[\*\] Z uwagi na mnogość klas I/O w Javie takich dylematów powstaje niezliczona ilość.
Wyjść jest kilka, z reguły przechodzimy przez kila warstw obiektów (w końcu biblioteka I/O w Javie realizuje *wzorzec chain of responsiility*), w najgorszym wypadku w pętli przepisując dane z jednego miejsca w drugie.

Nawet jeśli znalazłem już konkretne rozwiązanie, i tak z reguły pozostaje niesmak i przeświadczenie, że może dałoby się to zrobić krócej/lepiej/szybciej, niepotrzebne skreślić.
W tym celu przygotowałem [ściągawkę](http://sites.google.com/site/nurkiewicz/Home/zalaczniki/io.pdf), jeśli choć jedna osoba ją sobie wydrukuje i powiesi na biurkiem, będzie to mój sukces :-).

Czekam również na poprawki i propozycje, wciąż wiele ścieżek nie jest uzupełnionych.

\[\*\] - z rysunku dowiadujemy się, że najprościej zrobić to przy pomocy metody toCharArray() klasy [IOUtils](http://commons.apache.org/io/api-release/org/apache/commons/io/IOUtils.html#toCharArray(java.io.InputStream)) z pakietu [Apache Commons IO](http://commons.apache.org/io/).
