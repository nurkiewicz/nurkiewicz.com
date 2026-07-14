---
layout: post
title: SCJD - Sun Certified Java Developer zdobyty!
date: '2009-01-07T20:51:00.009+01:00'
author: Tomasz Nurkiewicz
tags:
- certyfikacja
- sun
modified_time: '2009-03-28T22:21:15.593+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3900536710211187817
blogger_orig_url: https://www.nurkiewicz.com/2009/01/scjd-sun-certified-java-developer.html
---

> 

Bez zbędnych wstępów, chciałem pochwalić się zdanym certyfikatem Sun Certified Java Developer (SCJD, [CX-310-027](http://www.sun.com/training/certification/java/scjd.xml)), którego przyjemność zdawania umożliwiła mi moja ulubiona [firma](https://www.javart.com.pl/) :-).
Przyjemność tym większa, że wynik bardzo pozytywnie mnie zaskoczył (dodam, że próg wynosi 320/400):

Section

Max

Actual

General Considerations:

100

90

Documentation:

70

70

Object-Oriented Design:

30

30

GUI:

40

31

Locking:

80

80

Data Store:

40

40

Network Server:

40

40

Total:

400

381

Ale nie o wynikach chciałem napisać, a podzielić się wrażeniami.
Ponieważ szczegóły zadanie są tajne/poufne :-) - raczej ogólnymi.

Przede wszystkim certyfikat, złożony z zadania projektowego i eseju, raczej nie nauczy Was super-nowego-frameworku, biblioteki czy technologii.
Swing + RMI i zakaz korzystania z jakichkolwiek zewnętrznych bibliotek.

Ale chyba nie o to chodzi - ten certyfikat to głównie szlifowanie i sprawdzanie "miękkich" umiejętności programistycznych.
Kod musi być dobrze napisany, udokumentowany, korzystać z całej palety wzorców projektowych.
Trzeba wykazać się znajomością podstawowego API (strumienie, wątki, sieć), ale żadnego EJB, serwletów, JPA.
I w tej materii wypada bardzo dobrze - sporo się nauczyłem na płaszczyźnie projektowania (z głównym naciskiem na czytelność, nawet kosztem wydajności), pisanie Javadoków weszło mi w krew (w projekcie każdy publiczny element kodu musi być udokumentowany).

Jeśli zatem chcecie sprawdzić umięjętności programistyczne jako takie, a nie znajomość takiego czy innego API, SCJD jest bardzo dobrym wyborem.
Napisanie projektu sprawdzonego czujnym okiem egzaminatorów z Suna (jedyny obok [SCEA](http://www.sun.com/training/certification/java/scea.xml) certyfikat wymagający pisania żywego kodu) daje wiele satysfakcji, zwłaszcza przy pozytywnym wyniku.
Sam temat projektu też jest dość ciekawy - z reguły nierelacyjna baza danych na wielodostępnym serwerze i klient w Swingu komunikujący się po RMI lub socketach.

Na koniec kilka uwag technicznych:

- maven sprawdził się znakomicie w tym dość specyficznym projekcie.
  Budował JAR, generował Javadoki, uruchamiał testy, zarządzał zależnościami testowymi (innych mieć nie można) i budował za pomocą assembly wynikowy artefakt ze spakowanym programem, dokumentacją i źródłami.
- Dokumentację użytkownika dostarczyłem w formacie HTML generując ją również mavenem z DocBooka za pomocą [docbkx-maven-plugin](http://docs.codehaus.org/display/MAVENUSER/Docbkx+Maven+Plugin).
- Formatowanie kodu w Eclipse Ganymede poradziło sobie z momentami zakręconymi standardami Suna (np.
  "Four spaces should be used as the unit of indentation.
  The exact construction of the indentation (spaces vs. tabs) is unspecified.
  Tabs must be set exactly every 8 spaces (not 4)").
- Przed napisaniem projektu przeczytałem (czasem kartkując) [SCJD Exam with J2SE 5](http://www.amazon.com/SCJD-Exam-Second-Experts-Voice/dp/1590595165) (autorstwa Andrew Monkhouse i Terry Camerlengo).
  Raczej warto.
- Całość (od pierwszej linijki kodu do ostatniej linijki docbookowego XMLa) zajęła mi miesiąc, w sumie ponad 10 KLOC.

To tyle, szczerze mogę polecić ten certyfikat, chociaż do najłatwiejszych (ani najtańszych) nie należy.
