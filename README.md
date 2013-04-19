# blogger2pelican

Converter [blogger](http://www.blogger.com) posts for import to [pelican](http://blog.getpelican.com/)

## How to install

To use blogger2pelican.py script you need to have installed `lxml`
```
$ pip install lxml
```

## How to use

- You need to export your posts from blogger: Control panel -> Settings -> Other -> Blog Tools: Export blog 
- To convert blogger xml file to pelican's posts run the command `./blogger2pelican.py <blogger_xml> <posts_directory>`

For example:
```
$ ./blogger2pelican.py source/blog-04-14-2013.xml posts/
```

All posts from xml file will be extracted to posts/ directory. Each post in separated file. The format of result file is Markdown.

Metadata syntax for Markdown posts are follow this pattern:
```
Title: blogger2pelican converter
Date: 2014-04-14 10:20
Tags: blogger, pelican, converter
Category: yeah
Slug: blogger2pelican
Author: ownport
Summary: Short version for index and feeds

This is the content of blogger2pelican blog post.
```

The field mapping from blogger xml file to Pelican post in Markdown format

Blogger | Pelican
------- | --------
title   | title
author  | author
updated | date
tags    | tags
content | post content

Note that, aside from the title, none of this metadata is mandatory.

## Links

- [Pelican web site](http://getpelican.com/)
- [Blogger.com](http://www.blogger.com)
- [Blogging with Pelican](http://www.futurile.net/resources/blogging/pelican.html)

