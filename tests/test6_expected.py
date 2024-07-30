def function_one():
    a = 3
    b = 7
    result_one = 10
    if 10:
        a += 20
    else:
        b += 20
    for _ in range(a):
        result_one += function_two(a, b)
    if result_one > 20:
        result_one *= 2
    else:
        result_one += 5 * a
    return result_one

def function_two(x, y):
    result_two = 5
    for _ in range(y):
        result_two *= 2
    if result_two > 15:
        result_two -= 5 * x
    else:
        result_two += 10 * y
    return result_two

def function_three():
    result_three = function_one() * 3
    result_three += 7
    return result_three