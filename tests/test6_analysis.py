def function_one():
    a = 3
    b = 7
    threshold_one = 20
    result_one = 10

    if result_one:
        a += threshold_one
    else:
        b += threshold_one

    for i in range(a):
        result_one += function_two(a, b)
    
    if result_one > threshold_one:
        result_one *= 2
    else:
        result_one += 5 * a
    
    return result_one

def function_two(x, y):
    z = 5
    threshold_two = 15

    result_two = z

    for j in range(y):
        result_two *= 2
    
    if result_two > threshold_two:
        result_two -= 5 * x
    else:
        result_two += 10 * y
    
    return result_two

def function_three():
    constant = 3

    result_three = function_one() * constant

    result_three += 7
    
    return result_three