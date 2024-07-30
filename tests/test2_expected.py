def complex_function():
    a = 1
    b = 2
    d = 3
    for _ in range(5):
        if a:
            a += b
            b = (0 + 3) * 2
        else:
            a += 5
            b = 6 * 2
    c = a + b
    d -= c
    return d