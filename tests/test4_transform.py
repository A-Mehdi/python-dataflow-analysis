def nested_loop_with_if_function():
    a = 1
    b = 2
    c = 0
    d = 5 # Removed after constant Value Propagation
    e = 6 # Removed after constant Value Propagation

    for i in range(3):
        a += i # Constant Value Propagation

        for j in range(2):
            b *= 2

            if a > b:
                c = d # Constant Value Propagation
            else:
                c = e # Constant Value Propagation

    result = a + b - c

    return result