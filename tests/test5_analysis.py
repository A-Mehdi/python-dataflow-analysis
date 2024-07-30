def function_one():
    a = 3 # removed after constant propagation
    b = 7 # removed after constant propagation

    result_one = 10
    
    for i in range(a): # replaced with underscore
        result_one += function_two(a, b) # constant propagation
    
    if result_one > 20:
        result_one *= 2
    else:
        result_one += 5
    
    return result_one

def function_two(x, y):
    z = 5 # removed after constant propagation

    result_two = x + y + z # z: constant propagation
    
    for j in range(y): # replaced with underscore
        result_two *= 2
    
    if result_two > 15:
        result_two -= 5
    else:
        result_two += 10
    
    return result_two