def nested_loop_function():
    a = 1
    b = 2
    c = 0
    for _ in range(3):
        a += 5
        for _ in range(2):
            b *= 2
            c += a + b
    result = a + b - c
    return result