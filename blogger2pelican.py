#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Converter blogger's posts to pelican's posts
#   
import sys

def usage():
    ''' print how to use blogger2pelican
    '''
    print 'usage: ./blogger2pelican.py <blogger_xml> <posts_directory>\n'
    sys.exit()
    

if __name__ == '__main__':
    
    if len(sys.argv) <> 3:
        usage()
        
