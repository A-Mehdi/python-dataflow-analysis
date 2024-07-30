def test():
    a = 1 # Removed after constant value propagation
    b = 2 # Removed after constant value propagation
    c = a + b # a, b: Constant Value Propagation
    d = 0
    if c > 5:
        d = c * a # a, b: Constant Value Propagation
        if d > 10:
            e = a # a, b: Constant Value Propagation
        else:
            e = b # a, b: Constant Value Propagation
    else:
        d = c * b # a, b: Constant Value Propagation
        e = c
    
    return e + d