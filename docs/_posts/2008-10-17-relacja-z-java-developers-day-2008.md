---
layout: post
title: Relacja z Java Developers' Day 2008
date: '2008-10-17T10:44:00.007+02:00'
author: Tomasz Nurkiewicz
tags:
- conferences
modified_time: '2009-10-18T10:53:45.724+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2702725474342073917
blogger_orig_url: https://www.nurkiewicz.com/2008/10/relacja-z-java-developers-day-2008.html
---

Dzięki uprzejmości mojej [firmy](http://www.javart.com.pl/) miałem w tym roku niewątpliwą przyjemność uczestniczyć w **Java Developers' Day 2008** w Krakowie.
Krótko o prelekcjach, których miałem możliwość wysłuchać:

Na początek keynote w wykonaniu **Teda Newarda**.
To, co miało być pogadanką o wszystkim i o niczym gościa z USA było pasjonującą podróżą po językach programowania od lat 60 do niedalekiej przyszłości.
Ogromne pokłady humoru i kilka mniej lub bardziej kontrowersyjnych opinii o relacjach między światem akademickim i komercyjnym.
Na koniec usłyszeliśmy tezę, że "*God doesn't think in objects*" z żartobliwym autoripostą "*He thinks in Ruby*" :-).
Mnóstwo ciekawostek i humoru rodem z za oceanu.
Słuchało się tego z przyjemnością.\*

Potem było **JAIN SLEE** ustami **Jana Pieczykolana**.
To mógł być dobry i ciekawy wykład, ale...
Niestety mam wrażenie, że gdyby prelegent nie skupił się tak mocno na promocji własnej firmy, starczyłoby mu czasu na ciekawą demonstrację.
A tak - było po prostu nudno.

Na szczęście potem było już dużo lepiej.
**Manik Surtani** ze stajni JBoss opowiadał o **JBoss Cache**.
Oczywiście najciekawsza była konfrontacja tego produktu z Ehcache, głównie w kontekście pracy rozproszonej.
Było nieco teorii oraz wyniki testów wydajnościowych.
Twórcy Jboss Cache sami napisali narzędzie do testów a potem przetestowali nim własny produkt i Ehcache - zgadnijcie, jaki był wynik?
:-) Oczywiście najlepiej sprawdzić samemu, np.
podmieniając implementację cache w Hibernate (JBoss udostępnia odpowiedni provider, o co nie omieszkałem zapytać) i testując zmiany wydajności naszych własnych aplikacji.
Warto zapamiętać: "Measure.
Don’t guess" oraz porównanie, że w dzisiejszych czasach na potrzeby cache RAM jest naszym dyskiem twardym a dysk twardy pełni już tylko rolę taśmy.

Szczepan Faber opowiadający o napisanej przez siebie bibliotece Mockito w prelekcji Wejście szpiega zapewne zostanie zapamiętany z porównania dmuchanej...
"zabawki" do obiektów typu mock.
Bardzo ciekawy wykład, podczas którego można było dowiedzieć się wiele o filozofii testowania w ogólności, dobrych praktykach i doświadczeniach prelegenta.
Biblioteka Mockito, chociaż opisana klarownie, stanowiła jedynie dodatek do tak szeroko ujętego temat.
Na pewno autorowi należy się pochwała za dużą dawkę luzu i humoru oraz krytyczne i obiektywne podejście do prezentowanego tematu.
Z całą pewnością zachęcił mnie do dalszego zgłębiania koncepcji mocków.

Z niecierpliwością czekałem na prelekcję o Envers, chociaż większość osób chyba wybrała J2EE 6.
Adam Warski, znowu z JBoss, prezentował na przykładach bardzo ciekawą bibliotekę swojego autorstwa służącą do zautomatyzowanego wersjonowania encji w Hibernate/JPA.
Jeśli chodzi o funkcjonalność, oprócz kilku jeszcze nie zaimplementowanych funkcji, Envers jest rozwiązaniem znakomitym.
Chętnie ujrzałbym taki mechanizm w ramach samej specyfikacji JPA.
Niestety odniosłem wrażenie, że nie jest to jeszcze projekt na tyle dojrzały, bo zaufać mu w środowisku produkcyjnym.
Zdaje się, że Adam jest jedynym developerem, co z jednej strony budzi wiele szacunku, jednak aby uwierzyć tak ważnej bibliotece, życzyłbym sobie jednak większej linii "wsparcia".
Niemniej jednak z zainteresowaniem i wypiekami na twarzy będę oczekiwał postępów jego prac.

Wykład o platformie Eclipse 4 autorstwa Szymona Brandysa mnie nieco rozczarował.
Chyba spodziewałem się czegoś bardziej spektakularnego, wczesnego podejrzenia nowych funkcjonalności, jakie planują programiści IBM, rewolucyjnych koncepcji, etc. Zamiast tego było nieco zbyt ogólnikowo.

Keynote w wykonaniu Neala Forda przypominał film na kanale Discovery, którego on był tylko narratorem.
Neal opowiadał o domain specific languages.
Muszę przyznać, że Amerykanie znacznie lepiej opanowali sztukę publicznych wystąpień i oba keynoty wypadły świetnie.
Podczas tego drugiego usłyszeliśmy kilka krytycznych słów o dzisiejszych językach programowania, muszę pozazdrościć niektórym tak obiektywnego spojrzenia oraz otwartego umysłu.
Ucieszyły mnie również wzmianki o ANTLR (również przez Teda), narzędzia szczególnie mi bliskiego.

I na koniec Jacek Laskowski ze swoją prezentacją o OSGi i Spring DM.
Największe gratulacje za to, że przez cały dzień tylko u Jacka widziałem demonstrację na żywym kodzie, a nie tylko suche prezentacje.
I powiem szczerze, że wreszcie zrozumiałem o co w tym całym OSGi chodzi, jak to działa i czemu na świecie tak wiele się o tej technologii teraz mówi.
Narzędzie jawiące mi się jako Święty Graal systemów opartych o Javę (o ogromnej mocy, ale jednocześnie niepoznany i enigmatyczny) okazało się konkretną, nowatorską platformą uruchomieniową.
Również gratulacje za trafnie dobrane przykłady, ukazujące sedno tego rozwiązania.

Tak oto zakończyła się dla mnie konferencja (co gorsza musiałem opuścić wykład o OSGi, na dodatek rozpoczęty z opóźnieniem).
Warto dodać, że duże imiennie identyfikatory na pewno sprzyjały integracji wśród uczestników (niestety było zdecydowanie zbyt mało czasu na kuluarowe rozmowy, agenda była bardzo napięta), ale jeszcze lepszym pomysłem był pendrive w prezencie z zapisanymi wszystkimi prezentacjami.
Gratulacje dla organizatorów, jeśli się uda, za rok również postaram się dotrzeć do Krakowa.

\* Wiecie, co oznacza skrót "WHISKEY"?
Według Teda jest to opis popularnej metodologii tworzenia oprogramowania: *Why the Hell Isn't Somebody Koding Everything Yet.*
:-)
