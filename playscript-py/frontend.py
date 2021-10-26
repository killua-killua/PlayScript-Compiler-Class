import sys
import os
from typing import List, Set
# from types import FunctionType

from antlr4 import *
# from antlr4.tree.Tree import *
# from antlr4.atn.ATNState import BlockEndState

from PlayScriptLexer import *
from PlayScriptParser import *
from PlayScriptListener import *
from PlayScriptVisitor import *

import enum


class Symbol():
    ''' Symbol：Variable, Function, Class '''

    def __init__(self):
        # 符号的名称
        self.name = None
        # 所属作用域
        self.enclosingScope = None
        # 可见性，比如public还是private
        self.visibility = None
        # Symbol关联的 AST节点
        self.ctx:ParserRuleContext = None
    
    def getName(self):
        return self.name

    def getEnclosingScope(self):
        return self.enclosingScope

class Class:
    pass

class Scope(Symbol):
    ''' Scope: BlockScope, Function '''

    def __init__(self):
        super().__init__()
        # List<Symbol>
        self.symbols = []
    def addSymbol(self, symbol):
        self.symbols.append(symbol)
        symbol.enclosingScope = self
    
    def getVariable(self, name):
        for s in self.symbols:
            if isinstance(s, Variable) and s.name == name:
                return s
        return None
    
    '''
     * 是否包含某个Function
     * @param name
     * @param paramTypes List<Type>. 不允许为空。该参数不允许为空。如果没有参数，需要传入一个0长度的列表。
     * @return Function
    '''
    def getFunction(self, name:str, paramTypes):
        rtn = None
        for s in self.symbols:
            if isinstance(s, Function) and s.name == name:
                if s.matchParameterTypes(paramTypes):
                    rtn = s
                    break
        return rtn

    '''
     * 获取一个函数类型的变量，能匹配相应的参数类型
    '''
    def getFunctionVariable(self, name, paramTypes):
        rtn:Variable = None
        for s in self.symbols:
            if isinstance(s, Variable) and isinstance(s.type, FunctionType) and (s.name == name):
                functionType:FunctionType = s.type
                if functionType.matchParameterTypes(paramTypes):
                    rtn = s
                    break
        return rtn
    
    '''
     * 是否包含某个Class
    '''
    def getClass(self, name:str) -> Class:
        rtn = None
        for s in self.symbols:
            if isinstance(s, Class) and s.name == name:
                rtn = s
                break
        return rtn
    
    # 是否包含某个Symbol
    def containsSymbol(self, symbol:Symbol):
        return symbol in self.symbols


class Variable(Symbol):
    # Variable可以是： 一般变量、函数变量、类变量（对象）
    def __init__(self, name:str, enclosingScope:Scope, ctx:ParserRuleContext):
        super().__init__()
        self.name = name
        self.enclosingScope = enclosingScope
        self.ctx = ctx

        self.type = None
        # 作为parameter的变量的属性。缺省值
        self.defaultValue = None
        # 是否允许多次重复，这是一个创新的参数机制
        self.multiplicity = 1

    # /**
    #  * 是不是类的属性
    #  * @return
    #  */
    # public boolean isClassMember(){
    #     return enclosingScope instanceof Class;
    # }

    def toString(self):
        return "Variable " + self.name + " -> "+ self.type.toString()


class BlockScope(Scope):
    # 给block编号的数字
    index:int = 1

    def __init__(self, enclosingScope:Scope, ctx:ParserRuleContext):
        super().__init__()
        self.name = "block" + str(BlockScope.index)
        BlockScope.index += 1
        self.enclosingScope = enclosingScope
        self.ctx = ctx
    
    def toString(self):
        return "Block " + self.name

class Type():
    ''' Type: PrimitiveType, VoidType, FunctionType, Class '''

    def getName(self):
        pass

    def getEnclosingScope(self):
        # Scope
        pass
    
    def toString(self):
        pass

    '''
    本类型是不是 is 目标类型。 也就是能否用来替换目标类型。
    以面向对象为例，子类 is 父类。子类可以出现在任何需要父类的地方。
    '''
    def isType(type):
        pass

class PrimitiveType(Type):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def getName(self):
        return self.name

    def getEnclosingScope(self):
        return None

    def toString(self):
        return self.name

    '''
     * 计算两个类型中比较“高”的一级，比如 int 和 float 相加，要取 float
    '''
    def getUpperType(type1, type2):
        type:PrimitiveType = None
        if type1 == String or type2 == String:
            type = String
        elif type1 == Float or type2 == Float:
            type = Float
        elif type1 == Integer or type2 == Integer:
            type = Integer
        else:
            type = None  # TODO: 以上这些规则有没有漏洞？
        return type

    '''
     * 某个类型是不是数值型的（以便进行数值型运算）
    '''
    def isNumeric(type:Type):
        if type == Integer or type == Float:
            return True
        else:
            return False

    def isType(self, type):
        return self == type

# 把常见的基础数据类型都定义出来
Integer = PrimitiveType("Integer")
Float = PrimitiveType("Float")
Boolean = PrimitiveType("Boolean")
String = PrimitiveType("String")
Null = PrimitiveType("null")

class VoidType(Type):
    def __init__(self):
        super().__init__()

    def getName(self):
        return "void"

    def getEnclosingScope(self):
        return None

    def isType(self, type):
        return self == type

    def toString(self):
        return "void"
# 只保留一个实例即可
voidType = VoidType()

class FunctionType(Type):
    def getReturnType(self):
        # Type
        pass

    def getParamTypes(self):
        # List<Type>
        pass

    def matchParameterTypes(self, paramTypes):
        # bool
        pass

class DefaultFunctionType(FunctionType):
    # 对于未命名的类型，自动赋予名字
    nameIndex:int = 1

    def __init__(self):
        super().__init__()
        self.name = "FunctionType" + str(DefaultFunctionType.nameIndex)
        DefaultFunctionType.nameIndex += 1
        self.enclosingScope = None
        self.returnType = None
        self.paramTypes = []  # List<Type>

    def getName(self):
        return self.name

    def getEnclosingScope(self):
        return self.enclosingScope

    def getReturnType(self):
        return self.returnType

    def getParamTypes(self):
        return self.paramTypes

    def toString(self):
        retTypeStr = self.returnType.toString()
        paraTypeStr = ''
        for i, para_type in enumerate(self.paramTypes):
            s = para_type.toString()
            if i > 0:
                paraTypeStr = paraTypeStr + ','
            paraTypeStr = paraTypeStr + s
        return retTypeStr + '(' + paraTypeStr + ')'

    def isType(self, type:Type):
        if isinstance(type, FunctionType):
            if self == type:
                return True  # shortcut
            if not self.getReturnType().isType(type.getReturnType()):
                return False
            paramTypes1 = self.getParamTypes()
            paramTypes2 = type.getParamTypes()
            if len(paramTypes1) != len(paramTypes2):
                return False
            for i in range(len(paramTypes1)):
                if not paramTypes1[i].isType(paramTypes2[i]):
                    return False
            return True
        return False

    '''
    检查该函数是否匹配所需的参数。
    '''
    def matchParameterTypes(self, paramTypes):
        # 比较每个参数
        if len(self.paramTypes) != len(paramTypes):
            return False

        match = True
        for i in range(len(paramTypes)):
            type1 = self.paramTypes[i]
            type = paramTypes[i]
            if not type1.isType(type):
                match = False
                break
        return match

class Function(Scope, FunctionType):
    def __init__(self, name:str, enclosingScope:Scope, ctx:ParserRuleContext):
        super().__init__()
        # 参数实体
        self.parameters = []  # List<Variable>
        # 返回值
        self.returnType = None
        # 闭包变量，即它所引用的外部环境变量
        self.closureVariables = set()  # Set<Variable>
        
        self.paramTypes = []  # List<Type>

        self.name = name
        self.enclosingScope = enclosingScope
        self.ctx = ctx

    def getReturnType(self):
        return self.returnType
    
    def getParamTypes(self) -> List[Type]:
        if self.paramTypes == []:
            for param in self.parameters:
                self.paramTypes.append(param.type)
        return self.paramTypes

    def toString(self):
        retTypeStr = self.returnType.toString()
        paraTypeStr = ''
        for i, para_type in enumerate(self.paramTypes):
            s = para_type.toString()
            if i > 0:
                paraTypeStr = paraTypeStr + ','
            paraTypeStr = paraTypeStr + s
        return retTypeStr + ' ' + self.name + '(' + paraTypeStr + ')'

    def isType(self, type:Type):
        if isinstance(type, FunctionType):
            if self == type:
                return True
            if not self.getReturnType().isType(type.getReturnType()):
                return False
            paramTypes1 = self.getParamTypes()
            paramTypes2 = type.getParamTypes()
            if len(paramTypes1) != len(paramTypes2):
                return False
            for i in range(len(paramTypes1)):
                if not paramTypes1[i].isType(paramTypes2[i]):
                    return False
            return True
        return False

    '''
    检查改函数是否匹配所需的参数
    '''
    def matchParameterTypes(self, paramTypes):
        # 比较每个参数
        if len(self.parameters) != len(paramTypes):
            return False

        match = True
        for i in range(len(paramTypes)):
            var:Variable = self.parameters[i]
            type:Type = paramTypes[i]
            if not var.type.isType(type):
                match = False
                break
        return match

    # 该函数是不是类的方法
    def isMethod(self):
        return isinstance(self.enclosingScope, Class)

    # 该函数是不是类的构建函数
    def isConstructor(self):
        if isinstance(self.enclosingScope, Class):
            return self.enclosingScope.name == self.name
        return False


# 用来表示"this"关键字的符号
class This(Variable):
    def __init__(self, theClass:Class, ctx:ParserRuleContext):
        super(This, self).__init__("this", theClass, ctx)
    def Class(self) -> Class:
        return self.enclosingScope
# 用来表示"super"关键字的符号
class Super(Variable):
    def __init__(self, theClass:Class, ctx:ParserRuleContext):
        super(Super, self).__init__("super", theClass, ctx)
    def Class(self) -> Class:
        return self.enclosingScope

'''
 * 代表一个缺省的构造函数。
 * 这不是在程序里声明的。因此没有对应的FunctionDeclarationContext
'''
class DefaultConstructor(Function):
    def __init__(self, name:str, theClass:Class):
        super(DefaultConstructor, self).__init__(name, theClass, None)
    def Class(self) -> Class:
        return self.enclosingScope

class Class(Scope, Type):
    def __init__(self, name, ctx:ParserRuleContext):
        super().__init__()
        self.name = name
        self.ctx = ctx
        self.parentClass:Class = None  #= rootClass;
        # 这个类的This变量
        self.thisRef:This = None
        self.superRef:Super = None
        self.thisRef:This = This(self, ctx)
        self.thisRef.type = self
        self.defaultConstructor:DefaultConstructor = None
    
    def getParentClass(self) -> Class:
        return self.parentClass
    
    def setParentClass(self, theClass:Class):
        self.parentClass = theClass
        # 其实superRef引用的也是自己
        self.superRef = Super(self.parentClass, self.ctx)
        self.superRef.type = self.parentClass

    def getThis(self) -> This:
        return self.thisRef

    def getSuper(self) -> Super:
        return self.superRef

    def toString(self) -> str:
        return "Class " + self.name

    # 是否包含某个Class
    # override
    def getClass(self, name:str) -> Class:
        rtn = super(Class, self).getClass(name)
        if rtn is None and self.parentClass:
            rtn = self.parentClass.getClass(name)  # TODO 是否要检查visibility?
        return rtn

    # 找到某个构建函数。不需要往父类去找，在本级找就行了
    def findConstructor(self, paramTypes:List[Type]) -> Function:
        rtn = super(Class, self).getFunction(self.name, paramTypes)  # TODO 是否要检查visibility?
        return rtn

    # 是否包含某个 Variable，包括自身及父类
    # override
    def getVariable(self, name:str) -> Variable:
        rtn = super(Class, self).getVariable(name)
        if rtn is None and self.parentClass:
            rtn = self.parentClass.getVariable(name)  # TODO 是否要检查visibility
        return rtn

    '''
     * 在自身及父类中找到某个方法
     * override
     * @param name
     * @param paramTypes 参数类型列表。该参数不允许为空。如果没有参数，需要传入一个0长度的列表。
    '''
    def getFunction(self, name, paramTypes:List[Type]) -> Function:
        # 在本级查找这个这个方法
        rtn = super(Class, self).getFunction(name, paramTypes)  # TODO 是否要检查visibility?
        # 如果在本级找不到，那么递归的从父类中查找
        if rtn == None and self.parentClass:
            rtn = self.parentClass.getFunction(name,paramTypes)
        return rtn

    def getFunctionVariable(self, name, paramTypes:List[Type]) -> Variable:
        rtn = super(Class, self).getFunctionVariable(name, paramTypes)  # TODO 是否要检查visibility?
        if rtn is None and self.parentClass:
            rtn = self.parentClass.getFunctionVariable(name, paramTypes)
        return rtn

    # 是否包含某个Symbol。这时候要把父类的成员考虑进来
    # Override
    def containsSymbol(self, symbol:Symbol) -> bool:
        # this super 关键字
        if symbol == self.thisRef or symbol == self.superRef:
            return True
        rtn = False
        rtn = symbol in self.symbols
        if not rtn and self.parentClass:
            rtn = self.parentClass.containsSymbol(symbol)
        return rtn

    # 当自身是目标类型的子类型的时候，返回true
    # Override
    def isType(self, type:Type) -> bool:
        if self == type:
            return True  # shortcut
        if isinstance(type, Class):
            return type.isAncestor(self)
        return False

    # 本类型是不是另一个类型的祖先类型
    def isAncestor(self, theClass:Class):
        if theClass.getParentClass():
            if theClass.getParentClass() == self:
                return True
            else:
                return self.isAncestor(theClass.getParentClass())
        return False

    def getDefaultConstructor(self) -> DefaultConstructor:
        if self.defaultConstructor is None:
            self.defaultConstructor = DefaultConstructor(self.name, self)
        return self.defaultConstructor

# 最顶层的基类
rootClass:Class = Class("Object", None)


class CompilationLog():
    class Type(enum.Enum):
        INFO = 0
        WARN = 1
        ERROR = 2

    def __init__(self):
        self.ctx:ParserRuleContext = None
        self.message = None
        self.line = None
        self.positionInLine = None
        self.type = None

class AnnotatedTree():
    def __init__(self):
        # AST
        self.ast = None
        
        # 解析出来的所有类型，包括类和函数，将来还可以包括数组和枚举。类的方法也作为单独的要素放进去。
        # List<Type>
        self.types = []

        # AST节点对应的Symbol
        # Map<ParserRuleContext, Symbol>
        self.symbolOfNode = {}

        # AST节点对应的Scope，如for、函数调用会启动新的Scope
        # Map<ParserRuleContext, Scope>
        self.node2Scope = {}

        # 用于做类型推断，每个节点推断出来的类型
        # Map<ParserRuleContext, Type>
        self.typeOfNode = {}

        # 语义分析过程中生成的信息，包括普通信息、警告、错误
        # List<CompilationLog>
        self.logs = []

        # 在构造函数里,引用的this()。第二个函数是被调用的构造函数
        self.thisConstructorRef = {}  # Map<Function, Function>

        # 在构造函数里,引用的super()。第二个函数是被调用的构造函数
        self.superConstructorRef = {}  # Map<Function, Function>

    '''
     * 查找某节点所在的Scope
     * 算法：逐级查找父节点，找到一个对应着Scope的节点，返回其Scope
    '''
    def enclosingScopeOfNode(self, node:ParserRuleContext):
        rtn:Scope = None
        parent = node.parentCtx
        if parent:
            rtn = self.node2Scope.get(parent, None)
            if rtn is None:
                rtn = self.enclosingScopeOfNode(parent)
        return rtn
    
    '''
     * 包含某节点的函数
    '''
    def enclosingFunctionOfNode(self, ctx:RuleContext):
        if isinstance(ctx.parentCtx, PlayScriptParser.FunctionDeclarationContext):
            return self.node2Scope[ctx.parentCtx]
        elif ctx.parentCtx is None:
            return None
        else:
            return self.enclosingFunctionOfNode(ctx.parentCtx)
    
    '''
     * 包含某节点的类
    '''
    def enclosingClassOfNode(self, ctx:RuleContext):
        if isinstance(ctx.parentCtx, PlayScriptParser.ClassDeclarationContext):
            return self.node2Scope[ctx.parentCtx]
        elif ctx.parentCtx is None:
            return None
        else:
            return self.enclosingClassOfNode(ctx.parentCtx)

    '''
     * 通过名称查找Variable。逐级Scope查找
    '''
    def lookupVariable(self, scope:Scope, idName:str):
        rtn:Variable = scope.getVariable(idName)
        if rtn is None and scope.enclosingScope:
            rtn = self.lookupVariable(scope.enclosingScope, idName)
        return rtn

    '''
     * 通过名称查找Class。逐级Scope查找。
    '''
    def lookupClass(self, scope:Scope, idName:str):
        rtn:Class = scope.getClass(idName)
        if rtn is None and scope.enclosingScope:
            rtn = self.lookupClass(scope.enclosingScope, idName)
        return rtn

    def lookupType(self, idName):   # TODO 单纯根据名称并不严密
        rtn:Type = None
        for type in self.types:
            if type.getName() == idName:
                rtn = type
                break
        return rtn

    '''
     * 通过方法的名称和方法签名查找Function。逐级Scope查找。
    '''
    def lookupFunction(self, scope:Scope, idName:str, paramTypes):
        rtn:Function = scope.getFunction(idName, paramTypes)
        if rtn is None and scope.enclosingScope:
            rtn = self.lookupFunction(scope.enclosingScope, idName, paramTypes)
        return rtn
    
    '''
     * 查找函数型变量，逐级查找。
    '''
    def lookupFunctionVariable(self, scope:Scope, idName:str, paramTypes):
        rtn:Variable = scope.getFunctionVariable(idName, paramTypes)
        if rtn is None and scope.enclosingScope:
            rtn = self.lookupFunctionVariable(scope.enclosingScope, idName, paramTypes)
        return rtn

    '''
    * 逐级查找函数（或方法）。仅通过名字查找。如果有重名的，返回第一个就算了。//TODO 应该报警。
    '''
    def lookupFunctionOnlyByName(self, scope:Scope, name:str):
        rtn:Function = None
        if isinstance(scope, Class):
            rtn = self.getMethodOnlyByName(scope, name)
        else:
            rtn = self.getFunctionOnlyByName(scope, name)

        if rtn is None and scope.enclosingScope:
            rtn = self.lookupFunctionOnlyByName(scope.enclosingScope, name)
        return rtn
    
    # 对于类，需要连父类也查找
    def getMethodOnlyByName(self, theClass:Scope, name:str):
        rtn:Function = self.getFunctionOnlyByName(theClass, name)
        if rtn is None and theClass.getParentClass():
            rtn = self.getMethodOnlyByName(theClass.getParentClass(), name)
        return rtn

    def getFunctionOnlyByName(self, scope, name):
        for s in scope.symbols:
            if isinstance(s, Function) and s.name == name:
                return s
        return None

    def log(self, message:str, type:CompilationLog.Type, ctx:ParserRuleContext):
        log = CompilationLog()
        log.ctx = ctx
        log.message = message
        # 这里获取ctx对应的行号，应该不叫 getStart 接口了
        log.line = ctx.start.line
        log.positionInLine = ctx.start.column
        log.type = type

        self.logs.append(log)
    
    def log_error(self, message:str, ctx:ParserRuleContext):
        log = CompilationLog()
        log.ctx = ctx
        log.message = message
        # 这里获取ctx对应的行号，应该不叫 getStart 接口了
        log.line = ctx.start.line
        log.positionInLine = ctx.start.column
        log.type = CompilationLog.Type.ERROR

        self.logs.append(log)
    
    def hasCompilationError(self):
        for log in self.logs:
            if log.type == CompilationLog.Type.ERROR:
                return True
        return False
    
    def show_log(self):
        for log in self.logs:
            typ_str = None
            if log.type == CompilationLog.Type.ERROR:
                typ_str = 'ERROR'
            elif log.type == CompilationLog.Type.INFO:
                typ_str = 'INFO'
            elif log.type == CompilationLog.Type.WARN:
                typ_str = 'WARN'
            line = '[' + typ_str + '] [' + str(log.line) + ', ' + str(log.positionInLine) + '] ' + log.message
            print(line)


'''
* 第一遍扫描：
* 建立作用域关系树，包括 BlockScope、Function、Class
* 识别出所有自定义的类型，包括：函数和类
'''
class TypeAndScopeScanner(PlayScriptListener):
    def __init__(self, at):
        super().__init__()
        self.at:AnnotatedTree = at
        self.scopeStack = []

    def pushScope(self, scope:Scope):
        self.scopeStack.append(scope)

    def popScope(self):
        self.scopeStack.pop()

    # 在遍历树的过程中，获取当前的Scope
    def currentScope(self):
        if len(self.scopeStack) > 0:
            return self.scopeStack[-1]
        else:
            return None

    #############################################

    def enterProg(self, ctx:PlayScriptParser.ProgContext):
        # 开局建立一个根作用域，用BlockScope来表示
        scope = BlockScope(self.currentScope(), ctx)
        self.at.node2Scope[ctx] = scope  # 这是整个语义分析 计算的第一个属性-值
        self.pushScope(scope)
    
    def exitProg(self, ctx:PlayScriptParser.ProgContext):
        self.popScope()

    def enterBlock(self, ctx:PlayScriptParser.BlockContext):
        # 对于函数，不需要再额外建一个scope
        if not isinstance(ctx.parentCtx, PlayScriptParser.FunctionBodyContext):
            scope = BlockScope(self.currentScope(), ctx)
            self.at.node2Scope[ctx] = scope
            self.currentScope().addSymbol(scope)
            self.pushScope(scope)

    def exitBlock(self, ctx:PlayScriptParser.BlockContext):
        if not isinstance(ctx.parentCtx, PlayScriptParser.FunctionBodyContext):
            self.popScope()

    def enterStatement(self, ctx:PlayScriptParser.StatementContext):
        # 为 for 建立额外的 Scope，如: for (int i=0; ...)
        if ctx.FOR():
            scope = BlockScope(self.currentScope(), ctx)
            self.at.node2Scope[ctx] = scope
            self.currentScope().addSymbol(scope)
            self.pushScope(scope)

    def exitStatement(self, ctx:PlayScriptParser.StatementContext):
        if ctx.FOR():
            self.popScope()

    def enterFunctionDeclaration(self, ctx:PlayScriptParser.FunctionDeclarationContext):
        funcName = ctx.IDENTIFIER().getText()
        # 注意：目前funtion的信息并不完整，参数类型要在 TypeResolver.py 中去确定
        function = Function(funcName, self.currentScope(), ctx)
        self.at.types.append(function)
        self.at.node2Scope[ctx] = function
        self.currentScope().addSymbol(function)
        self.pushScope(function)

    def exitFunctionDeclaration(self, ctx:PlayScriptParser.FunctionDeclarationContext):
        self.popScope()

    def enterClassDeclaration(self, ctx:PlayScriptParser.ClassDeclarationContext):
        # 把类的签名存到符号表中，不能跟已有符号名称冲突
        idName:str = ctx.IDENTIFIER().getText()
        theClass = Class(idName, ctx)
        self.at.types.append(theClass)

        # 这里是我们第一次做语义检查，并输出报警信息
        if self.at.lookupClass(self.currentScope(), idName):
            self.at.log_error("duplicate class name:" + idName, ctx)  # 只是报警，但仍然继续解析
        self.currentScope().addSymbol(theClass)
        self.at.node2Scope[ctx] = theClass
        self.pushScope(theClass)

    def exitClassDeclaration(self, ctx:PlayScriptParser.ClassDeclarationContext):
        self.popScope()

'''
 * 第二遍扫描：
 * 类型I属性计算，包括：变量声明语句、函数声明语句、类继承语句，即所有用到 typeTpe（语法规则） 的地方
 * Symbol化：针对函数形参和类成员变量，生成Symbol（Variable），添加到各自的作用域里（符号表）
 * 
 * 注意：
 * 这一步，并非把所有变量都Symbol化，并加入到符号表里，而是只涉及函数形参和类成员变量（class里的类成员变量允许先使用后定义，函数形参先天就是先定义后使用的，所以这里可以先Symbol化）
 * 最终把所有变量声明 都Symbol化并添加到符号表里，是分两步做的（变量声明有3类：类成员、函数形参、block内）
 * 第一步，是把类成员变量和函数形参 加进去（这一步）
 * 第二步，是在变量引用消解（RefResolver）的时候再添加：如果遇到了block里的 variableDeclarators 语句，才将变量Symbol化并添加到符号表里。
 *        这样在消解后面expression里的变量时，才能引用到正确的定义。注：这是参考C语言，block里（块作用域/函数体）的变量不允许先使用后声明。
 *
'''
class TypeResolver(PlayScriptListener):
    def __init__(self, at, enterLocalVariable:bool=False):
        super().__init__()
        self.at = at
        self.enterLocalVariable = enterLocalVariable  # 是否针对本地变量（block内的变量）生成Symbol

    # 设置变量声明语句里变量的类型 (I属性)
    def exitVariableDeclarators(self, ctx:PlayScriptParser.VariableDeclaratorsContext):
        scope:Scope = self.at.enclosingScopeOfNode(ctx)
        if isinstance(scope, Class) or self.enterLocalVariable:
            # 设置变量类型
            # print(ctx.start.line, ', ', ctx.start.column)
            type:Type = self.at.typeOfNode[ctx.typeType()]
            for child in ctx.variableDeclarator():
                variable:Variable = self.at.symbolOfNode[child.variableDeclaratorId()]
                variable.type = type
                # added code:
                self.at.typeOfNode[child.variableDeclaratorId()] = type

    # 把类成员变量/函数形参 的声明加入符号表
    def enterVariableDeclaratorId(self, ctx:PlayScriptParser.VariableDeclaratorIdContext):
        idName:str = ctx.IDENTIFIER().getText()
        scope:Scope = self.at.enclosingScopeOfNode(ctx)

        # 第一步只把 类成员变量/函数形参 加入符号表。
        # 下一步（enterLocalVariable==True），在变量消解时，再把其余变量加入符号表
        if isinstance(scope, Class) or self.enterLocalVariable or isinstance(ctx.parentCtx, PlayScriptParser.FormalParameterContext):
            variable:Variable = Variable(idName, scope, ctx)
            # 变量查重，比如：void func(int a, string a) { int a, b, b;}
            if scope.getVariable(idName):
                # self.at.log_error("Variable or parameter already Declared: " + idName, ctx)
                pass
                # TODO 上面的报错我先注释掉了，因为遇到一个问题：
                # 如果class A 里定义了 weight变量，class B 继承 class A，也定义了weight变量，这里不该报错吧？见test-class-4-this-super.play
                # class作为scope去getVariable是可以找到父类的定义的变量的，如果遇到同名变量，是否报错？
            scope.addSymbol(variable)
            self.at.symbolOfNode[ctx] = variable
    
    # 设置函数形参的类型，这些参数已经在 enterVariableDeclaratorId中Symbol化了，现在设置它们的类型
    def exitFormalParameter(self, ctx:PlayScriptParser.FormalParameterContext):
        # I属性计算
        type:Type = self.at.typeOfNode[ctx.typeType()]
        variable:Variable = self.at.symbolOfNode[ctx.variableDeclaratorId()]
        variable.type = type
        # 添加到Function的参数列表里
        scope = self.at.enclosingScopeOfNode(ctx)
        if isinstance(scope, Function):    # 从当前的语法看，只有function才会使用FormalParameter
            scope.parameters.append(variable)  # Function定义处/函数体 的参数实体

    # 设置函数的返回值类型
    def exitFunctionDeclaration(self, ctx:PlayScriptParser.FunctionDeclarationContext):
        function:Function = self.at.node2Scope[ctx]
        if ctx.typeTypeOrVoid():
            function.returnType = self.at.typeOfNode[ctx.typeTypeOrVoid()]
        else:
            # 如果是类的构建函数，返回值类型应该是一个类
            if function.isConstructor():
                function.returnType = function.getEnclosingScope()
            pass
        # 到这里，每个 Function，作为函数体/FunctionType/Scope/Symbol，所有的信息都齐了，包括 name/returnType/paramTypes/parameters
        # 函数查重，检查名称和参数：
        scope:Scope = self.at.enclosingScopeOfNode(ctx)
        found = scope.getFunction(function.name, function.getParamTypes())
        if found and found != function:
            # 这个查重逻辑，乍一看是有问题的，但你试想一下同一作用域下定义了两个相同函数的情况，就知道这段代码是能wrok的
            # 但这里有隐患，因为这里不是一报错就停下来，还会继续后面的语义分析，同一Scope里存在了两个/多个相同函数，是有问题的
            self.at.log_error("Function or method already Declared: " + ctx.getText(), ctx)

    # 设置类的父类
    def enterClassDeclaration(self, ctx:PlayScriptParser.ClassDeclarationContext):
        theClass:Class = self.at.node2Scope[ctx]
        # 设置父类
        if ctx.EXTENDS():
            parentClassName:str = ctx.typeType().getText()
            # 由于暂不支持内部类，所以这里的 classType 不会出现 ID.ID 的情况
            type = self.at.lookupType(parentClassName)
            if type and isinstance(type, Class):
                # PlayScript 目前只支持单继承（链式），不支持多继承（菱形）
                theClass.setParentClass(type)
            else:
                self.at.log_error("unknown class: " + parentClassName, ctx)

    def exitTypeTypeOrVoid(self, ctx:PlayScriptParser.TypeTypeOrVoidContext):
        if ctx.VOID():
            self.at.typeOfNode[ctx] = voidType
        elif ctx.typeType():
            self.at.typeOfNode[ctx] = self.at.typeOfNode[ctx.typeType()]

    def exitTypeType(self, ctx:PlayScriptParser.TypeTypeContext):
        # 冒泡，将下级的属性标注在本级 （I属性推导）
        if ctx.classType():
            type = self.at.typeOfNode[ctx.classType()]
            self.at.typeOfNode[ctx] = type
        elif ctx.functionType():
            type = self.at.typeOfNode[ctx.functionType()]
            self.at.typeOfNode[ctx] = type
        elif ctx.primitiveType():
            type = self.at.typeOfNode[ctx.primitiveType()]
            self.at.typeOfNode[ctx] = type

    def enterClassType(self, ctx:PlayScriptParser.ClassTypeContext):
        if ctx.IDENTIFIER():
            scope:Scope = self.at.enclosingScopeOfNode(ctx)
            idName:str = ctx.getText()
            # 因为暂不支持内部类，所以不会出现 ID.ID 的类名
            theClass:Class = self.at.lookupClass(scope, idName)
            if theClass is None:
                # 因为需要检查错误，所以要在enter里做，这样如果要报错终止编译，就更快了
                self.at.log_error("unknown class: " + idName, ctx)
            self.at.typeOfNode[ctx] = theClass

    # 这里针对函数变量（一等公民）的定义语句，加入一个函数类型(FunctionType)
    # function int(int, string) func;
    # TODO 判重，对于返回值和形参类型完全一致的 FunctionType，仅保留一个实体就好
    def exitFunctionType(self, ctx:PlayScriptParser.FunctionTypeContext):
        # 这里发现：function int() a = func()  中的 function int() 作为FunctionType被定义了两次，
        # 由于 at.types 列表会一直记录它们，所以前面定义的FunctionType会得不到释放，造成内存泄漏
        # 这是因为 TypeResolver 和 RefResolver 在解析到 variableDeclarators 语句时，都会回调这里，所以要预防一下
        if self.enterLocalVariable:
            return
        functionType = DefaultFunctionType()
        # print('++:  ' + str(ctx.start.line) + ', ' + str(ctx.start.column))
        self.at.types.append(functionType)
        self.at.typeOfNode[ctx] = functionType
        functionType.returnType = self.at.typeOfNode[ctx.typeTypeOrVoid()]
        # 参数的类型
        if ctx.typeList():
            for ttc in ctx.typeList().typeType():
                type:Type = self.at.typeOfNode[ttc]
                functionType.paramTypes.append(type)

    def exitPrimitiveType(self, ctx:PlayScriptParser.PrimitiveTypeContext):
        # TODO 同上，但不会造成内存泄漏，只是重复赋了相同type实例而已，所以不管了
        type:Type = None
        if ctx.BOOLEAN():
            type = Boolean
        elif ctx.INT():
            type = Integer
        elif ctx.FLOAT():
            type = Float
        elif ctx.STRING():
            type = String
        self.at.typeOfNode[ctx] = type


'''
 * 第3遍扫描：引用消解和类型推断
 * 1.消解所有的引用，即出现在 expression 里的符号，包括：变量、函数调用、类成员（如上述所说，在按顺序遍历AST消解引用的过程中，同时会针对block里的变量声明，进行Symbol化并添加到作用域里）
 * 2.类型推断：从下而上推断表达式的类型（S属性）
 * 这两件事要放在一起做，因为：
 * (1)对于变量，只有做了消解，才能推断出类型来。
 * (2)对于FunctionCall，只有把参数（表达式)的类型都推断出来，才能匹配到正确的函数（方法)。
 * (3)表达式里包含FunctionCall，如果要推导表达式的类型，必须知道是哪个Function，才能得到返回值。
 *
'''
class RefResolver(PlayScriptListener):
    def __init__(self, at:AnnotatedTree):
        super().__init__()
        self.at = at
        # 用于把本地变量（剩下的未被Variable化的变量）添加到符号表，并计算类型
        self.typeResolverWalker = ParseTreeWalker()
        self.localVariableEnter = TypeResolver(at, True)
        # this()和super()构造函数留到最后去消解，因为它可能引用别的构造函数，必须等这些构造函数都消解完。
        self.thisConstructorList:List[PlayScriptParser.FunctionCallContext]  = []
        self.superConstructorList:List[PlayScriptParser.FunctionCallContext] = []

    # 把本地变量（即block里定义的变量）加到符号表，必须是边添加，边解析，不能先添加后解析，否则会引起引用消解的错误
    # 这么做的目的：块作用域/函数体 里，不允许变量 先使用后声明，但class里可以
    # 例子：
    # int a = 2;
    # void fun() {
    #   println(a);
    #   int a = 3;
    #   println(a);
    # }
    def enterVariableDeclarators(self, ctx:PlayScriptParser.VariableDeclaratorsContext):
        scope = self.at.enclosingScopeOfNode(ctx)
        if isinstance(scope, BlockScope) or isinstance(scope, Function):
            self.typeResolverWalker.walk(self.localVariableEnter, ctx)

    def exitPrimary(self, ctx:PlayScriptParser.PrimaryContext):
        scope = self.at.enclosingScopeOfNode(ctx)
        type = None
        # 标识符
        if ctx.IDENTIFIER():
            # 变量的引用消解
            idName = ctx.IDENTIFIER().getText()
            variable:Variable = self.at.lookupVariable(scope, idName)
            if variable is None:
                # 看看是不是函数，因为函数可以作为值来传递。这个时候，函数重名没法区分
                # 因为普通Scope中的函数是不可以重名的，所以这应该是没有问题的
                # TODO 注意，查找function的时候，可能会把类的方法包含进去，是否需要调整？
                # TODO 想象这里为什么不能：针对每个FunctionDeclaration，建立一个Variable，这样就不需要在这里对Function进行特别处理了。
                # int a;
                # void a()
                # {
                #    println(a);  // 这里你希望a是引用函数a，还是外部的整型a？
                # }
                function:Function = self.at.lookupFunctionOnlyByName(scope, idName)
                if function:
                    self.at.symbolOfNode[ctx] = function
                    type = function
                else:
                    self.at.log_error("unknown variable or function: " + idName, ctx)
            else:
                self.at.symbolOfNode[ctx] = variable
                type = variable.type
        # 字面量
        elif ctx.literal():
            type = self.at.typeOfNode[ctx.literal()]
        # 括号里的表达式
        elif ctx.expression():
            type = self.at.typeOfNode[ctx.expression()]
        # this关键字
        elif ctx.THIS():
            # 找到Class类型的上级Scope
            theClass:Class = self.at.enclosingClassOfNode(ctx)
            if theClass:
                variable:This = theClass.getThis()
                self.at.symbolOfNode[ctx] = variable
                type = theClass
            else:
                self.at.log_error("keyword \"this\" can only be used inside a class", ctx)
        # super关键字。看上去跟This关键字的用法完全一样？
        elif ctx.SUPER():
            # 找到Class类型的上级Scope
            theClass:Class = self.at.enclosingClassOfNode(ctx)
            if theClass:
                variable:Super = theClass.getSuper()
                self.at.symbolOfNode[ctx] = variable
                type = theClass
            else:
                self.at.log_error("keyword \"super\" can only be used inside a class", ctx)

        # 类型推断、冒泡
        self.at.typeOfNode[ctx] = type


    def exitFunctionCall(self, ctx:PlayScriptParser.FunctionCallContext):
        # this
        if ctx.THIS():
            self.thisConstructorList.append(ctx)
            return
        # super
        elif ctx.SUPER():
            self.superConstructorList.append(ctx)
            return

        # TODO 临时代码，支持println
        if ctx.IDENTIFIER().getText() == "println":
            return

        idName = ctx.IDENTIFIER().getText()
        # 获得参数类型，这些类型已经在表达式中推断出来
        paramTypes = self.getParamTypes(ctx)
        found = False

        # 看看是不是点符号表达式调用的，调用的是类的方法
        if isinstance(ctx.parentCtx, PlayScriptParser.ExpressionContext):
            exp:PlayScriptParser.ExpressionContext = ctx.parentCtx
            if exp.bop and exp.bop.type == PlayScriptParser.DOT:
                symbol:Symbol = self.at.symbolOfNode[exp.expression(0)]
                if isinstance(symbol, Variable) and isinstance(symbol.type, Class):
                    theClass = symbol.type
                    # 查找名称和参数类型都匹配的函数。不允许名称和参数都相同，但返回值不同的情况（C++和Java都不允许这种情况吧）
                    function:Function = theClass.getFunction(idName, paramTypes)
                    if function:
                        found = True
                        self.at.symbolOfNode[ctx] = function
                        self.at.typeOfNode[ctx] = function.getReturnType()
                    else:
                        funcVar:Variable = theClass.getFunctionVariable(idName, paramTypes)
                        if funcVar:
                            found = True
                            self.at.symbolOfNode[ctx] = funcVar
                            self.at.typeOfNode[ctx] = funcVar.type.getReturnType()
                        else:
                            self.at.log_error("unable to find method " + idName + " in Class " + theClass.name, exp)
                else:
                    self.at.log_error("unable to resolve a class", ctx)

        scope = self.at.enclosingScopeOfNode(ctx)
        # 从当前Scope逐级查找函数(或方法)
        if not found:
            function = self.at.lookupFunction(scope, idName, paramTypes)
            if function:
                found = True
                self.at.symbolOfNode[ctx] = function  # 函数引用消解
                self.at.typeOfNode[ctx] = function.returnType  # 表达式类型推导（S属性）

        if not found:
            # 看看是不是类的构建函数，用相同的名称查找一个class
            theClass = self.at.lookupClass(scope, idName)
            if theClass:
                function:Function = theClass.findConstructor(paramTypes)
                if function:
                    found = True
                    self.at.symbolOfNode[ctx] = function
                # 如果是与类名相同的方法，并且没有参数，那么就是缺省构造方法
                elif ctx.expressionList() is None:
                    found = True
                    # self.at.symbolOfNode[ctx] = theClass  # TODO 直接赋予class
                    self.at.symbolOfNode[ctx] = theClass.getDefaultConstructor()
                else:
                    self.at.log_error("unknown class constructor: " + ctx.getText(), ctx)
                self.at.typeOfNode[ctx] = theClass  # 这次函数调用是返回一个对象
            # 看看是不是一个函数型的变量
            else:
                variable:Variable = self.at.lookupFunctionVariable(scope, idName, paramTypes)
                if variable and isinstance(variable.type, FunctionType):
                    found = True
                    self.at.symbolOfNode[ctx] = variable
                    self.at.typeOfNode[ctx] = variable.type.getReturnType()  # TODO: 这里原来是：self.at.typeOfNode[ctx] = variable.type，应该有问题
                else:
                    self.at.log_error("unknown function or function variable: " + ctx.getText(), ctx)

    '''
     * 获得函数的参数列表
    '''
    def getParamTypes(self, ctx:PlayScriptParser.FunctionCallContext):
        paramTypes = []
        if ctx.expressionList():
            for exp in ctx.expressionList().expression():
                type:Type = self.at.typeOfNode[exp]
                paramTypes.append(type)
        return paramTypes

    # 要消解处理点符号表达式的层层引用
    def exitExpression(self, ctx:PlayScriptParser.ExpressionContext):
        type:Type = None

        if ctx.bop and ctx.bop.type == PlayScriptParser.DOT:
            # 这是个左递归，要不断的把左边的节点的计算结果存到 node2Symbol，所以要在exitExpression里操作
            symbol:Symbol = self.at.symbolOfNode[ctx.expression(0)]
            if isinstance(symbol, Variable) and isinstance(symbol.type, Class):
                theClass:Class = symbol.type
                # 引用类的属性
                if ctx.IDENTIFIER():
                    idName:str = ctx.IDENTIFIER().getText()
                    variable:Variable = self.at.lookupVariable(theClass, idName)  # 在类的scope里去查找，不需要改变当前的scope
                    if variable:
                        self.at.symbolOfNode[ctx] = variable
                        type = variable.type  # 类型综合（冒泡)
                    else:
                        self.at.log_error("unable to find field " + idName + " in Class " + theClass.name, ctx)
                # 引用类的方法
                elif ctx.functionCall():
                    type = self.at.typeOfNode[ctx.functionCall()]
            else:
                self.at.log_error("symbol is not a qualified object：" + symbol, ctx)
        # 变量引用冒泡： 如果下级是一个变量，往上冒泡传递，以便在点符号表达式中使用
        # 也包括This和Super的冒泡
        elif ctx.primary():
            # 对于涉及到点号表达式的，如 mammal.speak()，这里的mammal需要记录好引用的谁，在exitPrimary中已经有记录了，在exitExpression这里要往上传
            # 注意：只有点号表达式里的 expression->primary 才需要这样处理。对于一般的 expression->primary，不需要把Symbol往上传，如 a = 2 or a = b or a = 2*b+3，就不用。2根本不存在Symbol。
            symbol:Symbol = self.at.symbolOfNode.get(ctx.primary(), None)
            if symbol:
                self.at.symbolOfNode[ctx] = symbol

        # 类型推断和综合。S属性
        if ctx.primary():
            type = self.at.typeOfNode[ctx.primary()]
        elif ctx.functionCall():
            if ctx.functionCall() in self.at.typeOfNode:
                type = self.at.typeOfNode[ctx.functionCall()]
            else:
                # ?
                return
        elif ctx.bop and len(ctx.expression()) == 2:
            # TODO  ? : 三目运算符，这里还无法推导类型，需要先计算第一个expression的值，才能推导
            type1 = self.at.typeOfNode[ctx.expression(0)]
            type2 = self.at.typeOfNode[ctx.expression(1)]
            bop_type = ctx.bop.type
            
            if bop_type == PlayScriptParser.ADD:
                if type1 == String or type2 == String:
                    type = String
                elif isinstance(type1, PrimitiveType) and isinstance(type2, PrimitiveType):
                    # 类型“向上”对齐，比如一个int和一个float，取float
                    type = PrimitiveType.getUpperType(type1, type2)
                else:
                    self.at.log_error("operand should be PrimitiveType for additive and multiplicative operation", ctx)
            elif bop_type in [PlayScriptParser.SUB, PlayScriptParser.MUL, PlayScriptParser.DIV]:
                if isinstance(type1, PrimitiveType) and isinstance(type2, PrimitiveType):
                    type = PrimitiveType.getUpperType(type1, type2)
                else:
                    self.at.log_error("operand should be PrimitiveType for additive and multiplicative operation", ctx)
            elif bop_type == PlayScriptParser.MOD:
                type = Integer  # TODO
            elif bop_type in [PlayScriptParser.EQUAL, PlayScriptParser.NOTEQUAL, PlayScriptParser.LE, PlayScriptParser.LT, PlayScriptParser.GE, \
                PlayScriptParser.GT, PlayScriptParser.AND, PlayScriptParser.OR]:
                type = Boolean
            elif bop_type in [PlayScriptParser.ASSIGN]:
                type = type1
            elif bop_type in [PlayScriptParser.ADD_ASSIGN, PlayScriptParser.SUB_ASSIGN, PlayScriptParser.MUL_ASSIGN, PlayScriptParser.DIV_ASSIGN]:
                type = type1
            elif bop_type == PlayScriptParser.MOD_ASSIGN:
                type = Integer  # TODO
        elif ctx.prefix != None:
            prefix = ctx.prefix.type
            if prefix == PlayScriptParser.BANG:
                type = Boolean
            elif prefix in [PlayScriptParser.ADD, PlayScriptParser.SUB, PlayScriptParser.INC, PlayScriptParser.DEC]:
                type = self.at.typeOfNode[ctx.expression(0)]
        elif ctx.postfix != None:
            type = self.at.typeOfNode[ctx.expression(0)]
        elif ctx.LBRACK() != None:
            pass  # 数组索引
        # 类型冒泡
        self.at.typeOfNode[ctx] = type


    # 对变量初始化部分也做一下类型推断（S属性）
    def exitVariableInitializer(self, ctx:PlayScriptParser.VariableInitializerContext):
        if ctx.expression():
            self.at.typeOfNode[ctx] = self.at.typeOfNode[ctx.expression()]

    # 根据字面量来推断类型（S属性）
    def exitLiteral(self, ctx:PlayScriptParser.LiteralContext):
        if ctx.BOOL_LITERAL():
            self.at.typeOfNode[ctx] = Boolean
        elif ctx.NULL_LITERAL():
            self.at.typeOfNode[ctx] = Null
        elif ctx.STRING_LITERAL():
            self.at.typeOfNode[ctx] = String
        elif ctx.integerLiteral():
            self.at.typeOfNode[ctx] = Integer
        elif ctx.floatLiteral():
            self.at.typeOfNode[ctx] = Float

    # 在结束扫描之前，把this()和super()构造函数消解掉
    def exitProg(self, ctx:PlayScriptParser.ProgContext):
        for fcc in self.thisConstructorList:
            self.resolveThisConstructorCall(fcc)
        for fcc in self.superConstructorList:
            self.resolveSuperConstructorCall(fcc)

    # 消解this()构造函数
    def resolveThisConstructorCall(self, ctx:PlayScriptParser.FunctionCallContext):
        theClass:Class = self.at.enclosingClassOfNode(ctx)
        if theClass:
            function:Function = self.at.enclosingFunctionOfNode(ctx)
            if function and function.isConstructor():
                # 检查是不是构造函数中的第一句
                fdx:PlayScriptParser.FunctionDeclarationContext = function.ctx
                if not self.firstStatmentInFunction(fdx, ctx):
                    self.at.log_error("this() must be first statement in a constructor", ctx)
                    # return
                paramTypes:List[Type] = self.getParamTypes(ctx)
                refered:Function = theClass.findConstructor(paramTypes)
                if refered:
                    self.at.symbolOfNode[ctx] = refered
                    self.at.typeOfNode[ctx] = theClass
                    self.at.thisConstructorRef[function] = refered
                elif len(paramTypes) == 0:  # 缺省构造函数
                    self.at.symbolOfNode[ctx] = theClass.getDefaultConstructor()
                    self.at.typeOfNode[ctx] = theClass
                    self.at.thisConstructorRef[function] = theClass.getDefaultConstructor()
                else:
                    self.at.log_error("can not find a constructor matches this()", ctx)
            else:
                self.at.log_error("this() should only be called inside a class constructor", ctx)
        else:
            self.at.log_error("this() should only be called inside a class", ctx)

    def firstStatmentInFunction(self, fdx:PlayScriptParser.FunctionDeclarationContext, ctx:PlayScriptParser.FunctionCallContext) -> bool:
        if fdx.functionBody().block().blockStatements().blockStatement(0).statement() \
            and fdx.functionBody().block().blockStatements().blockStatement(0).statement().expression() \
            and fdx.functionBody().block().blockStatements().blockStatement(0).statement().expression().functionCall() == ctx:
            return True
        return False

    '''
     * 消解Super()构造函数
     * TODO 对于调用super()是有要求的，比如：
     * (1) 必须出现在构造函数的第一行，
     * (2) this()和super()不能同时出现，等等。
    '''
    def resolveSuperConstructorCall(self, ctx:PlayScriptParser.FunctionCallContext):
        theClass:Class = self.at.enclosingClassOfNode(ctx)
        if theClass:
            function:Function = self.at.enclosingFunctionOfNode(ctx)
            if function and function.isConstructor():
                parentClass:Class = theClass.getParentClass()
                if parentClass:
                    # 检查是不是构造函数中的第一句
                    fdx:PlayScriptParser.FunctionDeclarationContext = function.ctx
                    if not self.firstStatmentInFunction(fdx, ctx):
                        self.at.log_error("super() must be first statement in a constructor", ctx)
                        # return
                    paramTypes:List[Type] = self.getParamTypes(ctx)
                    refered:Function = parentClass.findConstructor(paramTypes)
                    if refered:
                        self.at.symbolOfNode[ctx] = refered
                        self.at.typeOfNode[ctx] = theClass
                        self.at.superConstructorRef[function] = refered
                    elif len(paramTypes) == 0:  # 缺省构造函数
                        self.at.symbolOfNode[ctx] = parentClass.getDefaultConstructor()
                        self.at.typeOfNode[ctx] = theClass
                        self.at.superConstructorRef[function] = parentClass.getDefaultConstructor()  # 这里原来是 theClass.getDefaultConstructor()，应该是写错了
                    else:
                        self.at.log_error("can not find a constructor matches this()", ctx)
                else:  # 父类是最顶层的基类。
                    pass    # TODO 这里暂时不处理
            else:
                self.at.log_error("super() should only be called inside a class constructor", ctx)
        else:
            self.at.log_error("super() should only be called inside a class", ctx)

'''
 * 第4遍扫描：类型检查
 * 主要检查:
 * 1.赋值表达式；
 * 2.变量初始化；
 * 3.表达式里的一些运算，比如加减乘除，是否类型匹配
 * 4.返回值的类型
'''
class TypeChecker(PlayScriptListener):
    def __init__(self, at:AnnotatedTree):
        super().__init__()
        self.at = at

    def exitVariableDeclarator(self, ctx:PlayScriptParser.VariableDeclaratorContext):
        if ctx.variableInitializer():
            variable:Variable = self.at.symbolOfNode[ctx.variableDeclaratorId()]
            type1:Type = variable.type
            type2:Type = self.at.typeOfNode[ctx.variableInitializer()]
            self.checkAssign(type1, type2, ctx, ctx.variableDeclaratorId(), ctx.variableInitializer())

    def exitExpression(self, ctx:PlayScriptParser.ExpressionContext):
        if ctx.bop and len(ctx.expression()) == 2:
            # TODO ? : 三目运算符，这里没有考虑
            type1 = self.at.typeOfNode[ctx.expression(0)]
            type2 = self.at.typeOfNode[ctx.expression(1)]
            bop_type = ctx.bop.type

            if bop_type == PlayScriptParser.ADD:
                # 字符串能够跟任何对象做 + 运算
                if type1 != String and type2 != String:
                    self.checkNumericOperand(type1, ctx, ctx.expression(0))
                    self.checkNumericOperand(type2, ctx, ctx.expression(1))
            elif bop_type in [PlayScriptParser.SUB, PlayScriptParser.MUL, PlayScriptParser.DIV, PlayScriptParser.LE, PlayScriptParser.LT, PlayScriptParser.GE, PlayScriptParser.GT]:
                self.checkNumericOperand(type1, ctx, ctx.expression(0))
                self.checkNumericOperand(type2, ctx, ctx.expression(1))
            elif bop_type in [PlayScriptParser.EQUAL, PlayScriptParser.NOTEQUAL]:
                pass
            elif bop_type in [PlayScriptParser.AND, PlayScriptParser.OR]:
                # 这里只允许boolean，是有些严格了
                self.checkBooleanOperand(type1, ctx, ctx.expression(0))
                self.checkBooleanOperand(type2, ctx, ctx.expression(1))
            elif bop_type in [PlayScriptParser.ASSIGN]:
                self.checkAssign(type1, type2, ctx, ctx.expression(0), ctx.expression(1))
            elif bop_type in [PlayScriptParser.ADD_ASSIGN, PlayScriptParser.SUB_ASSIGN, PlayScriptParser.MUL_ASSIGN, PlayScriptParser.DIV_ASSIGN, PlayScriptParser.MOD_ASSIGN]:
                if PrimitiveType.isNumeric(type2):
                    if not self.checkNumericAssign(type2, type1):
                        self.at.log_error("can not assign " + ctx.expression(1).getText() + " of type " + type2 + " to " + ctx.expression(0) + " of type " + type1, ctx)
                else:  # += 只支持数值类型，不支持 String
                    self.at.log_error("operand + " + ctx.expression(1).getText() + " should be numeric", ctx)
        # TODO 对各种一元运算做类型检查，比如NOT操作

    # 检查类型是不是数值型的
    def checkNumericOperand(self, type, exp:PlayScriptParser.ExpressionContext, operand:PlayScriptParser.ExpressionContext):
        if not PrimitiveType.isNumeric(type):
            self.at.log_error("operand for arithmetic operation should be numeric : " + operand.getText(), exp)

    # 检查类型是不是Boolean型的
    def checkBooleanOperand(self, type, exp:PlayScriptParser.ExpressionContext, operand:PlayScriptParser.ExpressionContext):
        if type != Boolean:
            self.at.log_error("operand for logical operation should be boolean : " + operand.getText(), exp)

    '''
     * 检查是否能做赋值操作
     * 看一个类型能否赋值给另一个类型，比如：
     * (1) 整型可以转成浮点型；
     * (2) 子类的对象可以赋给父类;
     * (3) 函数赋值，要求签名是一致的。
    '''
    def checkAssign(self, type1:Type, type2:Type, ctx:ParserRuleContext, operand1:ParserRuleContext, operand2:ParserRuleContext):
        if PrimitiveType.isNumeric(type2):
            if not self.checkNumericAssign(type2, type1):
                self.at.log_error("can not assign " + operand2.getText() + " of type " + type2 + " to " + operand1.getText() + " of type " + type1, ctx)
        elif type2 == String:
            if type1 == String:
                pass
            else:
                self.at.log_error("can not assign " + operand2.getText() + " of type " + type2 + " to " + operand1.getText() + " of type " + type1, ctx)
        elif isinstance(type2, Class):
            # TODO 检查类的兼容性
            pass
        elif isinstance(type2, FunctionType):
            # TODO 检查函数的兼容性
            pass
    
    # 检查一个数值类型，能否赋值给另一个数值类型，这里要求比较严格，像float->int 这种“大->小”的，都不行
    def checkNumericAssign(self, fro:Type, to:Type):
        canAssign = False
        if to == Float:
            canAssign = (fro == Integer) or (fro == Float)
        elif to == Integer:
            canAssign = (fro == Integer)
        return canAssign

'''
 * 进行一些语义检查，包括：
 * 01.break 只能出现在循环语句中，或case语句中（不支持switch-case语句）
 *
 * 02.return语句
 * 02-01 函数声明了返回值，就一定要有return语句。除非返回值类型是void。
 * 02-02 类的构造函数里如果用到return，不能带返回值。
 * 02-03 return语句只能出现在函数里。
 * 02-04 返回值类型检查，就是函数声明的返回值类型，与实际返回的值的类型，是否一致 -> (要在TypeChecker里做）（这个依赖于控制流分析，还没实现）
 *
 * 03.左值
 * 03-01 标注左值（不标注就是右值)；
 * 03-02 检查表达式能否生成合格的左值。
 *
 * 04.类的声明不能在函数里（TODO 未来应该也可以，只不过对生存期有要求）
 *
 * 05.super()和this()，只能是构造函数中的第一句。  这个在RefResolver中实现了。
 *
 * 06.
 * TODO:
 * continue 语句，必须在 for/while 循环中（暂不支持 continue 语句）
'''
class SematicValidator(PlayScriptListener):
    def __init__(self, at):
        super().__init__()
        self.at = at

    def exitPrimary(self, ctx:PlayScriptParser.PrimaryContext):
        pass
    
    def exitFunctionCall(self, ctx:PlayScriptParser.FunctionCallContext):
        pass

    def exitExpression(self, ctx:PlayScriptParser.ExpressionContext):
        pass

    def exitClassDeclaration(self, ctx:PlayScriptParser.ClassDeclarationContext):
        # 04 类的声明不能在函数里
        if self.at.enclosingFunctionOfNode(ctx):
            self.at.log_error("can not declare class inside function", ctx)

    def exitFunctionDeclaration(self, ctx:PlayScriptParser.FunctionDeclarationContext):
        # 02-01 函数定义了返回值，就一定要有相应的return语句。
        # 另外，构造函数不能有返回值（在exitStatement里做了）
        # TODO 更完善的是要进行控制流计算，不是仅仅有一个return语句就行了。
        if ctx.typeTypeOrVoid():
            if not self.hasReturnStatement(ctx):
                returnType:Type = self.at.typeOfNode[ctx.typeTypeOrVoid()]
                if returnType != voidType:
                    self.at.log_error("return statment expected in function", ctx)

    def exitStatement(self, ctx:PlayScriptParser.StatementContext):
        # 02 类的构造函数不能有返回值
        if ctx.RETURN():
            # 02-03
            function = self.at.enclosingFunctionOfNode(ctx)
            if function is None:
                self.at.log_error("return statement not in function body", ctx)
            elif function.isConstructor() and ctx.expression():
                # 02-02 构造函数不能有 return value 的语句
                self.at.log_error("can not return a value from constructor", ctx)
        # 01 break语句
        elif ctx.BREAK():
            if not self.checkBreak(ctx):
                self.at.log_error("break statement not in loop or switch statements", ctx)
        # 这里还漏了 continue 语句

    # 检查一个函数里有没有return语句
    def hasReturnStatement(self, ctx:RuleContext):
        rtn = False
        for i in range(ctx.getChildCount()):
            child:RuleContext = ctx.getChild(i)
            if isinstance(child, PlayScriptParser.StatementContext) and child.RETURN():
                rtn = True
                break
            elif not (isinstance(child, PlayScriptParser.FunctionDeclarationContext) or isinstance(child, PlayScriptParser.ClassDeclarationContext)):
                rtn = self.hasReturnStatement(child)
                if rtn:
                    break
        return rtn

    # break 只能出现在循环语句或switch-case语句里
    def checkBreak(self, ctx:RuleContext):
        if isinstance(ctx.parentCtx, PlayScriptParser.StatementContext) and (ctx.parentCtx.FOR() or ctx.parentCtx.WHILE()):
        # or ctx.parentCtx is SwitchBlockStatementGroupContext:
            return True
        elif (ctx.parentCtx is None) or isinstance(ctx.parentCtx, PlayScriptParser.FunctionDeclarationContext):
            return False
        else:
            return self.checkBreak(ctx.parentCtx)

'''
函数闭包变量 分析
'''
class ClosureAnalyzer():
    def __init__(self, at:AnnotatedTree):
        super().__init__()
        self.at = at

    '''
     * 对所有的函数做闭包分析。
     * 只做标准函数的分析，不做类的方法的分析。
    '''
    def analyzeClosures(self):
        for type in self.at.types:
            if isinstance(type, Function) and not type.isMethod():  # 这里意思是：类的方法不支持闭包。面向对象和函数式编程是两种不同的编程范式，没必要兼容，当做互斥
                set = self.calcClosureVariables(type)  # set()
                if len(set) > 0:
                    type.closureVariables = set

    '''
     * 为某个函数计算闭包变量，也就是它所引用的外部环境变量。
     * 算法：计算所有的变量引用，去掉内部声明的变量，剩下的就是外部的。
    '''
    def calcClosureVariables(self, function:Function):  # Set<Variable>
        refered = self.variablesReferedByScope(function)  # Set<Variable>
        declared = self.variablesDeclaredUnderScope(function)  # Set<Variable> 
        rtn = refered.difference(declared)
        # # 观察每个函数的闭包变量是否正确
        # print('-----------------')
        # print(function.toString())
        # print('refered:')
        # for i in refered:
        #     print(i.toString(), end=', ')
        # print()
        # print('declared:')
        # for i in declared:
        #     print(i.toString(), end=', ')
        # print()
        # print('closure:')
        # for i in rtn:
        #     print(i.toString(), end=', ')
        # print()
        # print('-----------------')
        return rtn

    '''
     * 被一个Scope（包括下级Scope）内部的代码所引用的所有变量的集合
     * TODO 这里应该将函数内部定义的 Function/Class 排除掉，需要考虑嵌套闭包的情况
    '''
    def variablesReferedByScope(self, scope):  # Set<Variable>
        rtn = set()
        scopeNode:ParserRuleContext = scope.ctx
        # 扫描所有的符号引用。这对于大的程序性能不够优化，因为符号表太大。
        # 其实只要遍历scope对应的node的子树，找出所有带引用的结点所引用的 variable 即可
        for node in self.at.symbolOfNode:
            # 注意：由于 VariableDeclator 的ctx 也会跟symbol绑定，所以这里会连同 int a=2; 里的a 都算到引用集合里，
            # 虽然并非定义了就一定会引用，但即便没引用而把它当做引用了，也没什么关系。而且后面还会去掉所有在函数里定义的变量
            symbol:Symbol = self.at.symbolOfNode[node]
            if isinstance(symbol, Variable) and self.isAncestor(scopeNode, node):
                rtn.add(symbol)
                # 注意：这里只考虑了Variable的应用，没有考虑Function的引用
                # 函数不存在生存期的问题，所以永远可以找到，不需要记录到闭包环境里
        return rtn

    '''
     * 看看node1是不是node2的祖先
    '''
    def isAncestor(self, node1:RuleContext, node2:RuleContext):
        if node2.parentCtx is None:
            return False
        elif node2.parentCtx == node1:
            return True
        else:
            return self.isAncestor(node1, node2.parentCtx)

    '''
     * 在一个Scope（及）下级Scope中声明的所有变量的集合
    '''
    def variablesDeclaredUnderScope(self, scope:Scope):  # Set<Variable>
        rtn = set()
        for symbol in scope.symbols:
            if isinstance(symbol, Variable):
                rtn.add(symbol)
            elif isinstance(symbol, Scope):  # TODO 这里应该排除掉 Function/Class
                rtn = rtn.union(self.variablesDeclaredUnderScope(symbol))
                # 观察下面代码是否会出现问题：
                # func(int a) {
                #   // 计算inner的闭包
                #   inner() {
                #     println(a);  // 由于下级作用域存在a的定义，按照这里的做法，a不会加入闭包，到时候执行的时候会出错？不会，两个a是不同的Symbol！前面的RefResolve很关键 
                #     for (int a=0; a<3; a++) {
                #     ...
                #     }
                #   }
                #   return inner
                # }
        return rtn


'''
将源码翻译成 Annotated tree
'''
def translate(text):
    at = AnnotatedTree()

    # 词法分析
    input_stream = InputStream(text)
    lexer = PlayScriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    # 语法分析
    parser = PlayScriptParser(token_stream)
    at.ast = parser.prog()

    # 语义分析
    walker = ParseTreeWalker()
    # 多步的语义解析。
    # 优点：1.代码更清晰；2.允许使用在声明之前，这在支持面向对象、递归函数等特征时是必须的
    # pass1：type & Scope
    pass1:TypeAndScopeScanner = TypeAndScopeScanner(at)
    walker.walk(pass1, at.ast)
    # pass2：把变量声明、函数声明、类继承 的类型都解析出来。也就是所有声明时用到类型的地方（I属性）
    pass2:TypeResolver = TypeResolver(at)
    walker.walk(pass2, at.ast)
    # pass3：消解所有符号的引用（变量+函数）。还做了类型的推断（S属性）
    pass3:RefResolver = RefResolver(at)
    walker.walk(pass3, at.ast)
    # pass4：类型检查
    pass4:TypeChecker = TypeChecker(at)
    walker.walk(pass4, at.ast)
    # pass5：其他语义检查
    pass5:SematicValidator = SematicValidator(at)
    walker.walk(pass5, at.ast)
    # pass6：做闭包的分析
    closureAnalyzer:ClosureAnalyzer = ClosureAnalyzer(at)
    closureAnalyzer.analyzeClosures()

    return at


'''
调试功能：可以将 AST、作用域、符号表等信息，以DOT文本输出
'''
class Dumper():
    def __init__(self, at):
        self.at = at
        self.ctxToUid = {}
        self.id = 0
        self.symbol2Uid = {}

    def escape(self, s:str):
        s = list(s)
        for i in range(len(s)):
            if s[i] == '"':
                s[i] = r'\"'
        s = ''.join(s)
        return s

    def get_label(self, ctx)->str:
        if isinstance(ctx, TerminalNode): # hasattr(ctx, 'getSymbol'):
            ret = ctx.getText()
            return self.escape(ret)
        else:
            return PlayScriptParser.ruleNames[ctx.getRuleIndex()]

    def visit(self, ctx, f):
        idx = self.id
        self.id += 1
        self.ctxToUid[ctx] = str(idx)
        if isinstance(ctx, TerminalNode):
            line = self.ctxToUid[ctx] + ' [label="' + self.get_label(ctx) + '" shape=rectangle]'
        else:
            line = self.ctxToUid[ctx] + ' [label="' + self.get_label(ctx) + '"]'
        print(line, file=f)
        if ctx.parentCtx:
            line = self.ctxToUid[ctx.parentCtx] + ' -- ' + self.ctxToUid[ctx]
            print(line, file=f)
        if not isinstance(ctx, TerminalNode): # hasattr(ctx, 'getSymbol'):
            for childCtx in ctx.getChildren():
                self.visit(childCtx, f)
    
    def dump_ast(self, f=None):
        print('--------------------------', file=f)
        print('graph ast {', file=f)
        print('node [shape=plaintext]', file=f)
        self.ctxToUid = {}
        self.id = 0
        self.visit(self.at.ast, f)
        print('}', file=f)
        print('--------------------------', file=f)
    
    def dump_at(self, f=None):
        print('--------------------------')
        print('graph at {', file=f)
        print('node [shape=plaintext]', file=f)
        self.ctxToUid = {}
        self.id = 0
        self.symbol2Uid = {}
        self.visit(self.at.ast, f)

        # 给AST打上类型标注，rewrite那些带类型的结点
        node2Type = self.at.typeOfNode
        for node in node2Type:
            node_uid = self.ctxToUid[node]
            type_str = node2Type[node].toString()
            line = node_uid + ' [label="' + self.get_label(node) + '\\n(' + type_str + ')"]'
            print(line, file=f)

        # 画出每个Symbol结点，以及 定义&引用消解 关系
        # node2Symbol = self.at.symbolOfNode
        # for node in node2Symbol:
        #     symbol = node2Symbol[node]
        #     if not symbol in self.symbol2Uid:
        #         idx = self.id
        #         self.id += 1
        #         self.symbol2Uid[symbol] = str(idx)
        #         symbol_uid = self.symbol2Uid[symbol]
        #         name = symbol.name
        #         type_str = symbol.type.toString()
        #         line = symbol_uid + '[label="' + name +': ' + type_str + '" shape=circle]'
        #         print(line)
        #         line = symbol_uid + ' -- ' + self.ctxToUid[node] + ' [style="dashed" color="#ff0000"]'
        #         print(line)
        #     symbol_uid = self.symbol2Uid[symbol]
        #     if node != symbol.ctx:
        #         line = self.ctxToUid[node] + ' -- ' + symbol_uid + ' [style="dashed" color="#0000ff"]'
        #         print(line)

        print('}', file=f)

        # 打印 type list
        print()
        print('types: [', end='')
        for typ in self.at.types:
            print(typ.toString(), end=', ')
        print(']')
        print()

        # 打印 作用域
        node2Scope = self.at.node2Scope
        for node in node2Scope:
            line = node2Scope[node].name + ': ['
            for symbol in node2Scope[node].symbols:
                line += symbol.name + ', '
            line += ']'
            print(line)

        print('--------------------------')
