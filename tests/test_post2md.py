from blogger2pelican import Post2MD

def test_handle_code():
    ''' test_handle_code
    '''
    post = 'test __init__ <pre> __init__ </pre> test __init__ test'
    p2md = Post2MD(post)
    result = p2md._handle_code(post)
    assert result == 'test `__init__` \n    ::::\n    __init__ \n test `__init__` test', result

def test_handle_code_many_pre():
    ''' test_handle_code_many_pre
    '''
    post = 'test __init__ <pre> __init__ </pre> test <pre> __init__ </pre> __init__ test'
    p2md = Post2MD(post)
    result = p2md._handle_code(post)
    assert result == 'test `__init__` \n    ::::\n    __init__ \n test \n    ::::\n    __init__ \n `__init__` test', result
    
    
