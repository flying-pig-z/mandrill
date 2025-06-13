#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from lexer import TokenType, Lexer

# 语法分析器
class Parser:
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
        self.statement_list()
    
    def statement_list(self):
        """解析语句列表"""
        # 处理空程序
        if self.current_token is None:
            return
        
        # 处理至少一条语句
        self.statement()
        
        # 处理多条语句
        while self.current_token is not None and self.current_token.type != TokenType.OP and self.current_token.value != '}':
            self.statement()
    
    def statement(self):
        """解析单条语句"""
        if self.current_token is None:
            self.error("Unexpected end of input")
            
        if self.current_token.type == TokenType.KEYWORD:
            if self.current_token.value == "if":
                self.if_statement()
            elif self.current_token.value == "while":
                self.while_statement()
            elif self.current_token.value in ["write", "put"]:
                self.assignment_statement()
            else:
                self.error(f"Unexpected keyword: {self.current_token.value}")
        elif self.current_token.type == TokenType.ID:
            self.assignment_statement()
        else:
            self.error(f"Unexpected token: {self.current_token.type}:{self.current_token.value}")
    
    def if_statement(self):
        """解析if语句"""
        self.eat(TokenType.KEYWORD, "if")
        self.eat(TokenType.OP, "(")
        self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        self.statement_list()
        self.eat(TokenType.OP, "}")
        
        # else部分是可选的
        if self.current_token is not None and self.current_token.type == TokenType.KEYWORD and self.current_token.value == "else":
            self.eat(TokenType.KEYWORD, "else")
            self.eat(TokenType.OP, "{")
            self.statement_list()
            self.eat(TokenType.OP, "}")
    
    def while_statement(self):
        """解析while语句"""
        self.eat(TokenType.KEYWORD, "while")
        self.eat(TokenType.OP, "(")
        self.expression()
        self.eat(TokenType.OP, ")")
        self.eat(TokenType.OP, "{")
        self.statement_list()
        self.eat(TokenType.OP, "}")
    
    def assignment_statement(self):
        """解析赋值语句"""
        # 左值可以是标识符或特殊关键字(write, put)
        if self.current_token.type == TokenType.ID:
            self.eat(TokenType.ID)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["write", "put"]:
            self.eat(TokenType.KEYWORD)
        else:
            self.error("Expected identifier or output variable")
            
        self.eat(TokenType.OP, "=")
        self.expression()
        self.eat(TokenType.OP, ";")
    
    def expression(self):
        """解析表达式"""
        self.equality()
    
    def equality(self):
        """解析相等性表达式"""
        self.comparison()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["==", "!="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            self.comparison()
    
    def comparison(self):
        """解析比较表达式"""
        self.term()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in [">", "<", ">=", "<="]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            self.term()
    
    def term(self):
        """解析加减表达式"""
        self.factor()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["+", "-"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            self.factor()
    
    def factor(self):
        """解析乘除模表达式"""
        self.primary()
        
        while (self.current_token is not None and 
               self.current_token.type == TokenType.OP and 
               self.current_token.value in ["*", "/", "%"]):
            op = self.current_token.value
            self.eat(TokenType.OP, op)
            self.primary()
    
    def primary(self):
        """解析基本表达式"""
        if self.current_token.type == TokenType.LITERAL:
            self.eat(TokenType.LITERAL)
        elif self.current_token.type == TokenType.ID:
            self.eat(TokenType.ID)
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value in ["read", "write", "put", "get"]:
            self.eat(TokenType.KEYWORD)
        elif self.current_token.type == TokenType.OP and self.current_token.value == "(":
            self.eat(TokenType.OP, "(")
            self.expression()
            self.eat(TokenType.OP, ")")
        else:
            self.error("Invalid primary expression")
    
    def parse(self):
        """执行语法分析"""
        try:
            self.program()
            # 确保所有token都已处理
            if self.current_token is not None:
                self.error("Unexpected token at end of input")
            return True
        except Exception as e:
            # print(f"Parsing error: {e}")
            return False

def main():
    # 从标准输入读取源代码
    source = sys.stdin.read()
    
    # 创建词法分析器和语法分析器
    lexer = Lexer(source)
    parser = Parser(lexer)
    
    # 尝试分析源代码
    if parser.parse():
        print("PASS")
    else:
        print("ERROR")

if __name__ == "__main__":
    main()
