---
layout: post
title: Generyczne testy z adnotacją Parameters w JUnit 4
date: '2008-09-30T22:02:00.002+02:00'
author: Tomasz Nurkiewicz
tags:
- testing
- junit
modified_time: '2009-12-19T15:54:53.248+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5094640656588403240
blogger_orig_url: https://www.nurkiewicz.com/2008/09/generyczne-testy-z-adnotacj-parameters.html
---

Wydawałoby się, że JUnit jest na tyle prostą biblioteką, iż nic nie jest w stanie nas w niej zaskoczyć.
A jednak, odkryłem niedawno ciekawą adnotację @Parameters pozwalającą na generowanie testów z dostarczonych danych.
Przykład wiele rozjaśni:

```java
@RunWith(Parameterized.class) 
public class ParamsTest { 
    private int a;  
    private int b;  
    private int expected;  

    @Parameters  
    public static Collection data() {  
      return Arrays.asList(new Object[][] { { 1, 1, 2 }, { 1, 2, 3 }, { 4, 6, 9 }, { -2, 2, 0 } });  
    }  

    public ParamsTest(int a, int b, int expected) {  
        this.a = a;  
        this.b = b;  
        this.expected = expected;  
    }  

    @Test  
        public void sum() {  
        assertEquals(expected, a + b);  
    }  
}
```

Należy zwrócić uwagę na dwie rzeczy:
brak konstruktora bezargumentowego; normalnie JUnit nie byłby w stanie uruchomić jakiegokolwiek testu z tekiej klasy
metoda data() zwraca kolekcję tablic.

JUnit automatycznie dla każdego elementu kolekcji zwróconego przez metodę data() tworzy instancję klasy ParamsTest.
A co wstrzykuje do argumentów konstruktora?
Oczywiście wartości z tablicy bieżącego elementu kolekcji.
Przykładowo pierwszy test:

```java
new ParamsTest(1, 1, 2)
```

Dla każdej instacji klasy ParamsTest zostaną oczywiście wywołane wszystkie testy, zatem nie jeden sum, a cztery: sum\[0\], sum\[1\], sum\[2\], sum\[3\].
W podanym przykładzie błędem zakończy się test o nazwie sum\[2\].
Potrafisz powiedzieć czemu?
