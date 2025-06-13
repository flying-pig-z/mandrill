# mandrill2025
2025年编译原理作业

感谢强大的AI

代码中所涉及的理论知识点

| 课本理论内容                 | 实验代码应用           | 对应模块                        |
| ---------------------------- | ---------------------- | ------------------------------- |
| **有限状态自动机 (FSA/DFA)** | 词法分析器的Token识别  | `lexer.py`                      |
| **正则表达式**               | 词法模式定义           | `lexer.py`                      |
| **上下文无关文法**           | 语法规则的递归下降实现 | `parser.py`                     |
| **LL(1)分析**                | 递归下降语法分析器     | `parser.py`                     |
| **抽象语法树 (AST)**         | AST节点类和构造过程    | `interpreter.py`, `compiler.py` |
| **语法制导定义 (SDD)**       | AST构造和代码生成      | `compiler.py`                   |
| **三地址码**                 | 中间代码表示和生成     | `compiler.py`                   |
| **虚拟机执行**               | 栈式计算和指令解释     | `vm.py`                         |

测试仓库：https://github.com/croissantfish/mandrill-compiler-testcases
