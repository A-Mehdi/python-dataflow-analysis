def function_one():
    result_one = 10
    for _ in range(3):
        result_one += function_two(3, 7)
    if result_one > 20:
        result_one *= 2
    else:
        result_one += 5
    return result_one

def function_two(x, y):
    result_two = x + y + 5
    for _ in range(y):
        result_two *= 2
    if result_two > 15:
        result_two -= 5
    else:
        result_two += 10
    return result_two