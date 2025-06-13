#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct
from lexer import TokenType, Lexer

# AST节点定义
class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class StatementList(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class AssignmentStatement(ASTNode):
    def __init__(self, lvalue, expression):
        self.lvalue = lvalue
        self.expression = expression

class IfStatement(ASTNode):
    def __init__(self, condition, then_statements, else_statements=None):
        self.condition = condition
        self.then_statements = then_statements
        self.else_statements = else_statements

class WhileStatement(ASTNode):
    def __init__(self, condition, body_statements):
        self.condition = condition
        self.body_statements = body_statements

class BinaryOp(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value

class SpecialVar(ASTNode):
    def __init__(self, name):
        self.name = name

# 修改的Parser类，生成AST
class ASTParser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
    
    def error(self, message="Syntax error"):
        token_info = "EOF" if self.current_token is None else "{}:{}".format(self.current_token.type, self.current_token.value)
        raise Exception("{} at {}".format(message, token_info))
    
    def eat(self, token_type, token_value=None):
        """消费当前Token，如果类型或值不匹配则报错"""
        if self.current_token is None:
            self.error("Expected {}{}".format(token_type, ":{}".format(token_value) if token_value else ""))
            
        if self.current_token.type == token_type:
            if token_value is None or self.current_token.value == token_value:
                token = self.current_token
                self.current_token = self.lexer.get_next_token()
                return token
            else:
                self.error("Expected {}:{}".format(token_type, token_value))
        else:
            self.error("Expected {}{}".format(token_type, ":{}".format(token_value) if token_value else ""))
    
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
        
        # 处理至少一条语句
        if self.current_token.type != TokenType.OP or self.current_token.value != '}':
            statements.append(self.statement())
        
        # 处理多条语句
        while self.current_token is not None and self.current_token.type != TokenType.OP and self.current_token.value != '}':
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
                self.error("Unexpected keyword: {}".format(self.current_token.value))
        elif self.current_token.type == TokenType.ID:
            return self.assignment_statement()
        else:
            self.error("Unexpected token: {}:{}".format(self.current_token.type, self.current_token.value))
    
    def if_statement(self):
        """解析if语句"""
        self.eat(TokenType.KEYWORD, "if")
        self.eat(TokenType.OP, "(")
        condition = self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        then_statements = self.statement_list()
        self.eat(TokenType.OP, "}")
        
        else_statements = None
        # else部分是可选的
        if self.current_token is not None and self.current_token.type == TokenType.KEYWORD and self.current_token.value == "else":
            self.eat(TokenType.KEYWORD, "else")
            self.eat(TokenType.OP, "{")
            else_statements = self.statement_list()
            self.eat(TokenType.OP, "}")
        
        return IfStatement(condition, then_statements, else_statements)
    
    def while_statement(self):
        """解析while语句"""
        self.eat(TokenType.KEYWORD, "while")
        self.eat(TokenType.OP, "(")
        condition = self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        body_statements = self.statement_list()
        self.eat(TokenType.OP, "}")
        
        return WhileStatement(condition, body_statements)
    
    def assignment_statement(self):
        """解析赋值语句"""
        # 左值可以是标识符或特殊关键字(write, put)
        if self.current_token.type == TokenType.ID:
            lvalue = Identifier(self.current_token.value)
            self.eat(TokenType.ID)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["write", "put"]:
            lvalue = SpecialVar(self.current_token.value)
            self.eat(TokenType.KEYWORD)
        else:
            self.error("Expected identifier or output variable")
            
        self.eat(TokenType.OP, "=")
        expression = self.expression()
        self.eat(TokenType.OP, ";")
        
        return AssignmentStatement(lvalue, expression)
    
    def expression(self):
        """解析表达式"""
        return self.equality()
    
    def equality(self):
        """解析相等性表达式"""
        left = self.comparison()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["==", "!="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.comparison()
            left = BinaryOp(left, op, right)
        
        return left
    
    def comparison(self):
        """解析比较表达式"""
        left = self.term()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in [">", "<", ">=", "<="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.term()
            left = BinaryOp(left, op, right)
        
        return left
    
    def term(self):
        """解析加减表达式"""
        left = self.factor()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["+", "-"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.factor()
            left = BinaryOp(left, op, right)
        
        return left
    
    def factor(self):
        """解析乘除模表达式"""
        left = self.primary()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["*", "/", "%"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            right = self.primary()
            left = BinaryOp(left, op, right)
        
        return left
    
    def primary(self):
        """解析基本表达式"""
        if self.current_token.type == TokenType.LITERAL:
            value = self.current_token.value
            self.eat(TokenType.LITERAL)
            return Literal(value)
        elif self.current_token.type == TokenType.ID:
            name = self.current_token.value
            self.eat(TokenType.ID)
            return Identifier(name)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["read", "write", "put", "get"]:
            name = self.current_token.value
            self.eat(TokenType.KEYWORD)
            return SpecialVar(name)
        elif self.current_token.type == TokenType.OP and self.current_token.value == "(":
            self.eat(TokenType.OP, "(")
            expr = self.expression()
            self.eat(TokenType.OP, ")")
            return expr
        else:
            self.error("Invalid primary expression")
    
    def parse(self):
        """执行语法分析并返回AST"""
        try:
            ast = self.program()
            # 确保所有token都已处理
            if self.current_token is not None:
                self.error("Unexpected token at end of input")
            return ast
        except Exception as e:
            raise e

# 代码生成器
class CodeGenerator:
    def __init__(self):
        self.instructions = []  # 指令列表
        self.var_table = {}     # 变量符号表
        self.var_count = 0      # 变量计数器
        self.label_count = 0    # 标签计数器
    
    # 指令操作码
    NOP = 0x00000000
    DSTORE = 0x00000001
    DLOAD = 0x00000002
    DWRITE = 0x00000003
    EVAL = 0x00000005
    JUMP = 0x00000006
    GETI = 0x00000007
    GETC = 0x00000008
    PUTI = 0x00000009
    PUTC = 0x0000000A
    
    # eval指令操作数
    OP_ADD = 0x00010001
    OP_SUB = 0x00010002
    OP_MUL = 0x00010003
    OP_DIV = 0x00010004
    OP_MOD = 0x00010005
    OP_GT = 0x00010006
    OP_LT = 0x00010007
    OP_GE = 0x00010008
    OP_LE = 0x00010009
    OP_EQ = 0x0001000A
    OP_NE = 0x0001000B
    OP_COND_JUMP = 0x0001000C
    
    def get_var_id(self, name):
        """获取变量ID，如果不存在则创建"""
        if name not in self.var_table:
            self.var_table[name] = self.var_count
            self.var_count += 1
        return self.var_table[name]
    
    def emit(self, opcode, operand=0):
        """发射一条指令"""
        self.instructions.append((opcode, operand))
    
    def get_label(self):
        """获取新标签"""
        label = f"L{self.label_count}"
        self.label_count += 1
        return label
    
    def patch_jump(self, instruction_index, target_address):
        """修补跳转地址"""
        opcode, _ = self.instructions[instruction_index]
        self.instructions[instruction_index] = (opcode, target_address)
    
    def generate(self, ast):
        """生成代码"""
        self.visit(ast)
        # 添加程序结束指令
        self.emit(self.JUMP, 0xFFFFFFFF)
        return self.instructions
    
    def visit(self, node):
        """访问AST节点"""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        """通用访问方法"""
        raise Exception("No visit method for {}".format(type(node).__name__))
    
    def visit_Program(self, node):
        """访问程序节点"""
        for stmt in node.statements:
            self.visit(stmt)
    
    def visit_AssignmentStatement(self, node):
        """访问赋值语句"""
        # 计算右值表达式
        self.visit(node.expression)
        
        # 处理左值
        if isinstance(node.lvalue, Identifier):
            # 普通变量赋值
            var_id = self.get_var_id(node.lvalue.name)
            self.emit(self.DWRITE, var_id)
        elif isinstance(node.lvalue, SpecialVar):
            # 特殊变量赋值
            if node.lvalue.name == "write":
                self.emit(self.PUTI, 0)
            elif node.lvalue.name == "put":
                self.emit(self.PUTC, 0)
    
    def visit_IfStatement(self, node):
        """访问if语句"""
        # 生成条件表达式代码（结果在栈顶）
        self.visit(node.condition)
        
        if node.else_statements:
            # 有else分支的情况
            # 压入then和else分支地址
            then_addr_pos = len(self.instructions)
            self.emit(self.DSTORE, 0)  # then分支地址，稍后修补
            else_addr_pos = len(self.instructions) 
            self.emit(self.DSTORE, 0)  # else分支地址，稍后修补
            self.emit(self.EVAL, self.OP_COND_JUMP)
            
            # then分支代码
            then_start = len(self.instructions)
            for stmt in node.then_statements:
                self.visit(stmt)
            
            # 跳转到if语句结束
            jump_to_end = len(self.instructions)
            self.emit(self.JUMP, 0)  # 稍后修补
            
            # else分支代码
            else_start = len(self.instructions)
            for stmt in node.else_statements:
                self.visit(stmt)
            
            # 修补跳转地址
            end_addr = len(self.instructions) * 8
            self.patch_jump(jump_to_end, end_addr)
            self.patch_jump(then_addr_pos, then_start * 8)   # then分支地址
            self.patch_jump(else_addr_pos, else_start * 8)   # else分支地址
        else:
            # 没有else分支的情况
            then_addr_pos = len(self.instructions)
            self.emit(self.DSTORE, 0)  # then分支地址，稍后修补
            else_addr_pos = len(self.instructions)
            self.emit(self.DSTORE, 0)  # else分支地址（跳到结束），稍后修补
            self.emit(self.EVAL, self.OP_COND_JUMP)
            
            # then分支代码
            then_start = len(self.instructions)
            for stmt in node.then_statements:
                self.visit(stmt)
            
            # 修补跳转地址
            end_addr = len(self.instructions) * 8
            self.patch_jump(then_addr_pos, then_start * 8)  # then分支地址
            self.patch_jump(else_addr_pos, end_addr)        # else分支地址（跳到结束）
    
    def visit_WhileStatement(self, node):
        """访问while语句"""
        # 循环开始位置
        loop_start = len(self.instructions)
        
        # 生成条件表达式代码（结果在栈顶）
        self.visit(node.condition)
        
        # 压入then和else分支地址
        then_addr_pos = len(self.instructions)
        self.emit(self.DSTORE, 0)  # body分支地址，稍后修补
        else_addr_pos = len(self.instructions)
        self.emit(self.DSTORE, 0)  # end分支地址，稍后修补
        self.emit(self.EVAL, self.OP_COND_JUMP)
        
        # 循环体代码
        body_start = len(self.instructions)
        for stmt in node.body_statements:
            self.visit(stmt)
        
        # 跳回循环开始
        self.emit(self.JUMP, loop_start * 8)
        
        # 修补跳转地址
        end_addr = len(self.instructions) * 8
        self.patch_jump(then_addr_pos, body_start * 8)  # body分支地址
        self.patch_jump(else_addr_pos, end_addr)        # end分支地址
    
    def visit_BinaryOp(self, node):
        """访问二元运算"""
        # 计算左操作数
        self.visit(node.left)
        # 计算右操作数
        self.visit(node.right)
        
        # 生成对应的运算指令
        op_map = {
            "+": self.OP_ADD,
            "-": self.OP_SUB,
            "*": self.OP_MUL,
            "/": self.OP_DIV,
            "%": self.OP_MOD,
            ">": self.OP_GT,
            "<": self.OP_LT,
            ">=": self.OP_GE,
            "<=": self.OP_LE,
            "==": self.OP_EQ,
            "!=": self.OP_NE
        }
        
        if node.operator in op_map:
            self.emit(self.EVAL, op_map[node.operator])
        else:
            raise Exception("Unknown operator: {}".format(node.operator))
    
    def visit_Identifier(self, node):
        """访问标识符"""
        var_id = self.get_var_id(node.name)
        self.emit(self.DLOAD, var_id)
    
    def visit_Literal(self, node):
        """访问字面量"""
        # 将十六进制字符串转换为整数
        value = int(node.value, 16)
        self.emit(self.DSTORE, value)
    
    def visit_SpecialVar(self, node):
        """访问特殊变量"""
        if node.name == "read":
            self.emit(self.GETI, 0)
        elif node.name == "get":
            self.emit(self.GETC, 0)
        elif node.name == "write" or node.name == "put":
            # 这种情况不应该在表达式中出现
            raise Exception("Unexpected special variable in expression: {}".format(node.name))

# 字节码输出器
class BytecodeWriter:
    def __init__(self):
        pass
    
    def write_bytecode(self, instructions, var_count):
        """生成字节码文件内容"""
        # 计算大小
        data_size = var_count * 4  # 每个变量4字节
        code_size = len(instructions) * 8  # 每条指令8字节
        
        # 构建文件头
        header = bytearray()
        # 魔数：MANDRILLBYTECODE (16字节)
        magic = b"MANDRILLBYTECODE"
        header.extend(magic)
        
        # 版本号 (4字节大端序)
        version = struct.pack(">I", 1)
        header.extend(version)
        
        # 数据区大小 (4字节大端序)
        data_size_bytes = struct.pack(">I", data_size)
        header.extend(data_size_bytes)
        
        # 代码区大小 (4字节大端序)
        code_size_bytes = struct.pack(">I", code_size)
        header.extend(code_size_bytes)
        
        # 填充 (4字节)
        padding = b"\x00\x00\x00\x00"
        header.extend(padding)
        
        # 构建指令序列
        code = bytearray()
        for opcode, operand in instructions:
            # 每条指令8字节，前4字节操作码，后4字节操作数，都是大端序
            instruction = struct.pack(">II", opcode, operand)
            code.extend(instruction)
        
        return bytes(header + code)

def main():
    # 从标准输入读取源代码
    source = sys.stdin.read()
    
    try:
        # 词法分析
        lexer = Lexer(source)
        
        # 语法分析，生成AST
        parser = ASTParser(lexer)
        ast = parser.parse()
        
        # 代码生成
        generator = CodeGenerator()
        instructions = generator.generate(ast)
        
        # 生成字节码
        writer = BytecodeWriter()
        bytecode = writer.write_bytecode(instructions, generator.var_count)
        
        # 输出字节码到标准输出
        sys.stdout.buffer.write(bytecode)
        
    except Exception as e:
        print("Compilation error: {}".format(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()