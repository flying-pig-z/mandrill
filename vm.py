#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct

class MandrillVM:
    def __init__(self):
        self.stack = []         # 操作数栈
        self.variables = []     # 变量存储区
        self.code = []          # 代码存储区
        self.pc = 0             # 程序计数器
        self.input_tokens = []  # 输入token缓存
        self.input_pos = 0      # 输入位置
        self.input_chars = ""   # 原始字符输入
        self.char_pos = 0       # 字符位置
        
        # 指令操作码 - 作为类常量以避免属性查找
        self.NOP = 0x00000000
        self.DSTORE = 0x00000001
        self.DLOAD = 0x00000002
        self.DWRITE = 0x00000003
        self.EVAL = 0x00000005
        self.JUMP = 0x00000006
        self.GETI = 0x00000007
        self.GETC = 0x00000008
        self.PUTI = 0x00000009
        self.PUTC = 0x0000000A
        
        # eval指令操作数
        self.OP_ADD = 0x00010001
        self.OP_SUB = 0x00010002
        self.OP_MUL = 0x00010003
        self.OP_DIV = 0x00010004
        self.OP_MOD = 0x00010005
        self.OP_GT = 0x00010006
        self.OP_LT = 0x00010007
        self.OP_GE = 0x00010008
        self.OP_LE = 0x00010009
        self.OP_EQ = 0x0001000A
        self.OP_NE = 0x0001000B
        self.OP_COND_JUMP = 0x0001000C
        
        # 预计算的常量
        self.INT32_MIN = -2147483648
        self.INT32_MAX = 2147483647
        self.UINT32_MAX = 4294967296
        
        # 预读输入
        self._preload_input()
    
    def _preload_input(self):
        """预读所有输入并分割为tokens"""
        try:
            # 读取所有输入
            all_input = sys.stdin.read()
            # 为整数输入按空白字符分割
            self.input_tokens = all_input.split()
            # 为字符输入保存原始字符串
            self.input_chars = all_input
            self.char_pos = 0
        except:
            self.input_tokens = []
            self.input_chars = ""
            self.char_pos = 0
    
    def _get_next_int(self):
        """获取下一个整数"""
        while self.input_pos < len(self.input_tokens):
            token = self.input_tokens[self.input_pos]
            self.input_pos += 1
            try:
                return int(token)
            except ValueError:
                continue  # 跳过非数字token
        return 0  # 没有更多输入时返回0
    
    def _get_next_char(self):
        """获取下一个字符"""
        if self.char_pos < len(self.input_chars):
            char = self.input_chars[self.char_pos]
            self.char_pos += 1
            return ord(char)
        return 0
    
    def _to_32bit_int(self, value):
        """将值转换为32位有符号整数（模拟整数溢出）"""
        # 使用预计算的常量，避免重复计算
        if self.INT32_MIN <= value <= self.INT32_MAX:
            return value
        # 简化的模运算
        return ((value + self.INT32_MAX + 1) % self.UINT32_MAX) + self.INT32_MIN
    
    def load_bytecode(self, filename):
        """加载字节码文件"""
        with open(filename, 'rb') as f:
            # 读取文件头
            magic = f.read(16)
            if magic != b"MANDRILLBYTECODE":
                raise Exception("Invalid bytecode file: wrong magic number")
            
            version = struct.unpack(">I", f.read(4))[0]
            if version != 1:
                raise Exception("Unsupported bytecode version: {}".format(version))
            
            data_size = struct.unpack(">I", f.read(4))[0]
            code_size = struct.unpack(">I", f.read(4))[0]
            padding = f.read(4)  # 跳过填充
            
            # 初始化变量存储区
            var_count = data_size // 4
            self.variables = [0] * var_count
            
            # 预分配栈空间以减少重新分配
            # 根据代码大小估算所需栈空间
            estimated_stack_size = min(1000, code_size // 32)  # 保守估计
            self.stack = [0] * estimated_stack_size
            self.stack.clear()  # 清空但保留容量
            
            # 读取代码区
            code_bytes = f.read(code_size)
            instruction_count = code_size // 8
            self.code = [None] * instruction_count  # 预分配代码数组
            
            for i in range(instruction_count):
                offset = i * 8
                opcode, operand = struct.unpack(">II", code_bytes[offset:offset+8])
                self.code[i] = (opcode, operand)
    
    def run(self):
        """执行虚拟机 - 进一步优化版本"""
        self.pc = 0
        stack = self.stack  # 本地引用以减少属性查找
        variables = self.variables
        code = self.code
        
        # 预先创建指令处理函数映射，避免大量if-elif
        def handle_nop(operand): pass
        
        def handle_dstore(operand): 
            stack.append(operand)
        
        def handle_dload(operand): 
            stack.append(variables[operand])
        
        def handle_dwrite(operand):
            value = stack[-1]
            del stack[-1]
            variables[operand] = self._to_32bit_int(value)
        
        def handle_eval(operand):
            self.execute_eval_optimized(operand, stack)
        
        def handle_jump(operand):
            if operand == 0xFFFFFFFF:
                return True  # 程序结束标志
            self.pc = operand // 8 - 1  # -1因为主循环会+1
            return False
        
        def handle_geti(operand):
            stack.append(self._get_next_int())
        
        def handle_getc(operand):
            stack.append(self._get_next_char())
        
        def handle_puti(operand):
            value = stack[-1]
            del stack[-1]
            print(self._to_32bit_int(value), end='')
        
        def handle_putc(operand):
            value = stack[-1]
            del stack[-1]
            value = self._to_32bit_int(value)
            if 0 <= value <= 127:
                print(chr(value), end='')
        
        # 指令分发表
        instruction_handlers = {
            self.NOP: handle_nop,
            self.DSTORE: handle_dstore,
            self.DLOAD: handle_dload,
            self.DWRITE: handle_dwrite,
            self.EVAL: handle_eval,
            self.JUMP: handle_jump,
            self.GETI: handle_geti,
            self.GETC: handle_getc,
            self.PUTI: handle_puti,
            self.PUTC: handle_putc,
        }
        
        # 主执行循环
        while self.pc < len(code):
            opcode, operand = code[self.pc]
            
            handler = instruction_handlers.get(opcode)
            if handler:
                if opcode == self.JUMP:
                    if handler(operand):  # 程序结束
                        break
                else:
                    handler(operand)
            else:
                raise Exception("Unknown opcode: {}".format(opcode))
            
            self.pc += 1
    
    def execute_eval_optimized(self, operand, stack):
        """进一步优化的eval指令执行"""
        if operand == self.OP_COND_JUMP:
            # 条件跳转：使用索引访问而不是pop()
            else_addr = stack[-1]
            then_addr = stack[-2]
            condition = stack[-3]
            del stack[-3:]  # 一次性删除3个元素
            
            if condition != 0:
                self.pc = then_addr // 8
            else:
                self.pc = else_addr // 8
            self.pc -= 1  # 因为主循环会+1
            return
        
        # 二元运算：使用索引访问
        right = stack[-1]
        left = stack[-2]
        del stack[-2:]  # 一次性删除2个元素
        
        # 使用优化的分支结构减少比较次数
        if operand == self.OP_MUL:
            # 针对布尔乘法的特殊优化
            if left == 0 or right == 0:
                result = 0
            elif left == 1:
                result = right
            elif right == 1:
                result = left
            else:
                result = left * right
        elif operand == self.OP_ADD:
            result = left + right
        elif operand == self.OP_SUB:
            result = self._to_32bit_int(left - right)
        elif operand == self.OP_DIV:
            if right == 0:
                raise Exception("Division by zero")
            result = self._to_32bit_int(left // right)
        elif operand == self.OP_MOD:
            if right == 0:
                raise Exception("Division by zero")
            mod_result = left % right
            if right > 0 and mod_result < 0:
                mod_result += right
            result = self._to_32bit_int(mod_result)
        # 使用连续的比较操作减少分支预测失败
        elif operand == self.OP_EQ:
            result = 1 if left == right else 0
        elif operand == self.OP_NE:
            result = 1 if left != right else 0
        elif operand == self.OP_GT:
            result = 1 if left > right else 0
        elif operand == self.OP_LT:
            result = 1 if left < right else 0
        elif operand == self.OP_GE:
            result = 1 if left >= right else 0
        elif operand == self.OP_LE:
            result = 1 if left <= right else 0
        else:
            raise Exception("Unknown eval operand: {}".format(operand))
        
        stack.append(result)
    
    # 保留原来的execute_eval方法作为备用
    def execute_eval(self, operand):
        """执行eval指令"""
        if operand == self.OP_COND_JUMP:
            # 条件跳转：弹出3个值，注意弹出顺序
            if len(self.stack) < 3:
                raise Exception("Stack underflow in conditional jump")
            else_addr = self.stack.pop()  # 最后压入的是else地址  
            then_addr = self.stack.pop()  # 然后是then地址
            condition = self.stack.pop()  # 最先压入的是条件
            
            if condition != 0:
                self.pc = then_addr // 8
            else:
                self.pc = else_addr // 8
            self.pc -= 1  # 因为主循环会+1
        else:
            # 二元运算：弹出2个值
            if len(self.stack) < 2:
                raise Exception("Stack underflow in binary operation")
            right = self.stack.pop()
            left = self.stack.pop()
            
            if operand == self.OP_ADD:
                # 保持加法的完整精度，用于可能的后续模运算
                result = left + right
            elif operand == self.OP_SUB:
                result = self._to_32bit_int(left - right)
            elif operand == self.OP_MUL:
                # 不要立即截断乘法结果，保持完整精度用于可能的模运算
                result = left * right
            elif operand == self.OP_DIV:
                if right == 0:
                    raise Exception("Division by zero")
                result = self._to_32bit_int(left // right)
            elif operand == self.OP_MOD:
                if right == 0:
                    raise Exception("Division by zero")
                # 执行模运算后再截断
                mod_result = left % right
                # 确保模运算结果为正数（当除数为正时）
                if right > 0 and mod_result < 0:
                    mod_result += right
                result = self._to_32bit_int(mod_result)
            elif operand == self.OP_GT:
                result = 1 if left > right else 0
            elif operand == self.OP_LT:
                result = 1 if left < right else 0
            elif operand == self.OP_GE:
                result = 1 if left >= right else 0
            elif operand == self.OP_LE:
                result = 1 if left <= right else 0
            elif operand == self.OP_EQ:
                result = 1 if left == right else 0
            elif operand == self.OP_NE:
                result = 1 if left != right else 0
            else:
                raise Exception("Unknown eval operand: {}".format(operand))
            
            # 对于可能参与后续模运算的操作，保持完整精度
            # 只有比较运算才需要立即转换为32位
            if operand in [self.OP_GT, self.OP_LT, self.OP_GE, self.OP_LE, self.OP_EQ, self.OP_NE]:
                self.stack.append(result)  # 比较结果总是0或1，不需要转换
            else:
                self.stack.append(result)  # 保持完整精度

def main():
    if len(sys.argv) != 2:
        print("Usage: python vm.py <bytecode_file>", file=sys.stderr)
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        vm = MandrillVM()
        vm.load_bytecode(filename)
        vm.run()
    except Exception as e:
        print("VM error: {}".format(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()