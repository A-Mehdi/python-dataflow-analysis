from _ast import Assign, Expr, For, FunctionDef, If, Name, Subscript
import ast
from typing import Any
from analysis import Analysis

class DeadCodeElim:
    def __init__(self, functionTable) -> None:
        self.functionTable = functionTable
        self.analysis = Analysis(functionTable)
        self.analysis.processCallees = False
        self.allDefinitions = {}
        self.allScopes = {}

    """
    Obtains scope information for given line
    """
    def getScopeForGivenLine(self, lineNumber):
        for var in self.allDefinitions:
            if lineNumber in self.allDefinitions[var]:
                return self.allScopes[var][lineNumber]
        
        return self.getScopeForGivenLine(lineNumber-1)


    """
    Compares two scopes and checks whether scope2 subsumes scope1
    """
    def compareScopes(self, scope1, scope2):
        if scope1 == scope2:
            return True
        
        idx = 0

        while idx < min(len(scope2), len(scope1)):
            if scope2[idx] != scope1[idx]:
                break
            idx += 1

        if scope2 == []:
            return True
        elif idx == len(scope2):
            return True
        else:
            return False

    """
    Finds definitions that are not reaching uses.
    It iterates every uses and finds definitions that can lead to this use
    by using definition and scope information. Then it collects definitions that are
    overridden by other definitions. It also collects variables that have no uses
    i.e. iterator variables
    """
    def findUnreachingDefinitions(self, definitions, uses, scope, variable, definitionsToRemove, func):
        visited = []
        for k in uses:
            currentDefs = []
            for j in definitions:
                if int(j) != j:
                    continue
                useScope = self.getScopeForGivenLine(k)
                totalOrder = self.compareScopes(useScope, scope[j]) or self.compareScopes(scope[j], useScope)
                if j < k and totalOrder and j not in visited:
                    currentDefs.append((j, definitions[j]))
                    visited.append(j)
            currentDefs.sort(key=lambda x: x[0])
            if len(currentDefs) < 2:
                continue
            for curDef in range(len(currentDefs) - 1):
                for nextDef in range(curDef + 1, len(currentDefs)):
                    if self.compareScopes(scope[currentDefs[curDef][0]], scope[currentDefs[nextDef][0]]):
                        if variable in definitionsToRemove[func]:
                            definitionsToRemove[func][variable].append(currentDefs[curDef][0])
                        else:
                            definitionsToRemove[func][variable] = [currentDefs[curDef][0]]

    """
    This function finds the values that will affect returned
    variables of the function by traversing from the returned values backwards
    """
    def findUnimportantVariables(self, allDefinitions, func, unimportantDefinitions):
        varsUsedInReturn = allDefinitions['return']
        totalVisited = []
        for line in varsUsedInReturn:
            if line == 0:
                continue
            usedVariables = varsUsedInReturn[line]
            stack = []
            visited = []
            for i in usedVariables:
                stack.append((line, i))
                visited.append((line, i))

            while stack:
                curLine, curVar = stack.pop(0)
                if curVar in self.functionTable:
                    continue
                if curVar not in allDefinitions:
                    continue
                nextVariables = allDefinitions[curVar]
                lines = list(nextVariables.keys())
                lines.sort()
                idx = -1
                for i in range(len(lines)):
                    if lines[i] > curLine:
                        idx = i - 1
                nextLine = lines[idx]
                for vars in nextVariables[nextLine]:
                    if (nextLine, vars) not in visited:
                        stack.append((nextLine, vars))
                        visited.append((nextLine, vars))
            
            totalVisited += visited

        totalVisited = list(set(totalVisited))
        variablesUsedInReturn = []
        for i in totalVisited:
            variablesUsedInReturn.append(i[1])

        unimportantDefinitions[func] = []
        for i in allDefinitions:
            if i in self.functionTable or i in variablesUsedInReturn or i == 'return':
                continue
            unimportantDefinitions[func].append(i)

    """
    This function finds dead-code which is one of the following:
    1. Variables not used
    2. Definitions that are not used
    3. Definitions that do not contribute to the return
    """
    def findDeadCode(self):
        definitionsToRemove = {}
        notUsedAtAll = {}
        definitionsMayRemove = {}
        for func in self.functionTable:
            resTable, useTable, scopeTable = self.analysis.processFunction(self.functionTable[func], [])
            self.allDefinitions = resTable
            self.allScopes = scopeTable
            definitionsToRemove[func] = {}
            notUsedAtAll[func] = []
            for var in resTable:
                if var == 'return':
                    continue
                if var in useTable:
                    uses = useTable[var]
                    uses = list(set(uses))
                    definitions = resTable[var]
                    uses.sort()
                    scope = scopeTable[var]
                    self.findUnreachingDefinitions(definitions, uses, scope, var, definitionsToRemove, func)
                else:
                    notUsedAtAll[func].append(var)

        
            self.findUnimportantVariables(resTable, func, definitionsMayRemove)
        return (definitionsToRemove, notUsedAtAll, definitionsMayRemove)

def collectFunctions(root):
    functionTable = {}

    for node in ast.walk(root):
        match node:
            case ast.FunctionDef(name, args, body, decorator_list, returns, type_comment, type_params):
                functionTable[name] = node

    return functionTable

"""
Transformer for removing definitions that do not have
use
"""
class RemoveTransformer(ast.NodeTransformer):
    def __init__(self, globalFunctionTable) -> None:
        super().__init__()
        self.deadcode = DeadCodeElim(globalFunctionTable)
        results = self.deadcode.findDeadCode()
        self.toRemove = results[0]
        self.notUsedAtAll = results[1]
        self.mayRemove = results[2]
        self.currentFunc = None
        self.subscriptFlag = False
    
    """
    Keep track of current function
    """
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.currentFunc = node.name
        for nodes in node.body:
            if isinstance(nodes, ast.Assign):
                self.visit_Assign(nodes)
            else:
                self.visit(nodes)
        return node
    
    """
    In this transformer we target assign statements and delete them
    """
    def visit_Assign(self, node: Assign) -> Any:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0]
            if target.id in self.toRemove[self.currentFunc]:
                if node.lineno in self.toRemove[self.currentFunc][target.id]:
                    node.targets = []
                    node.value = ast.Constant("remove")
            elif target.id in self.notUsedAtAll[self.currentFunc]:
                node.targets = []
                node.value = ast.Constant("remove")
        else:
            for i in node.targets:
                if not isinstance(i, ast.Name):
                    return node
            
            newTargets = []
            for i in node.targets:
                if i.id in self.toRemove[self.currentFunc] and node.lineno in self.toRemove[self.currentFunc][i.id]:
                    continue
                elif i.id in self.notUsedAtAll[self.currentFunc]:
                    continue
                newTargets.append(i)

            node.targets = newTargets

        return node
    
    
"""
In case we cannot delete variables but know that they are not used,
for example iterator values, we replace them with underscore
"""
class ReplaceWithUnderScore(ast.NodeTransformer):
    def __init__(self, globalFunctionTable) -> None:
        super().__init__()
        self.deadcode = DeadCodeElim(globalFunctionTable)
        results = self.deadcode.findDeadCode()
        self.toRemove = results[0]
        self.notUsedAtAll = results[1]
        self.mayRemove = results[2]
        self.currentFunc = None
        self.subscriptFlag = False

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.currentFunc = node.name
        for nodes in node.body:
            self.visit(nodes)
        return node

    def visit_Subscript(self, node: Subscript) -> Any:
        self.subscriptFlag = True
        self.visit(node.value)
        self.visit(node.slice)
        self.subscriptFlag = False
        return node
    
    def visit_Name(self, node: Name) -> Any:
        if node.id in self.toRemove[self.currentFunc] and node.lineno in self.toRemove[self.currentFunc][node.id]:
            node.id = "_"
        elif node.id in self.notUsedAtAll[self.currentFunc]:
            node.id = "_"
        return node


"""
If after removing assign statement, block is empty, remove the block
"""
class RemoveBlocks(ast.NodeTransformer):
    def visit_If(self, node: If) -> Any:
        if node.body == [] and node.orelse == []:
            return None
        elif node.body == []:
            node.body.append(ast.Pass())
        return node
    
    def visit_For(self, node: For) -> Any:
        if node.body == []:
            return None
        return node


"""
Helper for RemoveTransformer, cannot directly remove Assign nodes
"""
class CleanUpTransformer(ast.NodeTransformer):
    def visit_Assign(self, node: Assign) -> Any:
        if node.targets == []:
            return None
        return node


"""
Transformer for constant value propagation
"""
class ConstantValuePropagation(ast.NodeTransformer):
    def __init__(self, globalFunctionTable) -> None:
        super().__init__()
        self.analysis = Analysis(globalFunctionTable)
        self.analysis.processCallees = False
        self.results = {}
        for func in globalFunctionTable:
            self.results[func] = self.analysis.processFunction(globalFunctionTable[func], [])
        self.currentFunc = None
        self.allDefinitions = {}
        self.allScopes = {}

    def getScopeForGivenLine(self, lineNumber):
        for var in self.allDefinitions:
            if lineNumber in self.allDefinitions[var]:
                return self.allScopes[var][lineNumber]
        
        return self.getScopeForGivenLine(lineNumber-1)

    def compareScopes(self, scope1, scope2):
        if scope1 == scope2:
            return True
        
        idx = 0

        while idx < min(len(scope2), len(scope1)):
            if scope2[idx] != scope1[idx]:
                break
            idx += 1

        if scope2 == []:
            return True
        elif idx == len(scope2):
            return True
        else:
            return False

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.currentFunc = node.name
        self.allDefinitions = self.results[node.name][0]
        self.allScopes = self.results[node.name][2]
        for nodes in node.body:
            self.visit(nodes)
        return node

    def visit_Name(self, node: Name) -> Any:
        uses = self.results[self.currentFunc][1]
        definitions = self.results[self.currentFunc][0]
        scope = self.results[self.currentFunc][2]
        if node.id in uses and node.id in definitions:
            varUses = uses[node.id]
            varDefinitions = definitions[node.id]
            varScopes = scope[node.id]
            if node.lineno in varUses:
                if node.lineno in varDefinitions:
                    return node

                # Finds the latest definition that comes before
                # the current use and is in scope to affect it
                beforeDefinitions = []
                for i in varDefinitions:
                    if i < node.lineno:
                        beforeDefinitions.append((i, varDefinitions[i]))
                
                beforeDefinitionsInScope = []
                useScope = self.getScopeForGivenLine(node.lineno)
                for i in beforeDefinitions:
                    if self.compareScopes(useScope, varScopes[i[0]]):
                        beforeDefinitionsInScope.append(i)

                if beforeDefinitionsInScope == []:
                    return node
                
                beforeDefinitionsInScope.sort(key=lambda x: x[0])
                lastDef = beforeDefinitionsInScope[-1]
                if len(lastDef[1]) == 1 and isinstance(lastDef[1][0], ast.Constant):
                    return lastDef[1][0]
        
        return node
                
                


def transformLoop(filePath):
    
    file = open(filePath, "r")

    tree = ast.parse(file.read())

    # print(ast.dump(tree, indent=4))

    while True:
        globalFunctionTable = collectFunctions(tree)
        t1 = RemoveTransformer(globalFunctionTable)
        t2 = CleanUpTransformer()
        t3 = ReplaceWithUnderScore(globalFunctionTable)
        newTree = t1.visit(tree)
        newTree = t2.visit(newTree)
        newTree = t3.visit(newTree)
        globalFunctionTable = collectFunctions(newTree)
        t4 = ConstantValuePropagation(globalFunctionTable)
        newTree = t4.visit(newTree)
        globalFunctionTable = collectFunctions(newTree)
        t1 = RemoveTransformer(globalFunctionTable)
        t2 = CleanUpTransformer()
        newTree = t1.visit(newTree)
        newTree = t2.visit(newTree)
        if tree == newTree:
            break
        tree = newTree

    globalFunctionTable = collectFunctions(tree)
    deadcode = DeadCodeElim(globalFunctionTable)
    res = deadcode.findDeadCode()
    if res[2]:
        for i in res[2]:
            if res[2][i]:
                print("These variables do not affect return in function:", i)
                print(res[2][i])


    print(ast.unparse(tree))
