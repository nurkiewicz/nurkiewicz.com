---
layout: post
title: 'Poor man''s CRUD: jqGrid, REST, AJAX, and Spring MVC in one house'
date: '2011-07-03T19:15:00.001+02:00'
author: Tomasz Nurkiewicz
tags:
- jqgrid
- jquery
- spring mvc
- javascript
- rest
- spring
modified_time: '2011-11-17T19:22:27.232+01:00'
thumbnail: /assets/img/poor-mans-crud-jqgrid-rest-ajax-and/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-981368694888269595
blogger_orig_url: https://www.nurkiewicz.com/2011/07/poor-mans-crud-jqgrid-rest-ajax-and.html
---

More than two years back I wrote an article on how two implement elegant CRUD in [Struts2](http://struts.apache.org/2.2.1.1/).
Actually I had to devote two articles on that subject because the topic was so broad.
Today I have taken much more lightweight and modern approach with a set of popular and well established frameworks and libraries.
Namely, we will use [Spring MVC](http://static.springsource.org/spring/docs/current/spring-framework-reference/html/mvc.html) on the back-end to provide REST interface to our resources, fabulous [jqGrid](http://www.trirand.com/blog) plugin for [jQuery](http://jquery.com/) to render tabular grids (and much more!)
and we will wire up everything with a pinch of JavaScript and AJAX.

Back-end is actually the least interesting part of this showcase, it could have been implemented using any server-side technology capable of handling RESTful requests, probably JAX-RS should now be considered standard in this field.
I have chosen Spring MVC without any good reason, but it's also not a bad choice for this task.
We will expose CRUD operations over REST interface; the list of [best selling books in history](http://en.wikipedia.org/wiki/List_of_best-selling_books) will be our domain model (can you guess who is on the podium?)

```java

@Controller
@RequestMapping(value = "/book")
public class BookController {

  private final Map<Integer, Book> books = new ConcurrentSkipListMap<Integer, Book>();

  @RequestMapping(value = "/{id}", method = GET)
  public @ResponseBody Book read(@PathVariable("id") int id) {
    return books.get(id);
  }

  @RequestMapping(method = GET)
  public @ResponseBody Page<Book> listBooks(
      @RequestParam(value = "page", required = false, defaultValue = "1") int page,
      @RequestParam(value = "max", required = false, defaultValue = "20") int max) {
    final ArrayList<Book> booksList = new ArrayList<Book>(books.values());
    final int startIdx = (page - 1) * max;
    final int endIdx = Math.min(startIdx + max, books.size());
    return new Page<Book>(booksList.subList(startIdx, endIdx), page, max, books.size());
  }
}
```

Few things need explanation.
First of all **for the purposes of this simple showcase** I haven't used any database, all the books are stored in an in-memory map inside a controller.
Forgive me.
Second issue is more subtle.
Since there seems to be [no agreement](http://stackoverflow.com/questions/924472) on how to handle paging with RESTful web services, I used simple query parameters.
You may find it ugly, but I find abusing Accept-Ranges and Range headers together with 206 HTTP response code even uglier.

Last notable detail is the Page\<Book\> wrapper class:

```java

@XmlRootElement
public class Page<T> {

  private List<T> rows;

  private int page;
  private int max;
  private int total;

  //...

}
```

I could have return raw list (or, more precisely, requested part of the list), but I also need a way to provide convenient metadata like total number of records to the view layer, not to mention some difficulties while marshalling/unmarshalling raw lists.

We are now ready to start our application and do a little test drive with curl:

```xml

<!-- $ curl -v "http://localhost:8080/books/rest/book?page=1&max=2" -->

<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<page>
  <total>43</total>
  <page>1</page>
  <max>3</max>
  <rows xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="book">
    <author>Charles Dickens</author>
    <available>true</available>
    <cover>PAPERBACK</cover>
    <id>1</id>
    <publishedYear>1859</publishedYear>
    <title>A Tale of Two Cities</title>
  </rows>
  <rows xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="book">
    <author>J. R. R. Tolkien</author>
    <available>true</available>
    <cover>HARDCOVER</cover>
    <id>2</id>
    <publishedYear>1954</publishedYear>
    <title>The Lord of the Rings</title>
  </rows>
  <rows xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="book">
    <author>J. R. R. Tolkien</author>
    <available>true</available>
    <cover>PAPERBACK</cover>
    <id>3</id>
    <publishedYear>1937</publishedYear>
    <title>The Hobbit</title>
  </rows>
</page>
```

Response type defaults to XML if none is specified but if we add [Jackson](http://jackson.codehaus.org/) library to the CLASSPATH, Spring will pick it up and enable us to use JSON as well:

```javascript

// $ curl -v -H "Accept: application/json" "http://localhost:8080/books/rest/book?page=1&max=3"

{
    "total":43,
    "max":3,
    "page":1,
    "rows":[
        {
            "id":1,
            "available":true,
            "author":"Charles Dickens",
            "title":"A Tale of Two Cities",
            "publishedYear":1859,
            "cover":"PAPERBACK",
            "comments":null
        },
        {
            "id":2,
            "available":true,
            "author":"J. R. R. Tolkien",
            "title":"The Lord of the Rings",
            "publishedYear":1954,
            "cover":"HARDCOVER",
            "comments":null
        },
        {
            "id":3,
            "available":true,
            "author":"J. R. R. Tolkien",
            "title":"The Hobbit",
            "publishedYear":1937,
            "cover":"PAPERBACK",
            "comments":null
        }
    ]
}
```

Nice, now we can work on the front-end, hopefully not making our hands too dirty.
With regards to HTML markup, this is all we need, seriously:

```html

<table id="grid"></table>
<div id="pager"></div>
```

Keep in mind that we will implement all CRUD operations, but still, this is all we need.
No more HTML.
Rest of the magic happens thanks to marvellous jqGrid library.
Here is a basic setup:

```javascript

$("#grid")
    .jqGrid({
      url:'rest/book',
      colModel:[
        {name:'id', label: 'ID', formatter:'integer', width: 40},
        {name:'title', label: 'Title', width: 300},
        {name:'author', label: 'Author', width: 200},
        {name:'publishedYear', label: 'Published year', width: 80, align: 'center'},
        {name:'available', label: 'Available', formatter: 'checkbox', width: 46, align: 'center'}
      ],
      caption: "Books",
      pager : '#pager',
      height: 'auto'
    })
    .navGrid('#pager', {edit:false,add:false,del:false, search: false});
```

Technically, this is all we need.
URL to fetch the data, pointing to our controller (jqGrid will perform all the AJAX magic for us) and the data model (you may recognize book fields and their descriptions).
However, since jqGrid is highly customizable, I applied few tweaks to make the grid look a bit better.
Also I didn't like suggested names of metadata, for instance total field returned from the server is suppose to be the total number of pages, not records – highly counter-intuitive.
Here are my tweaked options:

```javascript

$.extend($.jgrid.defaults, {
  datatype: 'json',
  jsonReader : {
    repeatitems:false,
    total: function(result) {
      //Total number of pages
      return Math.ceil(result.total / result.max);
    },
    records: function(result) {
      //Total number of records
      return result.total;
    }
  },
  prmNames: {rows: 'max', search: null},
  height: 'auto',
  viewrecords: true,
  rowList: [10, 20, 50, 100],
  altRows: true,
  loadError: function(xhr, status, error) {
    alert(error);
  }
  });
```

Eager to see the results?
Here is a browser screenshot:

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/1.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/1.png)

Good looking, with customizable paging, lightweight refreshing...
And our hands are still relatively clean!
But I promised CRUD...
If you were careful, you have probably noticed few navGrid attributes, dying to be turned on:

```javascript

var URL = 'rest/book';
var options = {
  url: URL,
  editurl: URL,
  colModel:[
    {
      name:'id', label: 'ID',
      formatter:'integer',
      width: 40,
      editable: true,
      editoptions: {disabled: true, size:5}
    },
    {
      name:'title',
      label: 'Title',
      width: 300,
      editable: true,
      editrules: {required: true}
    },
    {
      name:'author',
      label: 'Author',
      width: 200,
      editable: true,
      editrules: {required: true}
    },
    {
      name:'cover',
      label: 'Cover',
      hidden: true,
      editable: true,
      edittype: 'select',
      editrules: {edithidden:true},
      editoptions: {
        value: {'PAPERBACK': 'paperback', 'HARDCOVER': 'hardcover', 'DUST_JACKET': 'dust jacket'}
      }
    },
    {
      name:'publishedYear',
      label: 'Published year',
      width: 80,
      align: 'center',
      editable: true,
      editrules: {required: true, integer: true},
      editoptions: {size:5, maxlength: 4}
    },
    {
      name:'available',
      label: 'Available',
      formatter: 'checkbox',
      width: 46,
      align: 'center',
      editable: true,
      edittype: 'checkbox',
      editoptions: {value:"true:false"}
    },
    {
      name:'comments',
      label: 'Comments',
      hidden: true,
      editable: true,
      edittype: 'textarea',
      editrules: {edithidden:true}
    }
  ],
  caption: "Books",
  pager : '#pager',
  height: 'auto'
};
$("#grid")
    .jqGrid(options)
    .navGrid('#pager', {edit:true,add:true,del:true, search: false});
```

The configuration is getting dangerously verbose, but there's nothing complicated out there – for each field we have added few additional attributes controlling how this field should be treated in edit mode.
This includes what type of HTML input should represent it, validation rules, visibility, etc. But honestly, I believe it was worth it:

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/2.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/2.png)

This nicely looking edit window has been fully generated by jqGrid based on our edit options mentioned above, including validation logic.
We can make some of the fields visible in the grid hidden/inactive in edit dialog (like id) and vice-versa (cover and comments are not present in the grid, however you can modify them).
Also notice few new icons visible in bottom-left corner of the grid.
Adding and deleting is possible as well – and we haven't written a single line of HTML/JSP/JavaScript (excluding jqGrid configuration object).

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/3.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/3.png)

Of course we all know that [*The User Interface Is The Application*](http://www.codinghorror.com/blog/2005/08/the-user-interface-is-the-application.html), and our interface is pretty good, however sometimes we really want a beautiful **and** working application.
And currently the latter requirement is our Achilles' heel.
Not because the back-end isn't ready, this is rather trivial:

```java

@Controller
@RequestMapping(value = "/book")
public class BookController {

  private final Map<Integer, Book> books = new ConcurrentSkipListMap<Integer, Book>();

  @RequestMapping(value = "/{id}", method = GET)
  public @ResponseBody Book read(@PathVariable("id") int id) {
    //...
  }

  @RequestMapping(method = GET)
  public
  @ResponseBody
  Page<Book> listBooks(
      @RequestParam(value = "page", required = false, defaultValue = "1") int page,
      @RequestParam(value = "max", required = false, defaultValue = "20") int max) {
    //...
  }

  @RequestMapping(value = "/{id}", method = PUT)
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void updateBook(@PathVariable("id") int id, @RequestBody Book book) {
    //...
  }

  @RequestMapping(method = POST)
  public ResponseEntity<String> createBook(HttpServletRequest request, @RequestBody Book book) {
    //...
  }

  @RequestMapping(value = "/{id}", method = DELETE)
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void deleteBook(@PathVariable("id") int id) {
    //...
  }

}
```

Server-side is ready, but when it comes to data manipulation on the client-side, jqGrid reveals its dirty secret – all the traffic to the server is sent using POST like this:

```text

Content-Type: application/x-www-form-urlencoded in the following format:

id=&title=And+Then+There+Were+None&author=Agatha+Christie&cover=PAPERBACK&publishedYear=1939&available=true&comments=&oper=add
```

The last attribute (oper=add) is crucial.
Not really idiomatic REST, don't you think?
If we could only use POST/PUT/DELETE appropriately and serialize data using JSON or XML...
Modifying my server so that it is compliant with some JavaScript library (no matter how cool it is), seems like a last resort.
Thankfully, everything can be [customized](http://www.trirand.com/jqgridwiki/doku.php?id=wiki:jqgriddocs) with a moderate amount of work.

```javascript

$.extend($.jgrid.edit, {
      ajaxEditOptions: { contentType: "application/json" },
      mtype: 'PUT',
      serializeEditData: function(data) {
        delete data.oper;
        return JSON.stringify(data);
      }
    });
$.extend($.jgrid.del, {
      mtype: 'DELETE',
      serializeDelData: function() {
        return "";
      }
    });

var URL = 'rest/book';
var options = {
  url: URL,
  //...
}

var editOptions = {
  onclickSubmit: function(params, postdata) {
    params.url = URL + '/' + postdata.id;
  }
};
var addOptions = {mtype: "POST"};
var delOptions = {
  onclickSubmit: function(params, postdata) {
    params.url = URL + '/' + postdata;
  }
};


$("#grid")
    .jqGrid(options)
    .navGrid('#pager',
    {}, //options
    editOptions,
    addOptions,
    delOptions,
    {} // search options
);
```

We have customized HTTP method per operation, serialization is handled using JSON and finally URLs for edit and delete operations are now suffixed with /*record_id*.
Now it not only looks, it works!
Look at the browser interaction with the server (note different HTTP methods and URLs):

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/4.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/4.png)

Here is an example of creating a new resource on browser side:

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/5.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/5.png)

To follow REST principles as closely as possible I return 201 Created response code together with Location header pointing to newly created resource.
As you can see data is now being sent to the server in JSON format.

To summarize, such an approach has plenty of advantages:

- GUI is very responsive, page appears instantly (it can be a static resource served from [CDN](http://en.wikipedia.org/wiki/Content_delivery_network)), while data is loaded asynchronously via AJAX in lightweight JSON format
- We get CRUD operations for free
- REST interface for other systems is also for free
  Compare this with any web framework out there.
  And did I mention about this little cherry on our JavaScript frosting: jqGrid is fully compliant with [jQuery UI themes](http://jqueryui.com/themeroller) and also supports internationalization.
  Here is the same application with changed theme and language:

[![](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/6.png)](/assets/img/poor-mans-crud-jqgrid-rest-ajax-and/6.png)

Full [source code](https://github.com/nurkiewicz/books) is available on [my](https://github.com/nurkiewicz) GitHub account.
The application is self contained, just build it and deploy it to some servlet container.
