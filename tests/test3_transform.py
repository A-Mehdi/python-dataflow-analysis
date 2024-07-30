def nested_loop_function():
    a = 1
    b = 2
    c = 0
    d = 5

    for i in range(3): # i replaced with _
        a += d # i: Constant value propagation

        for j in range(2): # j: replace with _
            b *= 2
            c += a + b

    result = a + b - c

    return result