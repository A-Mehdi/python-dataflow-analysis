def test():
    a = 1
    b = 2 # removed after constant propagation
    c = e = 3 # removed after constant propagation and not reaching
    d = 4 # removed not reaching definition
    e = 5 # removed after constant propagation
    d = c # constant propagation
    if a > 1:
        b = 5 #removed not reaching
        d = a # constant propagation
    elif a > 2:
        d = b # constant propagation
    else:
        d = e # constant propagation
    
    b = 7 # removed after constant propagation
    a += 1
    return d + b # constant propagation

def test1():
    a = 1 #removed not used
    return 0