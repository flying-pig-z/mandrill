#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from lexer import TokenType, Lexer

# AST节点基类
class ASTNode:
    pass

# 表达式节点
class Expression(ASTNode):
    pass

class BinaryOp(Expression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Literal(Expression):
    def __init__(self, value):
        self.value = value

class Identifier(Expression):
    def __init__(self, name):
        self.name = name

class Keyword(Expression):
    def __init__(self, name):
        self.name = name

# 语句节点
class Statement(ASTNode):
    pass

class Assignment(Statement):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class IfStatement(Statement):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileStatement(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class Block(Statement):
    def __init__(self, statements):
        self.statements = statements

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

# 修改Parser来构建AST
class ASTParser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
    
    def error(self, message="Syntax error"):
        token_info = "EOF" if self.current_token is None else f"{self.current_token.type}:{self.current_token.value}"
        raise Exception(f"{message} at {token_info}")
    
    def eat(self, token_type, token_value=None):
        """消费当前Token，如果类型或值不匹配则报错"""
        if self.current_token is None:
            self.error(f"Expected {token_type}" + (f":{token_value}" if token_value else ""))
            
        if self.current_token.type == token_type:
            if token_value is None or self.current_token.value == token_value:
                self.current_token = self.lexer.get_next_token()
            else:
                self.error(f"Expected {token_type}:{token_value}")
        else:
            self.error(f"Expected {token_type}" + (f":{token_value}" if token_value else ""))
    
    def program(self):
        """解析整个程序"""
        statements = self.statement_list()
        return Program(statements)
    
    def statement_list(self):
        """解析语句列表"""
        statements = []
        
        # 处理空程序
        if self.current_token is None:
            return statements
        
        # 处理语句
        while self.current_token is not None and not (self.current_token.type == TokenType.OP and self.current_token.value == '}'):
            statements.append(self.statement())
        
        return statements
    
    def statement(self):
        """解析单条语句"""
        if self.current_token is None:
            self.error("Unexpected end of input")
            
        if self.current_token.type == TokenType.KEYWORD:
            if self.current_token.value == "if":
                return self.if_statement()
            elif self.current_token.value == "while":
                return self.while_statement()
            elif self.current_token.value in ["write", "put"]:
                return self.assignment_statement()
            else:
                self.error(f"Unexpected keyword: {self.current_token.value}")
        elif self.current_token.type == TokenType.ID:
            return self.assignment_statement()
        else:
            self.error(f"Unexpected token: {self.current_token.type}:{self.current_token.value}")
    
    def if_statement(self):
        """解析if语句"""
        self.eat(TokenType.KEYWORD, "if")
        self.eat(TokenType.OP, "(")
        condition = self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        then_block = Block(self.statement_list())
        self.eat(TokenType.OP, "}")
        
        else_block = None
        # else部分是可选的
        if self.current_token is not None and self.current_token.type == TokenType.KEYWORD and self.current_token.value == "else":
            self.eat(TokenType.KEYWORD, "else")
            self.eat(TokenType.OP, "{")
            else_block = Block(self.statement_list())
            self.eat(TokenType.OP, "}")
        
        return IfStatement(condition, then_block, else_block)
    
    def while_statement(self):
        """解析while语句"""
        self.eat(TokenType.KEYWORD, "while")
        self.eat(TokenType.OP, "(")
        condition = self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        body = Block(self.statement_list())
        self.eat(TokenType.OP, "}")
        
        return WhileStatement(condition, body)
    
    def assignment_statement(self):
        """解析赋值语句"""
        # 左值可以是标识符或特殊关键字(write, put)
        if self.current_token.type == TokenType.ID:
            target = Identifier(self.current_token.value)
            self.eat(TokenType.ID)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["write", "put"]:
            target = Keyword(self.current_token.value)
            self.eat(TokenType.KEYWORD)
        else:
            self.error("Expected identifier or output variable")
            
        self.eat(TokenType.OP, "=")
        value = self.expression()
        self.eat(TokenType.OP, ";")
        
        return Assignment(target, value)
    
    def expression(self):
        """解析表达式"""
        return self.equality()
    
    def equality(self):
        """解析相等性表达式"""
        node = self.comparison()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["==", "!="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.comparison()
            node = BinaryOp(node, op, right)
        
        return node
    
    def comparison(self):
        """解析比较表达式"""
        node = self.term()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in [">", "<", ">=", "<="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.term()
            node = BinaryOp(node, op, right)
        
        return node
    
    def term(self):
        """解析加减表达式"""
        node = self.factor()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["+", "-"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.factor()
            node = BinaryOp(node, op, right)
        
        return node
    
    def factor(self):
        """解析乘除模表达式"""
        node = self.primary()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["*", "/", "%"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.primary()
            node = BinaryOp(node, op, right)
        
        return node
    
    def primary(self):
        """解析基本表达式"""
        if self.current_token.type == TokenType.LITERAL:
            value = self.current_token.value
            self.eat(TokenType.LITERAL)
            # 将十六进制字符串转换为整数
            if value.startswith('0x'):
                return Literal(int(value, 16))
            else:
                return Literal(int(value))
        elif self.current_token.type == TokenType.ID:
            name = self.current_token.value
            self.eat(TokenType.ID)
            return Identifier(name)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["read", "write", "put", "get"]:
            name = self.current_token.value
            self.eat(TokenType.KEYWORD)
            return Keyword(name)
        elif self.current_token.type == TokenType.OP and self.current_token.value == "(":
            self.eat(TokenType.OP, "(")
            node = self.expression()
            self.eat(TokenType.OP, ")")
            return node
        else:
            self.error("Invalid primary expression")
    
    def parse(self):
        """执行语法分析"""
        try:
            ast = self.program()
            # 确保所有token都已处理
            if self.current_token is not None:
                self.error("Unexpected token at end of input")
            return ast
        except Exception as e:
            raise e

# 解释器
class Interpreter:
    def __init__(self, input_file='mandrill.in'):
        self.variables = {}  # 全局变量字典
        self.input_data = ""
        self.input_index = 0
        
        # 读取输入文件
        try:
            with open(input_file, 'r') as f:
                self.input_data = f.read()
        except FileNotFoundError:
            self.input_data = ""
        
        # 缓存访问方法以提高性能
        self.visitors = {
            'Program': self.visit_Program,
            'Block': self.visit_Block,
            'Assignment': self.visit_Assignment,
            'IfStatement': self.visit_IfStatement,
            'WhileStatement': self.visit_WhileStatement,
            'BinaryOp': self.visit_BinaryOp,
            'Literal': self.visit_Literal,
            'Identifier': self.visit_Identifier,
            'Keyword': self.visit_Keyword,
        }
        
    def interpret(self, ast):
        """解释执行AST"""
        self.visit(ast)
    
    def visit(self, node):
        """访问AST节点"""
        node_type = type(node).__name__
        visitor = self.visitors.get(node_type, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """通用访问方法"""
        raise Exception(f'No visit_{type(node).__name__} method')
    
    def visit_Program(self, node):
        """访问程序节点"""
        for statement in node.statements:
            self.visit(statement)
    
    def visit_Block(self, node):
        """访问块节点"""
        for statement in node.statements:
            self.visit(statement)
    
    def visit_Assignment(self, node):
        """访问赋值语句"""
        value = self.visit(node.value)
        
        if isinstance(node.target, Identifier):
            # 普通变量赋值
            self.variables[node.target.name] = value
        elif isinstance(node.target, Keyword):
            # 特殊关键字赋值
            if node.target.name == "write":
                print(value, end='')  # write不添加换行符
            elif node.target.name == "put":
                if 0 <= value <= 127:  # 有效ASCII字符
                    print(chr(value), end='')
    
    def visit_IfStatement(self, node):
        """访问if语句"""
        condition = self.visit(node.condition)
        if condition != 0:  # 非零为真
            self.visit(node.then_block)
        elif node.else_block:
            self.visit(node.else_block)
    
    def visit_WhileStatement(self, node):
        """访问while语句"""
        while True:
            condition = self.visit(node.condition)
            if condition == 0:  # 零为假
                break
            self.visit(node.body)
    
    def visit_BinaryOp(self, node):
        """访问二元操作"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if node.op == '+':
            return left + right
        elif node.op == '-':
            return left - right
        elif node.op == '*':
            return left * right
        elif node.op == '/':
            return left // right if right != 0 else 0
        elif node.op == '%':
            return left % right if right != 0 else 0
        elif node.op == '>':
            return 1 if left > right else 0
        elif node.op == '<':
            return 1 if left < right else 0
        elif node.op == '>=':
            return 1 if left >= right else 0
        elif node.op == '<=':
            return 1 if left <= right else 0
        elif node.op == '==':
            return 1 if left == right else 0
        elif node.op == '!=':
            return 1 if left != right else 0
        else:
            raise Exception(f'Unknown binary operator: {node.op}')
    
    def visit_Literal(self, node):
        """访问字面量"""
        return node.value
    
    def visit_Identifier(self, node):
        """访问标识符"""
        return self.variables.get(node.name, 0)  # 未定义变量默认为0
    
    def visit_Keyword(self, node):
        """访问关键字"""
        if node.name == "read":
            return self.read_integer()
        elif node.name == "get":
            return self.read_character()
        elif node.name in ["write", "put"]:
            # 这些在赋值语句中处理
            return 0
        else:
            raise Exception(f'Unknown keyword: {node.name}')
    
    def read_integer(self):
        """读取整数，类似scanf("%d", &n)的行为"""
        # 跳过空白字符
        while self.input_index < len(self.input_data) and self.input_data[self.input_index].isspace():
            self.input_index += 1
        
        if self.input_index >= len(self.input_data):
            return 0
        
        # 读取数字（包括负号）
        num_str = ""
        start_index = self.input_index
        
        # 处理负号
        if self.input_index < len(self.input_data) and self.input_data[self.input_index] == '-':
            num_str += self.input_data[self.input_index]
            self.input_index += 1
        
        # 读取数字
        while (self.input_index < len(self.input_data) and 
               self.input_data[self.input_index].isdigit()):
            num_str += self.input_data[self.input_index]
            self.input_index += 1
        
        # 如果没有读取到有效数字，返回0
        if not num_str or num_str == '-':
            self.input_index = start_index
            return 0
        
        try:
            return int(num_str)
        except ValueError:
            return 0
    
    def read_character(self):
        """读取字符，类似getchar()的行为"""
        if self.input_index < len(self.input_data):
            char = self.input_data[self.input_index]
            self.input_index += 1
            return ord(char)
        return 0

def main():
    # 从标准输入读取源代码
    source = sys.stdin.read()
    
    try:
        # 创建词法分析器和AST解析器
        lexer = Lexer(source)
        parser = ASTParser(lexer)
        
        # 解析生成AST
        ast = parser.parse()
        
        # 创建解释器并执行
        interpreter = Interpreter()
        interpreter.interpret(ast)
        
    except Exception as e:
        # 静默处理错误，按照要求不输出错误信息
        pass

if __name__ == "__main__":
    main()