#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

# 定义Token类型
class TokenType:
    KEYWORD = "keyword"  # 关键字
    ID = "id"            # 标识符
    LITERAL = "literal"  # 常量
    OP = "op"            # 运算符

# Token类，表示词法单元
class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value

    def __str__(self):
        return f"[{self.type}:{self.value}]"

# 定义Mandrill语言的关键字
KEYWORDS = {
    "if", "else", "while", "read", "put", "write", "get"
}

# 定义合法的单字符运算符
SINGLE_CHAR_OPS = {
    "+", "-", "*", "/", "%", ">", "<", "=", ";", "(", ")", "{", "}"
}

# 定义双字符运算符
DOUBLE_CHAR_OPS = {
    ">=", "<=", "==", "!="
}

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source[0] if source else None

    def error(self, message=None):
        """报告词法错误"""
        if message is None:
            message = f"Invalid character: {self.current_char}"
        raise Exception(f"Lexical error at line {self.line}, column {self.column}: {message}")

    def advance(self):
        """读取下一个字符"""
        self.pos += 1
        if self.pos >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.pos]
            if self.current_char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1

    def peek(self):
        """查看下一个字符但不移动指针"""
        peek_pos = self.pos + 1
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def identifier(self):
        """处理标识符和关键字"""
        result = ""
        while self.current_char is not None and self.current_char.isalpha() and self.current_char.islower():
            result += self.current_char
            self.advance()

        # 检查是否是关键字
        if result in KEYWORDS:
            return Token(TokenType.KEYWORD, result)
        else:
            return Token(TokenType.ID, result)

    def number(self):
        """处理整数常量"""
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        # 转换为十六进制表示
        value = int(result)
        hex_value = f"0x{value:x}"
        return Token(TokenType.LITERAL, hex_value)

    def character(self):
        """处理字符常量"""
        self.advance()  # 跳过开始的单引号
        
        # 处理转义字符
        if self.current_char == '\\':
            self.advance()
            if self.current_char == 'n':
                char_value = ord('\n')
            elif self.current_char == '\\':
                char_value = ord('\\')
            elif self.current_char == '\'':
                char_value = ord('\'')
            else:
                self.error(f"Unsupported escape sequence \\{self.current_char}")
        else:
            # 普通字符
            char_value = ord(self.current_char)
        
        self.advance()  # 移动到字符后
        
        # 检查终止的单引号
        if self.current_char != '\'':
            self.error("Unterminated character literal")
        
        self.advance()  # 跳过结束的单引号
        
        # 返回十六进制表示的ASCII码
        hex_value = f"0x{char_value:x}"
        return Token(TokenType.LITERAL, hex_value)

    def get_next_token(self):
        """获取下一个Token（与parser兼容的接口）"""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            if self.current_char.isalpha() and self.current_char.islower():
                return self.identifier()
                
            if self.current_char.isdigit():
                return self.number()
                
            if self.current_char == '\'':
                return self.character()
                
            # 检查双字符运算符
            if self.current_char in ['>', '<', '=', '!'] and self.peek() == '=':
                op = self.current_char + self.peek()
                self.advance()
                self.advance()
                return Token(TokenType.OP, op)
            
            # 检查单字符运算符
            elif self.current_char in SINGLE_CHAR_OPS:
                op = self.current_char
                self.advance()
                return Token(TokenType.OP, op)
            
            self.error(f"Invalid character: {self.current_char}")
            
        # 没有更多的token了
        return None

    def tokenize(self):
        """将源代码转换为词元序列（用于直接输出）"""
        tokens = []
        while True:
            token = self.get_next_token()
            if token is None:
                break
            tokens.append((token.type, token.value))
        return tokens

def main():
    # 从标准输入读取源代码
    source_code = sys.stdin.read()
    
    # 初始化词法分析器
    lexer = Lexer(source_code)
    
    # 进行词法分析
    tokens = lexer.tokenize()
    
    # 按要求的格式输出词元（每行后面加一个空格）
    for token_type, value in tokens:
        print(f"[{token_type}:{value}] ")

if __name__ == "__main__":
    main()