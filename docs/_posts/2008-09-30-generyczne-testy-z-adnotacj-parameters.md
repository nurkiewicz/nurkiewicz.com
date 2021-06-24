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

Wydawałoby się, że JUnit jest na tyle prostą biblioteką, iż nic nie jest w stanie nas w niej zaskoczyć. A jednak, odkryłem niedawno ciekawą adnotację @Parameters pozwalającą na generowanie testów z dostarczonych danych. Przykład wiele rozjaśni:<br /><br /><pre class="brush: java; highlight: [1, 8, 12]">@RunWith(Parameterized.class) <br />public class ParamsTest { <br />    private int a;  <br />    private int b;  <br />    private int expected;  <br /><br />    @Parameters  <br />    public static Collection data() {  <br />      return Arrays.asList(new Object[][] { { 1, 1, 2 }, { 1, 2, 3 }, { 4, 6, 9 }, { -2, 2, 0 } });  <br />    }  <br /><br />    public ParamsTest(int a, int b, int expected) {  <br />        this.a = a;  <br />        this.b = b;  <br />        this.expected = expected;  <br />    }  <br /><br />    @Test  <br />        public void sum() {  <br />        assertEquals(expected, a + b);  <br />    }  <br />}</pre><br /><br />Należy zwrócić uwagę na dwie rzeczy:<br />brak konstruktora bezargumentowego; normalnie JUnit nie byłby w stanie uruchomić jakiegokolwiek testu z tekiej klasy<br />metoda data() zwraca kolekcję tablic.<br /><br />JUnit automatycznie dla każdego elementu kolekcji zwróconego przez metodę data() tworzy instancję klasy ParamsTest. A co wstrzykuje do argumentów konstruktora? Oczywiście wartości z tablicy bieżącego elementu kolekcji. Przykładowo pierwszy test: <br /><br /><pre class="brush: java">new ParamsTest(1, 1, 2)</pre><br /><br />Dla każdej instacji klasy ParamsTest zostaną oczywiście wywołane wszystkie testy, zatem nie jeden sum, a cztery: sum[0], sum[1], sum[2], sum[3]. W podanym przykładzie błędem zakończy się test o nazwie sum[2]. Potrafisz powiedzieć czemu?

{% include post-footer.html %}