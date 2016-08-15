#!/usr/bin/env python
#   -*- coding: utf-8 -*-
#   
#   XPath selector
#
#   based on Scrapy selectors https://github.com/scrapy/scrapy/tree/master/scrapy/selector
#

import re
from lxml import etree
import six

def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        if hasattr(el, "__iter__"):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def extract_regex(regex, text, encoding='utf-8'):
    """Extract a list of unicode strings from the given text/encoding using the following policies:

    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """

    if isinstance(regex, basestring):
        regex = re.compile(regex, re.UNICODE)

    try:
        strings = [regex.search(text).group('extract')]   # named group
    except:
        strings = regex.findall(text)    # full regex or numbered groups
    strings = flatten(strings)
    return strings

class XPathSelectorList(list):

    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))

    def select(self, xpath):
        return self.__class__(flatten([x.select(xpath) for x in self]))

    def re(self, regex):
        return flatten([x.re(regex) for x in self])

    def extract(self):
        return [x.extract() for x in self]

    def extract_unquoted(self):
        return [x.extract_unquoted() for x in self]

class XPathSelector(object):
    
    def __init__(self, html_content=None, base_url='', _root=None, _expr=None, namespaces=None):
        ''' init
        '''
        self.namespaces = namespaces
        parser = self._parser(recover=True, encoding='utf-8')
        if html_content is not None:
            _root = etree.fromstring(html_content, parser=parser, base_url=base_url)
        self._root = _root
        self._expr = _expr

    def select(self, xpath):
        '''returns a list of new selectors.
        '''
        try:
            xpathev = self._root.xpath
        except AttributeError:
            return XPathSelectorList([])

        try:
            result = xpathev(xpath, namespaces=self.namespaces)
        except etree.XPathError:
            raise ValueError("Invalid XPath: %s" % xpath)

        if type(result) is not list:
            result = [result]

        result = [self.__class__(_root=x, _expr=xpath, namespaces=self.namespaces)
                  for x in result]
        return XPathSelectorList(result)

    def re(self, regex):
        return extract_regex(regex, self.extract())
        
    def extract(self):
        try:
            return etree.tostring(self._root, method=self._tostring_method, encoding=six.u, with_tail=False)
        except (AttributeError, TypeError):
            if self._root is True:
                return u'1'
            elif self._root is False:
                return u'0'
            else:
                return self._root

    def register_namespace(self, prefix, uri):
        if self.namespaces is None:
            self.namespaces = {}
        self.namespaces[prefix] = uri

    def __str__(self):
        data = repr(self.extract()[:40])
        return "<%s xpath=%r data=%s>" % (type(self).__name__, self._expr, data)

    __repr__ = __str__

class XmlXPathSelector(XPathSelector):
    __slots__ = ()
    _parser = etree.XMLParser
    _tostring_method = 'xml'

class HtmlXPathSelector(XPathSelector):
    __slots__ = ()
    _parser = etree.HTMLParser
    _tostring_method = 'html'


if __name__ == '__main__':
    def tests_html():
        ''' HTML tests '''
        
        html_content = '''
        <html>
         <head>
          <base href='http://example.com/' />
          <title>Example website</title>
         </head>
         <body>
          <div id='images'>
           <a href='image1.html'>Name: My image 1 <br /><img src='image1_thumb.jpg' /></a>
           <a href='image2.html'>Name: My image 2 <br /><img src='image2_thumb.jpg' /></a>
           <a href='image3.html'>Name: My image 3 <br /><img src='image3_thumb.jpg' /></a>
           <a href='image4.html'>Name: My image 4 <br /><img src='image4_thumb.jpg' /></a>
           <a href='image5.html'>Name: My image 5 <br /><img src='image5_thumb.jpg' /></a>
          </div>
         </body>
        </html>
        '''
        hxs = HtmlXPathSelector(html_content) 
        assert hxs.select('//title/text()').extract() == [u'Example website']
        assert hxs.select('//base/@href').extract() == [u'http://example.com/']
        assert hxs.select('//div/@id').extract() == [u'images']
        assert hxs.select('//a[@href="image2.html"]/img/@src').extract() == [u'image2_thumb.jpg']
        result = [u'image1_thumb.jpg', u'image2_thumb.jpg', u'image3_thumb.jpg', u'image4_thumb.jpg', u'image5_thumb.jpg']
        assert hxs.select('//a').select('img/@src').extract() == result
        
        links = hxs.select('//a[contains(@href, "image")]')
        assert links.extract() == [
            u'<a href="image1.html">Name: My image 1 <br><img src="image1_thumb.jpg"></a>',
            u'<a href="image2.html">Name: My image 2 <br><img src="image2_thumb.jpg"></a>',
            u'<a href="image3.html">Name: My image 3 <br><img src="image3_thumb.jpg"></a>',
            u'<a href="image4.html">Name: My image 4 <br><img src="image4_thumb.jpg"></a>',
            u'<a href="image5.html">Name: My image 5 <br><img src="image5_thumb.jpg"></a>',
        ]

        results = [
            ([u'image1.html'], [u'image1_thumb.jpg']),
            ([u'image2.html'], [u'image2_thumb.jpg']),
            ([u'image3.html'], [u'image3_thumb.jpg']),
            ([u'image4.html'], [u'image4_thumb.jpg']),
            ([u'image5.html'], [u'image5_thumb.jpg']),
        ]
        for index, link in enumerate(links):
            args = (link.select('@href').extract(), link.select('img/@src').extract())
            assert args == results[index]
        
        
    def tests_xml():
        ''' XML tests '''
        
        xml_content = '''
        <?xml version="1.0"?>
        <counters>
            <measurement start_time="2012-12-12T00:00:00" interval="60">
                <object name="object_1">
                    <counter1>10</counter1>
                    <counter2>20</counter2>
                    <counter3>30</counter3>
                    <counter4>40</counter4>
                    <counter5>50</counter5>
                </object>
            </measurement>
        </counters>
        '''
        xxs = XmlXPathSelector(xml_content)
        assert xxs.select('//counter1/text()').extract() == [u'10']
        assert xxs.select('//object/@name').extract() == [u'object_1']

    def tests():
        tests_html()
        tests_xml()

    tests()
    
