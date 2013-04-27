#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Converter blogger's posts to pelican's posts
#   
import os
import re
import sys
import urlparse

from datetime import datetime
from urlparse import urlparse
from packages.xpathselectors import XmlXPathSelector

BLOGGER_NAMESPACES = {
    'a': 'http://www.w3.org/2005/Atom',
}

class Post2MD(object):
    ''' convert html post to markdown
    '''
    def __init__(self, html):
        ''' __init__
        '''
        self._html = html
    
    def _handle_a_tag(self, html):
        ''' handle `a` tag
        '''
        # remove <a name='more'></a>
        result = re.sub(r"<a name='more'></a>", r'', html)
        # `img` in `a` tag
        result = re.sub(r'<a.*?><img alt="(.*?)".*?src="(.+?)".+?/></a>', r'\n![\1](\2)\n', result )
        result = re.sub(r'<a.*?><img.*?src="(.+?)".+?/></a>', r'\n![](\1)\n', result )
        # `a` tag
        result = re.sub(r'<a href="(.+?)">(.+?)</a>', r'[\2](\1)', result )
        return result

    def _handle_code(self, html):
        ''' handle code
        '''
        def wrapper(html):
            ''' wrapper
            '''
            result = re.sub(r'(__\w+__)', r'`\1`', html)
            return result

        def pre_handler(html):
            ''' pre_handler
            '''
            CODE_PREFIX = '    '
            result = list()
            result.append('\n' + CODE_PREFIX + '::::')
            for line in html.split('\n'):  
                result.append(CODE_PREFIX + line)
            result.append('')
            return '\n'.join(result)
        
        result = unicode()
        curr_pos = 0
        while True:
            pre_pos = html.find('<pre>', curr_pos)
            if pre_pos >= 0:
                result += wrapper(html[curr_pos:pre_pos])
                curr_pos = pre_pos + 5 # 5 is length of <pre>
                curr_pos = html.find('</pre>', curr_pos) + 6 # 6 is length of </pre>
                result += pre_handler(html[pre_pos+5:curr_pos-6])
            else:
                # no `<pre>` & `</pre>`
                result += wrapper(html[curr_pos:])
                break
        return result
    
                
    def _handle_abbrv(self, html):
        ''' handle abbreviations in html
        '''
        result = re.sub(r'&lt;', '<', html)
        result = re.sub(r'&gt;', '>', result)
        return result
    
    def transform(self):
        ''' transform html post to markdown format
        '''
        # `br` tag
        self._html = re.sub(r'<br />', '\n', self._html)

        # `a` tag
        self._html = self._handle_a_tag(self._html)
        
        # move `<span style="font-weight: bold;">` to bold
        self._html = re.sub(r'<span style="font-weight: bold;">(.+?)</span>', r'**\1**', self._html)
        self._html = re.sub(r'<b>(.+?)</b>', r'**\1**', self._html)

        # move `<span style="font-style: italic;">` to italic
        self._html = re.sub(r'<span style="font-style: italic;">(.+?)</span>', r'_\1_', self._html)
        self._html = re.sub(r'<i>(.+?)</i>', r'_\1_', self._html)

        # move `<ul>` to list
        self._html = re.sub(r'<ul>(.+?)</ul>', r'- \1\n', self._html)
        
        # Blogger specific HTML code
        self._html = re.sub(r'<div class="separator" style="clear: both; text-align: center;">\n(.+?)\n</div>',
                            r'\1', self._html)
        self._html = self._html.replace('<div class="separator" style="clear: both; text-align: center;"></div>', '')
        self._html = re.sub(r'<div style="text-align: center;">(.+?)</div>', r'**\1**\n', self._html)

        # code
        self._html = self._handle_code(self._html)

        # abbreviations
        self._html = self._handle_abbrv(self._html)        

        # remove multiple EoL
        # self._html = re.sub(r'\n{3,}','\n', self._html)
        return self._html
     

def simplify_datetime(dt):
    ''' 
    - leave just date + time without miliseconds and timezone
    - replace 'T' by ' '
    '''
    dt, dt_tzone = dt.split('.')
    dt = dt.replace('T',' ')
    return dt

def make_post(post):
    ''' make post
    '''
    result = unicode()
    result += u'Title: %s\n' % post['title']
    if post['author']['email'] <> u'noreply@blogger.com':
        result += u'Author: %s <%s>\n' % (post['author']['name'], post['author']['email'])
    else:
        result += u'Author: %s\n' % post['author']['name']
    result += u'Date: %s\n' % post['published']
    result += u'Slug: %s\n' % os.path.basename(post['link']).replace('.html','')
    result += u'Tags: %s\n\n' % ','.join(post['tags'])

    result += post['content']
    return result

def print_post(post):
    ''' print post
    '''
    print make_post(post)
    print '--------------------------------------\n'

def save_post(directory, post):
    ''' save post to file
    '''
    post_directory = os.path.dirname(urlparse(post['link']).path)
    if post_directory[0] == '/':
        post_directory = post_directory[1:]
    post_directory = os.path.join(directory, post_directory)
    
    if not os.path.exists(post_directory):
        os.makedirs(post_directory)
    
    post_path = os.path.join(post_directory, os.path.basename(post['link']))
    post_path = post_path.replace('.html', '.md')
    
    with open(post_path, 'w+') as post_file:
        post_file.write(make_post(post).encode('utf8'))  

def parse_entry(entry):
    ''' return parsed entry
    '''
    result = dict()

    result['tags'] = entry.select('a:category/@term').extract()
    if 'http://schemas.google.com/blogger/2008/kind#post' in result['tags']:
        result['tags'].remove('http://schemas.google.com/blogger/2008/kind#post')
    else:
        # http://schemas.google.com/blogger/2008/kind#template
        # http://schemas.google.com/blogger/2008/kind#settings
        return None

    result['id'] = u''.join(entry.select('a:id/text()').extract())
    result['published'] = u''.join(entry.select('a:published/text()').extract())
    result['published'] = simplify_datetime(result['published']) 
    result['updated'] = u''.join(entry.select('a:updated/text()').extract())
    result['updated'] = simplify_datetime(result['updated'])
    result['title'] = u''.join(entry.select('a:title/text()').extract())
    
    content = u''.join(entry.select('a:content/text()').extract())
    post2md = Post2MD(content)
    result['content'] = post2md.transform()
    
    result['link'] = u''.join(entry.select('a:link[@rel="alternate"]/@href').extract())
    
    result['author'] = dict()
    result['author']['name'] = u''.join(entry.select('a:author/a:name/text()').extract())
    result['author']['email'] = u''.join(entry.select('a:author/a:email/text()').extract())
    result['author']['uri'] = u''.join(entry.select('a:author/a:uri/text()').extract())

    return result

def parse_xml(xml_file, directory):
    ''' parse xml file and store posts in directory
    '''
    blog = dict()
    content = open(xml_file, 'r').read()
    xxs = XmlXPathSelector(content, namespaces=BLOGGER_NAMESPACES)
    
    blog['title'] = u''.join(xxs.select('//a:feed/a:title/text()').extract())
    blog['subtitle'] = u''.join(xxs.select('//a:feed/a:subtitle/text()').extract())
    blog['links'] = xxs.select('//a:feed/a:link/@href').extract()
    
    blog['author'] = dict()
    blog['author']['name'] = u''.join(xxs.select('//a:feed/a:author/a:name/text()').extract())
    blog['author']['email'] = u''.join(xxs.select('//a:feed/a:author/a:email/text()').extract())
    blog['author']['uri'] = u''.join(xxs.select('//a:feed/a:author/a:uri/text()').extract())
    
    for entry in xxs.select('//a:feed/a:entry'):
        entry_res = parse_entry(entry)
        if entry_res:
            #print_post(entry_res)
            save_post(directory, entry_res)
    
def usage():
    ''' print how to use blogger2pelican
    '''
    print 'usage: ./blogger2pelican.py <blogger_xml> <posts_directory>\n'
    sys.exit()
    

if __name__ == '__main__':
    
    if len(sys.argv) <> 3:
        usage()
    
    blogger_xml = sys.argv[1]
    posts_directory = sys.argv[2]

    if not os.path.isfile(blogger_xml):
        print >> sys.stderr, 'Error! File %s does not exist\n' % blogger_xml
        sys.exit()

    if not os.path.isdir(posts_directory):
        print >> sys.stderr, 'Error! Directory %s does not exist\n' % posts_directory
        sys.exit()
        
    parse_xml(blogger_xml, posts_directory)                
    
        
