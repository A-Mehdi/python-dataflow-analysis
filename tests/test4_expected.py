def nested_loop_with_if_function():
    a = 1
    b = 2
    c = 0
    for i in range(3):
        a += 3
        for _ in range(2):
            b *= 2
            if a > b:
                c = 5
            else:
                c = 6
    result = a + b - c
    return result