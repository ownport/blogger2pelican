#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Converter blogger's posts to pelican's posts
#   
import os
import sys
import urlparse

from datetime import datetime
from packages import html2text
from urlparse import urlparse
from packages.xpathselectors import XmlXPathSelector

BLOGGER_NAMESPACES = {
    'a': 'http://www.w3.org/2005/Atom',
}

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
    # TODO: added base url
    h = html2text.HTML2Text()
    h.parse_weird_links = True
    result['content'] = h.handle(content)
    
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
    
        
