def complex_function():
    a = 1
    b = 2
    c = 0 # Removed after constant propagation
    d = 3
    e = 5 # Unused value removed
    f = 6 # Removed after constant propagation

    for i in range(5): # i replaced with _
        if a:
            a += b
            b = (c+d) * 2 # c, d: constant value propagation
        else:
            a += e # e: constant value propagation
            b = f * 2 # f: constant value propagation

    c = a + b
    d -= c

    return d    