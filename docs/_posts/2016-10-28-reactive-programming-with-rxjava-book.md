---
layout: post
title: Reactive Programming with RxJava book published
date: '2016-10-28T12:29:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- books
- rxjava
modified_time: '2016-10-28T12:29:14.721+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4345391673007735507
blogger_orig_url: https://www.nurkiewicz.com/2016/10/reactive-programming-with-rxjava-book.html
image: /assets/img/reactive-programming-with-rxjava-book/hero.jpg
---

"**Reactive Programming with RxJava: Creating Asynchronous, Event-Based Applications**" book was finally published on paper.
More than a year of hard work resulted in almost 350 pages packed with RxJava and touching various technologies like Android, Camel, NoSQL, Hystrix and more.
It's available as an ebook and in paperback at [official O'Reilly store](http://shop.oreilly.com/product/0636920042228.do) as well as on [Amazon](http://amzn.to/2fdn8vU).
But rather than making a sales pitch I'd like to share some of my experiences with writing my first book.

# Atlas is great

All authors writing for O'Reilly get access to [*Atlas*](https://atlas.oreilly.com/) - their publishing platform.
Atlas is like a combination of GitHub and Jenkins - it hosts your books in built-in git repository and "builds" them.
For developers the user experience is very familiar.
The one and only source of your book is in O'Reilly-hosted git repository.
You can use it as any other repository: commit changes, push to branches, pull revisions from other authors.
You can quickly see history of given chapter, revert, etc.

This is all possible because supported formats (AsciiDoc and DocBook) are purely text-based.
More on editing later.
Atlas also has [great documentation](http://docs.atlas.oreilly.com/index.html) and [Getting Started guide](http://chimera.labs.oreilly.com/books/1230000000065/index.html).
Whenever you feel like it you can browse to your book in Atlas (looks like a stripped-down GitHub web interface) and click *Build*.
In about a minute Atlas will show links to PDF, epub, mobi and HTML version of your book.
All having consistent look and feel looking almost like a complete publication.
The whole process is controlled via tiny `atlas.json` configuration file.
If you want to automate it even further, Atlas exposes an API and command-line interface.
I scripted `git push` so that it was immediately followed by building of final book in various formats and downloading them:

```text
#!/bin/bash

if [ -z "$OREILLY_API_TOKEN" ]
then
  echo "Set OREILLY_API_TOKEN variable first"
  exit 1
fi

FORMAT=$@
if [ -z "$FORMAT" ]
then
    FORMAT='pdf'
fi

grep TODO *.asc
git add . -A
git commit -m "WIP"
git push origin HEAD -f
if [[ $FORMAT != *"none"* ]]
then
    rm -rf target
    mkdir -p target
    echo 'Building in Atlas...'
    time atlas build $OREILLY_API_TOKEN oreillymedia/book-name $FORMAT `git rev-parse --abbrev-ref HEAD` | tee target/atlas.log
    echo 'Downloading...'
    grep "PDF: "  target/atlas.log | sed 's/PDF: //'  | xargs -r wget -qO target/rxjava.pdf
    grep "MOBI: " target/atlas.log | sed 's/MOBI: //' | xargs -r wget -qO target/rxjava.mobi
    grep "EPUB: " target/atlas.log | sed 's/EPUB: //' | xargs -r wget -qO target/rxjava.epub
    if [ -e target/rxjva.pdf ]
    then
        echo 'Opening...'
        evince target/rxjava.pdf &
    fi
fi
```

I'm not a `bash` expert but what it does is:

1.  Making sure `OREILLY_API_TOKEN` is set - required for authentication
2.  Determining the target format(s) we are interested in (comma separated)
3.  Shows all `TODO` comments so that I can fix them next time (yeah, it should probably interrupt in case there are any...)
4.  `git commit` followed by `git push` of current branch (I never worked on `master` until chapter was finished so `-f` is...
    OK?)
5.  If building of book was requested I run `atlas` [CLI command](http://docs.atlas.oreilly.com/api.html).
    `git rev-parse --abbrev-ref HEAD` yields current branch name because Atlas can build any branch
6.  The standard output of the CLI tool prints URLs to final versions of book.
    I extract and download them using `wget`
7.  Finally if PDF was downloaded, I open it immediately using [`evince`](https://wiki.gnome.org/Apps/Evince) browser

The whole process takes about one minute so with one command I can publish my work in AsciiDoc and see the final book in beautiful PDF.
Atlas does all the formatting, table of contents, index, cover, cross-reference links, etc. That being said it wasn't always painful.
I ran into bizarre:

```text
- /usr/AHFormatterV62_64/run.sh: line 35: 11589 Segmentation fault      "${AHF62_64_BIN_FOLDER}/AHFCmd" "$@"
```

once in a while.
However this problem was quickly fixed by O'Reilly team.
Also AsciiDoc did not always rendered the way we expected, especially complex tables.
I can't compare Atlas with [Leanpub](https://leanpub.com/) (which [recently became non-free for authors](https://leanpub.com/blog/2016/10/leanpub-and-pricing)) but I suspect they are similar in functionality.
I'm not sure how other publishers are hosting and distributing manuscripts.
I can't imagine using Microsoft Word distributed over e-mail or other non-developer friendly workflow.
From a developer perspective O'Reilly is fantastic.

# Day-to-day writing

I wrote the entire book in [Sublime Text](https://www.sublimetext.com/).
Typically in Distraction Free Mode so my workspace looked as follows:

[![](/assets/img/reactive-programming-with-rxjava-book/1.png)](/assets/img/reactive-programming-with-rxjava-book/1.png)

Seriously.
I didn't use LaTeX because AsciiDoc was sufficient.
Tip for writing in AsciiDoc and Markdown: one sentence per line.
Not more, not less.
Screen width is a natural limit of how long one sentence should be.
Also it's much simpler to move sentences around, delete them and find repetitions.
From markup language perspective single line break is transparent, you need at least two to start a new paragraph.
Writing in a markup language as opposed to binary format like `docx` has another advantage: `grep`, `sed` and other UNIX goodies work as expected.

To catch simple grammar and typos I installed spell checking in Sublime Text.
I configured Sublime a little bit to work better for me:

```text
{
    "added_words":
    [
        "backpressure",
        "unsubscription",
        "Hystrix",
        "servlet"
    ],
    "color_scheme": "Packages/Color Scheme - Default/Dawn.tmTheme",
    "font_size": 13,
    "highlight_line": true,
    "rulers":
    [
        70
    ],
    "spell_check": true
}
```

Couple of words are so common yet unheard of in traditional English that I added them to a dictionary: `added_words`.
`highlight_line` shows a horizontal light blue line where caret currently is.
`rulers` on the other hand displays vertical line at column 70, which happens to be a line length limit for code listings.
You have to be very creative in order to fit code in 70 characters and remain readable.
Especially when writing Java, where class names are not much shorter...

I also appreciated the help of [Powerthesaurus](https://www.powerthesaurus.org/).
I'm not a native English speaker (by far...)
so finding a synonym once in a while to avoid too childish or boring style was very useful.
Luckily the editors and proof readers made tons of corrections to my manuscript so if you were annoyed by my grammar or style in early releases, the final book should be much better.
I was also asked to entirely rewrite several sentences which were hard to understand.

# Reviewers

A great number of people helped us in writing this book.
I would like to especially thank reviewers: [Dávid Karnok](http://akarnokd.blogspot.com/) and [Venkat Subramaniam](http://www.agiledeveloper.com/).
Dávid's feedback was very detailed and many times I felt really foolish making simple mistakes and misunderstandings.
Venkat on the other hand provided a lot of feedback related to overall reading flow.
I rearranged and removed whole chapters based on his feedback (see: [Functor and monad examples in plain Java](http://www.nurkiewicz.com/2016/06/functor-and-monad-examples-in-plain-java.html)).
Their work was great and I truly appreciate it.
Thank you guys!

# Summary

I'm proud to be the [first Polish author](http://www.oreilly.com/pub/au/6868) for O'Reilly, quickly followed by my friend [Konrad Malawski](http://www.oreilly.com/pub/au/7222).
The book is out and it reached \#1 and \#2 "*Hot New Releases*" in *Object-Oriented Design* and *Parallel Computer Programming* categories on Amazon quickly after release:

[![](/assets/img/reactive-programming-with-rxjava-book/2.png)](/assets/img/reactive-programming-with-rxjava-book/2.png)

[![](/assets/img/reactive-programming-with-rxjava-book/3.png)](/assets/img/reactive-programming-with-rxjava-book/3.png)

"Reactive Programming with RxJava" was based on RxJava 1.x.
In the meantime the works on RxJava 2.x (led by aforementioned Dávid Karnok) are very advanced and it should soon be released.
This does not make the book obsolete, about 90% of the content is still applicable.
However when RxJava 2.x is released and Java ecosystem begins to incorporate it (e.g.
RxNetty, Reactive Camel and so on) we (Ben and myself) are considering upgrading the book and releasing second edition.
Yet for the time being our book should be quite comprehensive source of reactive programming knowledge.
Have fun reading and I'm looking for feedback!
