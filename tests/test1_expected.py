def test():
    c = 1 + 2
    d = 0
    if c > 5:
        d = c * 1
        if d > 10:
            e = 1
        else:
            e = 2
    else:
        d = c * 2
        e = c
    return e + d