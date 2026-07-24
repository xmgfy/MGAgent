import math
import operator

def calculate(expression: str) -> str:
    try:
        safe_expr = expression.replace('^', '**')
        allowed_chars = set('0123456789+-*/().%^ ')
        for char in safe_expr:
            if char not in allowed_chars:
                return f"错误: 表达式包含非法字符 '{char}'"
        
        result = eval(safe_expr, {"__builtins__": None}, {
            "math": math,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "exp": math.exp,
            "abs": abs,
            "pow": pow,
        })
        
        return f"计算结果: {result}"
    except ZeroDivisionError:
        return "错误: 除以零"
    except Exception as e:
        return f"计算错误: {str(e)}"