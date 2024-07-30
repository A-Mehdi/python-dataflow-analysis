import ast
import copy


class Analysis:
    def __init__(self, functionTable):
        self.functionTable = functionTable
        self.currentScope = []
        self.updateToScoop = {}
        self.processCallees = True

    """
    Check whether the current if condition has else clause by
    iteratively checking the orelse node. This is done to see whether
    an definition coming before the if statement will completely
    overridden by if and else statement or it will not (just if)

    @param node: node corresponding to the If stmt
    """
    def checkIfhasElse(self, node):
        orelse = node.orelse

        while orelse:
            match orelse[0]:
                case ast.If(test, body, orelse1):
                    orelse = orelse1
                case _:
                    break
        
        if orelse:
            return True
        
        return False


    """
    Keep interpreting the loop body until the interpretation
    does not result in new state

    @param node: AST node representing the loop we are in
    @param body: List of statements in the loop body
    @param reference_table: mapping from each variable to their definitions,
                            a variable can have multiple definitions in different locations
    @param l_update: mapping from each variable to their last updated location
    @param use_table: mapping from each variable to its use locations
    """
    def loopFixpoint(self, node, body, reference_table, l_update, use_table):
        beforeLoop = copy.deepcopy(reference_table)
        for nd in body:
            self.processNode(nd, reference_table, l_update, use_table)
        
        while True:
            flag = True
            for var in beforeLoop:
                combined = []
                for elem in reference_table[var]:
                    if elem not in beforeLoop[var]:
                        combined += reference_table[var][elem]
                if len(combined) > 0:
                    combined = list(set(combined))
                    reference_table[var][node.lineno] = combined
                    l_update[var] = node.lineno
                    self.updateToScoop[var][node.lineno] = self.currentScope[:]
                    flag = False
                    for use in combined:
                        if use in use_table:
                            use_table[use].append(node.lineno)
                        else:
                            use_table[use] = [node.lineno]
            if flag:
                break
            beforeLoop = copy.deepcopy(reference_table)
            self.processNode(nd, reference_table, l_update, use_table)
        
        self.currentScope.pop(-1)
        # Add the data coming out of for block to an non-existing line
        for var in reference_table:
            if node.lineno in reference_table[var]:
                reference_table[var][node.end_lineno + 0.5] = reference_table[var][node.lineno]
                l_update[var] = node.end_lineno + 0.5
                self.updateToScoop[var][node.end_lineno + 0.5] = self.currentScope[:]
    
    """
    Update variable-definition mapping
    @param target: variables to be updates
    @param value: variables that are used
    @param reference_table: mapping from each variable to their definitions,
                            a variable can have multiple definitions in different locations
    @param l_update: mapping from each variable to their last updated location
    @param use_table: mapping from each variable to its use locations
    """
    def updateReferences(self, target, value, reference_table, l_update, use_table, is_aug=True):
        dependency = self.processNode(value, reference_table, l_update, use_table)
        results = self.processNode(target, reference_table, l_update, use_table)
        for i in dependency:
            if i in use_table:
                use_table[i].append(target.lineno)
            else:
                use_table[i] = [target.lineno]
        for res in results:
            if is_aug:
                dependency_aug = dependency + [res]
                if res in use_table:
                    use_table[res].append(target.lineno)
                else:
                    use_table[res] = [target.lineno]
            else:
                dependency_aug = dependency
            if res in reference_table:
                reference_table[res][target.lineno] = reference_table[res][l_update[res]] + dependency_aug
                l_update[res] = target.lineno
                if res in self.updateToScoop:
                    self.updateToScoop[res][target.lineno] = self.currentScope[:]
                else:
                    self.updateToScoop[res]= {target.lineno: self.currentScope[:]}
            else:
                reference_table[res] = {target.lineno: dependency_aug}
                l_update[res] = target.lineno
                if res in self.updateToScoop:
                    self.updateToScoop[res][target.lineno] = self.currentScope[:]
                else:
                    self.updateToScoop[res]= {target.lineno: self.currentScope[:]}

    """
    Similar to updateReferences with added check to see if used variables contain
    defined variables, i.e augmented assign operation
    @param target: variables to be updates
    @param value: variables that are used
    @param reference_table: mapping from each variable to their definitions,
                            a variable can have multiple definitions in different locations
    @param l_update: mapping from each variable to their last updated location
    @param use_table: mapping from each variable to its use locations
    """
    def updateReferencesCheckAugmentation(self, target, value, reference_table, l_update, use_table):
        dependency = self.processNode(value, reference_table, l_update, use_table)
        res = self.processNode(target, reference_table, l_update, use_table)
        for i in dependency:
            if i in use_table:
                use_table[i].append(target.lineno)
            else:
                use_table[i] = [target.lineno]
        for i in res:
            if i not in reference_table:
                reference_table[i] = {target.lineno: dependency}
                l_update[i] = target.lineno
                if i in self.updateToScoop:
                    self.updateToScoop[i][target.lineno] = self.currentScope[:]
                else:
                    self.updateToScoop[i]= {target.lineno: self.currentScope[:]}
            else:
                if i in dependency:
                    reference_table[i][target.lineno] = reference_table[i][l_update[i]] + dependency
                    l_update[i] = target.lineno
                    self.updateToScoop[i][target.lineno] = self.currentScope[:]
                else:
                    reference_table[i][target.lineno] = dependency
                    l_update[i] = target.lineno
                    self.updateToScoop[i][target.lineno] = self.currentScope[:]
    
    """
    Process the if statement by interpreting both if and orelse
    bodies and unify them in the end

    @param node: node corresponding to if statement
    @param reference_table: mapping from each variable to their definitions,
                            a variable can have multiple definitions in different locations
    @param l_update: mapping from each variable to their last updated location
    @param use_table: mapping from each variable to its use locations
    """
    def processIfStmt(self, node, reference_table, l_update, use_table):
        variables = self.processNode(node.test, reference_table, l_update, use_table)
        for i in variables:
            if i in use_table:
                use_table[i].append(node.test.lineno)
            else:
                use_table[i] = [node.test.lineno]
        copy1 = copy.deepcopy(reference_table)
        l_update_copy1 = copy.deepcopy(l_update)
        copy2 = copy.deepcopy(reference_table)
        l_update_copy = copy.deepcopy(l_update)
        for i in node.body:
            self.processNode(i, reference_table, l_update, use_table)
        self.currentScope.pop(-1)
        addedFlag = False
        if node.orelse and not isinstance(node.orelse[0], ast.If):
            self.currentScope.append(ast.If(node.test, node.orelse, []))
            addedFlag = True
        for i in node.orelse:
            self.processNode(i, copy2, l_update_copy, use_table)
        if addedFlag:
            self.currentScope.pop(-1)
        for i in reference_table:
            if i in copy2 and reference_table[i] != copy2[i]:
                if i in self.functionTable:
                    continue
                for j in copy2[i]:
                    reference_table[i][j] = copy2[i][j]
                reference_table[i][node.end_lineno+0.5] = list(set(reference_table[i][l_update[i]] + copy2[i][l_update_copy[i]]))
                l_update[i] = node.end_lineno+0.5
                self.updateToScoop[i][node.end_lineno+0.5] = self.currentScope[:]
            if (i not in self.functionTable) and i in l_update_copy and l_update[i] != l_update_copy[i]:
                l_update[i] = node.end_lineno+0.5
                self.updateToScoop[i][node.end_lineno+0.5] = self.currentScope[:]
        
        # If there are no else case for this if statement
        # variable should be able to keep its dependencies
        # before if.
        for i in copy1:
            if not self.checkIfhasElse(node):
                reference_table[i][l_update[i]] = list(set(reference_table[i][l_update[i]] + copy1[i][l_update_copy1[i]]))

    
    """
    Process each ast node, this is the main function that processes
    each node in the AST. Its return is the list of variables that are part of the
    current processed node

    @param node: node corresponding to if statement
    @param reference_table: mapping from each variable to their definitions,
                            a variable can have multiple definitions in different locations
    @param l_update: mapping from each variable to their last updated location
    @param use_table: mapping from each variable to its use locations
    """
    def processNode(self, node, reference_table, l_update, use_table):
        match node:
            case ast.Return(value):
                res = self.processNode(value, reference_table, l_update, use_table)
                # Multiple return statements in a function
                if 'return' in reference_table:
                    reference_table['return'][node.lineno] = res
                    self.updateToScoop['return'][node.lineno] = self.currentScope[:]
                else:
                    reference_table['return'] = {node.lineno: res}
                    self.updateToScoop['return'] = {node.lineno: self.currentScope[:]}
                
                for i in res:
                    if i in use_table:
                        use_table[i].append(node.lineno)
                    else:
                        use_table[i] = [node.lineno]
                return []
            case ast.Constant(value):
                # self.processCallees is used to differentiate between
                # interactive analysis or code transformation
                if self.processCallees:
                    return []
                else:
                    # if it is code transformation, we need the constant
                    # node value
                    return [node]
            case ast.List(elts, ctx):
                initial = []
                for i in elts:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                return initial
            case ast.Tuple(elts, ctx):
                initial = []
                for i in elts:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                return initial
            case ast.Dict(keys, values):
                initial = []
                for i in keys:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                for i in values:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                return initial
            case ast.Name(id, ctx):
                return [id]
            case ast.Expr(value):
                return self.processNode(value, reference_table, l_update, use_table)
            case ast.UnaryOp(op, operand):
                return self.processNode(operand, reference_table, l_update, use_table)
            case ast.BinOp(left, op, right):
                return self.processNode(left, reference_table, l_update, use_table) + self.processNode(right, reference_table, l_update, use_table)
            case ast.BoolOp(op, values):
                initial = []
                for i in values:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                return initial
            case ast.Compare(left, ops, comparators):
                initial = []
                initial += self.processNode(left, reference_table, l_update, use_table)
                for i in comparators:
                    initial += self.processNode(i, reference_table, l_update, use_table)
                return initial
            case ast.Call(func, args, keywords):
                # Do only in the interactive analysis
                if (self.processCallees):
                    match func:
                        # User defined function
                        
                        case ast.Name(id, _):
                            if id in self.functionTable:
                                returnVars = []
                                arg_list = []
                                for i in args:
                                    cur = self.processNode(i, reference_table, l_update, use_table)
                                    arg_list.append(cur)
                                    returnVars += cur
                                
                                for j in arg_list:
                                    for i in j:
                                        if i in use_table:
                                            use_table[i].append(node.lineno)
                                        else:
                                            use_table[i] = [node.lineno]
                                
                                res = self.processFunction(self.functionTable[id], arg_list)
                                # Add function name as dependence
                                if id in reference_table:
                                    reference_table[id][node.lineno] = res[0]
                                else:
                                    reference_table[id] = {node.lineno: res[0]}
                                
                                return [id] + returnVars
                    # Other functions, assume every function input is affecting
                    # function output
                        case _:
                            initial = []
                            for i in args:
                                initial += self.processNode(i, reference_table, l_update, use_table)
                            
                            for i in initial:
                                if i in use_table:
                                    use_table[i].append(node.lineno)
                                else:
                                    use_table[i] = [node.lineno]
                            
                            return initial
                else:
                    match func:
                        case ast.Name(id,_):
                            initial = []
                            initial.append(id)
                            for i in args:
                                initial += self.processNode(i, reference_table, l_update, use_table)
                            
                            for i in initial:
                                if i in use_table:
                                    use_table[i].append(node.lineno)
                                else:
                                    use_table[i] = [node.lineno]
                    
                            return initial
            case ast.IfExp(test, body, orelse):
                return (self.processNode(test, reference_table, l_update, use_table) + 
                        self.processNode(body, reference_table, l_update, use_table) + 
                        self.processNode(orelse, reference_table, l_update, use_table))
            case ast.Attribute(value, attr, ctx):
                res = self.processNode(value, reference_table, l_update, use_table)
                return res + [attr]
            case ast.Subscript(value, slice, ctx):
                return self.processNode(value, reference_table, l_update, use_table) + self.processNode(slice, reference_table, l_update, use_table)
                
            case ast.Slice(lower, upper, step):
                return self.processNode(lower, reference_table, l_update, use_table) + self.processNode(upper, reference_table, l_update, use_table)
                
            case ast.Assign(targets, value, type_comment):
                for target in targets:
                    match target:
                        case ast.Tuple(elts1, ctx):
                            match value:
                                # Special case where multiple variables are assigned to multiple
                                # values
                                case ast.Tuple(elts2, ctx):
                                    assert len(elts1) == len(elts2)
                                    for i in range(len(elts1)):
                                        new_node = ast.Assign([elts1[i]], elts2[i], type_comment)
                                        new_node.lineno = node.lineno
                                        self.processNode(new_node, reference_table, l_update, use_table)
                                case _:
                                    self.updateReferencesCheckAugmentation(target, value, reference_table, l_update, use_table)
                        # If there is a expression with subscript, e.g a[b],
                        # only update a
                        case ast.Subscript(value1, slice, ctx):
                            while isinstance(target, ast.Subscript):
                                target = target.value
                            self.updateReferences(target, value, reference_table, l_update, use_table, False)
                        case _:
                            self.updateReferencesCheckAugmentation(target, value, reference_table, l_update, use_table)
                return []
            case ast.AugAssign(target, op, value):
                match target:
                    # In subscript, indexes do not change
                    case ast.Subscript(value1, slice, ctx):
                        while isinstance(target, ast.Subscript):
                            target = target.value
                        self.updateReferences(target, value, reference_table, l_update, use_table)
                    case _:
                        self.updateReferences(target, value, reference_table, l_update, use_table)
                
                return []
            case ast.If(test, body, orelse):
                self.currentScope.append(node)
                self.processIfStmt(node, reference_table, l_update, use_table)
                return []
            case ast.For(target, iter, body, orelse, type_comment):
                self.currentScope.append(node)
                targets = self.processNode(target, reference_table, l_update, use_table)
                dependency = self.processNode(iter, reference_table, l_update, use_table)
                for i in dependency:
                    if i in use_table:
                        use_table[i].append(node.lineno)
                    else:
                        use_table[i] = [node.lineno]
                for elem in targets:
                    reference_table[elem] = {node.lineno: dependency}
                    l_update[elem] = node.lineno
                    self.updateToScoop[elem] = {node.lineno: self.currentScope[:]}
                self.loopFixpoint(node, body, reference_table, l_update, use_table)
                return []
            case ast.While(test, body, orelse):
                self.currentScope.append(node)
                self.loopFixpoint(node, body, reference_table, l_update, use_table)
                return []
            case ast.Break:
                pass
            case ast.Continue:
                pass
        return []

    """
    Process the given function with the given parameters
    and unify the states from each return statement at special location, line number 0

    @param function: AST node corresponding to function definition
    @param arg_list: List of arguments passed into the function
    """
    def processFunction(self, function, arg_list):
        nodes = []
        fArgs = []
        # Collect arguments
        match function:
            case ast.FunctionDef(name, args, body, decorator_list, returns, type_comment, type_params):
                for i in body:
                    nodes.append(i)
                match args:
                    case ast.arguments(posonlyargs, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults):
                        if len(args) != len(arg_list) and arg_list != []:
                            return None
                        for i in args:
                            match i:
                                case ast.arg(name, _):
                                    fArgs.append(name)
        referenceTable = {}
        lastUpdated = {}
        use_table = {}
        # Create mapping from arguments to parameters
        for i in range(len(arg_list)):
            referenceTable[fArgs[i]] = {function.lineno: arg_list[i]}
            lastUpdated[fArgs[i]] = function.lineno

        if len(arg_list) == 0:
            for i in range(len(fArgs)):
                referenceTable[fArgs[i]] = {function.lineno: []}
                lastUpdated[fArgs[i]] = function.lineno
                self.updateToScoop[fArgs[i]] = {function.lineno: []}

        for node in nodes:
            self.processNode(node, referenceTable, lastUpdated, use_table)
        
        collection = []
        
        # Combine returns
        if 'return' in referenceTable:
            for i in referenceTable['return']:
                collection += referenceTable['return'][i]
        referenceTable['return'][0] = collection

        return (referenceTable, use_table, copy.deepcopy(self.updateToScoop))
    
    """
    Process the analysis results and print out the dependencies. It starts from
    the given variable and recursively processes the dependencies.

    @param referenceTable: mapping from each variable to their definitions,
                           a variable can have multiple definitions in different locations
    @param variableName: currently processed variable
    @param line: currently processed location
    """
    def getResults(self, referenceTable, variableName, line):
        stack = [variableName]
        visited = [variableName]
        outside_variables = []
        while stack:
            variableName = stack.pop(0)
            
            # These variables are passed arguments to the current functon
            if variableName not in referenceTable:
                outside_variables.append(variableName)
                continue
            refs = referenceTable[variableName]
            if variableName in self.functionTable:
                lineNumbers = list(refs.keys())
                lineNumbers.sort()
                targetLine = 0
                for i in range(len(lineNumbers)):
                    if lineNumbers[i] > line and i > 0:
                        targetLine = i - 1
                targetLine = lineNumbers[targetLine]
                if lineNumbers[-1] < line:
                    targetLine = lineNumbers[-1]
                print("Dependencies from function:", variableName)
                parameters = self.getResults(refs[targetLine], 'return', 0)
                for i in parameters:
                    if i not in visited:
                        stack.append(i)
                        visited.append(i)
            else:
                lineNumbers = list(refs.keys())
                lineNumbers.sort()
                targetLine = 0
                for i in range(len(lineNumbers)):
                    if lineNumbers[i] > line and i > 0:
                        targetLine = i - 1
                
                targetLine = lineNumbers[targetLine]
                if lineNumbers[-1] <= line or line == 0:
                    targetLine = lineNumbers[-1]
                
                if (variableName == 'return'):
                    print("Returned values from the function")
                else:
                    print("Variable", variableName, "depends on these variables at line:", targetLine)
                print(refs[targetLine])
                for i in refs[targetLine]:
                    if i not in visited:
                        stack.insert(0, i)
                        visited.append(i)
                line = targetLine
        return outside_variables
    
    def runInteractiveAnalysis(self):
        functionName = ""
        functionName = input("Pick function to analyze: ")
        if functionName not in self.functionTable:
            while functionName not in self.functionTable:
                print("Function does not exist")
                functionName = input("Pick function to analyze: ")
            
        function = self.functionTable[functionName]
        referenceTable = self.processFunction(function, [])
        variableName = input("Pick variable name to analyze: ")
        if variableName not in referenceTable[0]:
            while variableName not in referenceTable[0]:
                print("Variable does not exist")
                variableName = input("Pick variable name to analyze: ")
        
        line = int(input("Pick line number to analyze: "))
        if line > self.functionTable[functionName].end_lineno:
            while line > self.functionTable[functionName].end_lineno:
                print("Line is out of the function scope")
                line = int(input("Pick line number to analyze: "))
        self.getResults(referenceTable[0], variableName, line)
    
    """
    Function for printing out everything
    """
    def runAnalysisOnAll(self):
        for func in self.functionTable:
            resTable, useTable = self.processFunction(self.functionTable[func], [])
            print(func)
            self.printReferenceTable(resTable)
            for i in useTable:
                print(i, useTable[i])
            
            print("\n")

    def printReferenceTable(self, refTable, indent=""):
        for i in refTable:
            if i in self.functionTable:
                print(indent + i)
                n_indent = indent + "    "
                for j in refTable[i]:
                    self.printReferenceTable(refTable[i][j], n_indent)
            else:
                print(indent + i, refTable[i])
                # print(self.updateToScoop[i])

"""
Function for collection all function definitions in
the target file

@param root: root of the AST of the parsed program
"""
def collectFunctions(root):
    functionTable = {}

    for node in ast.walk(root):
        match node:
            case ast.FunctionDef(name, args, body, decorator_list, returns, type_comment, type_params):
                functionTable[name] = node

    return functionTable

"""
Run the interactive analysis

@param filePath: file path to the tested program
"""
def runInteractive(filePath):
    file = open(filePath, "r")

    tree = ast.parse(file.read())

    table = collectFunctions(tree)

    analysis = Analysis(table)

    analysis.runInteractiveAnalysis()