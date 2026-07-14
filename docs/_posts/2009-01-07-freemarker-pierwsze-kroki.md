---
layout: post
title: Freemarker - pierwsze kroki
date: '2009-01-07T20:12:00.003+01:00'
author: Tomasz Nurkiewicz
tags:
- freemarker
modified_time: '2009-08-14T00:04:48.594+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5686563089048014206
blogger_orig_url: https://www.nurkiewicz.com/2009/01/freemarker-pierwsze-kroki.html
---

Postanowiłem sporządzić krótki tutorial z jednym prostym przykładem pokazującym podstawowe możliwości [Freemarkera](http://freemarker.sourceforge.net/).
Wbrew pozorom nie stanąłem przed koniecznością migracji plików JSP na Freemarker, a użyłem tej biblioteki w klasycznej, konsolowej aplikacji Java SE.
Jak się okazało, sprawdziła się znakomicie.

Bez zbędnego lania wody - Freemarker jest procesorem, który na wejściu otrzymuje model (zestaw obiektów Java) + szablon, a na wyjściu produkuje dokument będący szablonem uzupełnionym o odpowiednio sformatowane dane z modelu.
Problem polega na konwersji obiektu Java do reprezentacji tekstowej.
By być precyzyjnym, chodziło o translację następującego JavaBeanu:

```
package com.blogspot.nurkiewicz;

import java.util.List;

public class Procedure {

    private boolean returns;

    private String name;

    private List<String> args;

    /* konstruktory, gettery i settery*/

}
```

do kodu w języku Java.
Dla przykładowych wartości właściwości: name="count", args=\[x, y, size\], returns=true, powinniśmy otrzymać następujący tekst:

```
public double subCount(double x, double y, double size);
```

Zacznijmy zatem od przygotowania środowiska.
Podstawowym obiektem Freemarkera jest klasa [Template](http://freemarker.sourceforge.net/docs/api/freemarker/template/Template.html).
Co prawda dokumentacja poleca tworzenie jej instancji za pomocą klasy [Configuration](http://freemarker.sourceforge.net/docs/api/freemarker/template/Configuration.html), jednak ponieważ domyślnie ma ona dość ubogie API (można ładować szablony jedynie z plików, i to bez przeszukiwania CLASSPATH), utworzymy obiekt klasy Template bezpośrednio:

```
Template template = new Template(null,
    new InputStreamReader(Main.class.getResourceAsStream("procedure.ftl")),
    new Configuration());
```

Kod ten został umieszczony w klasie com.blogspot.nurkiewicz.Main, zatem plik procedure.ftl będzie szukany w katalogu src/main/resource/com/blogspot/nurkiewicz.

Posiadając obiekt template możemy przystąpić do zasilenia go modelem; wystarczy prosta mapa:

```
Map<String, Object> model = new HashMap<String, Object>();
final Procedure procedure = new Procedure(true, "count", Arrays.asList("x", "y", "size"));
model.put("proc", procedure);
```

Jak widać umieściliśmy w modelu, pod kluczem proc, instancję naszej klasy Procedure.
Oznacza to, że w naszym szablonie będziemy mogli otrzymać wartości z tego obiektu posługując się prefiksem proc.
Spróbujmy - przypominam, że plik procedure.ftl zawiera treść szablonu:

```
public double ${proc.name}(double ${proc.args[0]}, double ${proc.args[1]}, double ${proc.args[2]});
```

\${proc.name} jest jednym z odwołań do modelu - w tym wypadku do właściwości name obiektu pod kluczem proc (czyli Freemarker wywoła Procedure.getName() na instancji klasy Procedure).
Z kolei \${proc.args\[0\]} spowoduje javowe odwołanie getArgs().get(0).
Jasne.

Do uruchomienia przykładu potrzebujemy jeszcze właściwego przetworzenia szablonu wraz z modelem oraz zdefiniowania dokąd ma trafić wynik (w naszym wypadku standardowe wyjście):

```
template.process(model, new OutputStreamWriter(System.out));
```

I wynik programu, nieco odbiegający od oczekiwań:

```
public double count(double x, double y, double size);
```

Nie dość, że brakuje prefiksu sub przed nazwą metody, to jeszcze zahardkodowaliśmy długość listy args oraz nie sprawdzamy właściwości returns, wartość której determinuje, czy metoda zwraca double czy void.
Zacznijmy od tego.
Freemarker udostępnia proste wyrażenia warunkowe, zwróćcie uwagę, że nie ma już potrzeby korzystania ze znaku dolara i nawiasów klamrowych:

```
public <#if proc.returns>double<#else>void</#if>
    ${proc.name}(${proc.args[0]}, ${proc.args[1]}, ${proc.args[2]});
```

Dla lepszej czytelności rozbiję szablon na linijki.
Wyrażenie chyba oczywiste, Freemarker domyśla się, że trzeba wywołać metodę Procedure.isReturns().
Jednak zamiast złożonego warunku możemy zwyczajnie napisać:

```
${proc.returns?string("double", "void")}
```

co przypomina znany z wielu języków, także Javy, trójargumentowy operator warunkowy ?: .

Większym problemem jest nazwa metody - samo dodanie prefiksu nie wystarczy, ponieważ dodatkowo, zgodnie z notacją camel case, trzeba rozpocząć dostarczoną nazwę metody od wielkiej litery.
Szczęśliwie, Freemarker potrafi sobie poradzić z tak prostym zabiegiem edycyjnym:

```
public ${proc.returns?string("double", "void")} sub${proc.name?cap_first}(
    ${proc.args[0]}, ${proc.args[1]}, ${proc.args[2]}
);
```

cap_first od capitalize first letter, Freemarker umożliwia nam jeszcze wiele innych transformacji, takich jak substring, dopełnianie czy obcinanie białych znaków.
Tymczasem nasz wynik:

```
public double subCount(
    x, y, size
);
```

Została tylko nieszczęsna lista.
Po pierwsze musimy umieć iterować po liście dowolnej długości, po drugie ostatni element nie może się kończyć przecinkiem.
Użyjemy w tym celu dyrektywy \<#list\> (istnieje również uboższa wersja: \<#foreach\>):

```
<#list proc.args as arg>
    double ${arg},
</#list>);
```

Znowu dość prosty kod: dla każdego elementu z kolekcji proc.args (w każdej iteracji dany element jest widoczny pod kluczem arg) zostanie wydrukowana zawartość dyrektywy \<#list\>, czyli w naszym wypadku "double \${arg},".
Efekt do przewidzenia, ale co zrobić z przecinkiem po ostatniej iteracji?
Otóż dyrektywa \<#list\> wprowadza kilka dodatkowych zmiennych, m.in.
swojsko brzmiącą arg_has_next.
Czy trzeba tłumaczyć, że w każdej iteracji z wyjątkiem ostatniej przybiera ona wartość true?
I czy muszę pokazywać pełny kod szablonu?

```
public ${proc.returns?string("double", "void")} sub${proc.name?cap_first}(
<#list proc.args as arg>
    double ${arg}<#if arg_has_next>, </#if>
</#list>);
```

I tak oto Freemarker pomógł mi skrócić kod w Javie do zaledwie jednej linijki wykonującej odpowiedni szablon, zamknąłem widok i odizolowałem od modelu.
A co najważniejsze, usunąłem pachnącą amatorką, zamotaną pętlę ze StringBuilderem, warunkami i tekstem przeplecionym z kodem w Javie - i chyba o to chodzi?

Mam nadzieję, że udało mi się przybliżyć składnię Freemarkera i zachęcić do stosowania tego narzędzia wszędzie tam, gdzie trzeba zamienić dane na tekst.
Narzędzie to może również z powodzeniem zastępować XSLT: [FreeMarker vs. XSLT](http://freemarker.org/fmVsXSLT.html).

[Pełen kod źródłowy programu](http://sites.google.com/site/nurkiewicz/Home/zalaczniki/freemarker-test.zip), maven friendly, 3,3 KiB.
