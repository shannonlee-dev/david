import sys
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class Calculator:
    """기본 계산기 클래스"""
    
    def __init__(self):
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
    
    def add(self, a, b):
        result = a + b
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def subtract(self, a, b):
        result = a - b
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def multiply(self, a, b):
        result = a * b
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError
        result = a / b
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def reset(self):
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
    
    def negative_positive(self):
        if self.current_number != '0':
            if self.current_number.startswith('-'):
                self.current_number = self.current_number[1:]
            else:
                self.current_number = '-' + self.current_number
    
    def percent(self):
        value = float(self.current_number) / 100
        self.current_number = str(value)
    
    def equal(self):
        if self.operator and not self.waiting_for_operand:
            prev = float(self.previous_number)
            curr = float(self.current_number)
            
            if self.operator == '+':
                result = self.add(prev, curr)
            elif self.operator == '-':
                result = self.subtract(prev, curr)
            elif self.operator == '×':
                result = self.multiply(prev, curr)
            elif self.operator == '÷':
                result = self.divide(prev, curr)
            else:
                result = curr
            
            self.current_number = str(result)
            self.operator = None
            self.waiting_for_operand = True
            return result


class EngineeringCalculator(Calculator, QWidget):
    """공학용 계산기 클래스 - Calculator 클래스를 상속"""
    
    def __init__(self):
        Calculator.__init__(self)
        QWidget.__init__(self)
        self.memory = 0.0
        self.angle_mode = 'rad'  # 'rad' or 'deg'
        self.init_ui()
    
    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 디스플레이
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 36px;
                font-weight: 300;
                padding: 15px;
                border: none;
            }
        """)
        self.display.setFixedHeight(80)
        main_layout.addWidget(self.display)
        
        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        
        # 첫 번째 행: 2nd, π, e, C, AC
        row1 = QHBoxLayout()
        self.create_button('2nd', row1, 'gray', self.on_button_click)
        self.create_button('π', row1, 'gray', self.on_button_click)
        self.create_button('e', row1, 'gray', self.on_button_click)
        self.create_button('C', row1, 'gray', self.on_button_click)
        self.create_button('AC', row1, 'gray', self.on_button_click)
        button_layout.addLayout(row1)
        
        # 두 번째 행: x!, x^y, rad, sin, cos
        row2 = QHBoxLayout()
        self.create_button('x!', row2, 'gray', self.on_button_click)
        self.create_button('x^y', row2, 'gray', self.on_button_click)
        self.create_button('rad', row2, 'gray', self.on_button_click)
        self.create_button('sin', row2, 'gray', self.on_button_click)
        self.create_button('cos', row2, 'gray', self.on_button_click)
        button_layout.addLayout(row2)
        
        # 세 번째 행: 1/x, x^2, ln, tan, sinh
        row3 = QHBoxLayout()
        self.create_button('1/x', row3, 'gray', self.on_button_click)
        self.create_button('x^2', row3, 'gray', self.on_button_click)
        self.create_button('ln', row3, 'gray', self.on_button_click)
        self.create_button('tan', row3, 'gray', self.on_button_click)
        self.create_button('sinh', row3, 'gray', self.on_button_click)
        button_layout.addLayout(row3)
        
        # 네 번째 행: √x, x^3, log, EE, cosh
        row4 = QHBoxLayout()
        self.create_button('√x', row4, 'gray', self.on_button_click)
        self.create_button('x^3', row4, 'gray', self.on_button_click)
        self.create_button('log', row4, 'gray', self.on_button_click)
        self.create_button('EE', row4, 'gray', self.on_button_click)
        self.create_button('cosh', row4, 'gray', self.on_button_click)
        button_layout.addLayout(row4)
        
        # 다섯 번째 행: mc, mr, m+, m-, tanh
        row5 = QHBoxLayout()
        self.create_button('mc', row5, 'gray', self.on_button_click)
        self.create_button('mr', row5, 'gray', self.on_button_click)
        self.create_button('m+', row5, 'gray', self.on_button_click)
        self.create_button('m-', row5, 'gray', self.on_button_click)
        self.create_button('tanh', row5, 'gray', self.on_button_click)
        button_layout.addLayout(row5)
        
        # 여섯 번째 행: (, ), %, +/-, ÷
        row6 = QHBoxLayout()
        self.create_button('(', row6, 'gray', self.on_button_click)
        self.create_button(')', row6, 'gray', self.on_button_click)
        self.create_button('%', row6, 'gray', self.on_button_click)
        self.create_button('+/-', row6, 'gray', self.on_button_click)
        self.create_button('÷', row6, 'orange', self.on_button_click)
        button_layout.addLayout(row6)
        
        # 일곱 번째 행: Rand, 7, 8, 9, ×
        row7 = QHBoxLayout()
        self.create_button('Rand', row7, 'gray', self.on_button_click)
        self.create_button('7', row7, 'dark_gray', self.on_button_click)
        self.create_button('8', row7, 'dark_gray', self.on_button_click)
        self.create_button('9', row7, 'dark_gray', self.on_button_click)
        self.create_button('×', row7, 'orange', self.on_button_click)
        button_layout.addLayout(row7)
        
        # 여덟 번째 행: ., 4, 5, 6, -
        row8 = QHBoxLayout()
        self.create_button('.', row8, 'dark_gray', self.on_button_click)
        self.create_button('4', row8, 'dark_gray', self.on_button_click)
        self.create_button('5', row8, 'dark_gray', self.on_button_click)
        self.create_button('6', row8, 'dark_gray', self.on_button_click)
        self.create_button('-', row8, 'orange', self.on_button_click)
        button_layout.addLayout(row8)
        
        # 아홉 번째 행: 0, 1, 2, 3, +
        row9 = QHBoxLayout()
        self.create_button('0', row9, 'dark_gray', self.on_button_click)
        self.create_button('1', row9, 'dark_gray', self.on_button_click)
        self.create_button('2', row9, 'dark_gray', self.on_button_click)
        self.create_button('3', row9, 'dark_gray', self.on_button_click)
        self.create_button('+', row9, 'orange', self.on_button_click)
        button_layout.addLayout(row9)
        
        # 마지막 행: =
        row10 = QHBoxLayout()
        row10.addStretch()
        row10.addStretch()
        row10.addStretch()
        row10.addStretch()
        self.create_button('=', row10, 'orange', self.on_button_click)
        button_layout.addLayout(row10)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 윈도우 설정
        self.setWindowTitle('Engineering Calculator')
        self.setFixedSize(600, 600)
        self.setStyleSheet("QWidget { background-color: black; }")
    
    def create_button(self, text, layout, color, callback):
        button = QPushButton(text)
        button.clicked.connect(lambda: callback(text))
        self.set_button_style(button, color)
        button.setFixedSize(100, 50)
        layout.addWidget(button)
        return button
    
    def set_button_style(self, button, color):
        if color == 'gray':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #A6A6A6;
                    color: black;
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: 400;
                }
                QPushButton:pressed {
                    background-color: #D4D4D2;
                }
            """)
        elif color == 'dark_gray':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #333333;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                    font-weight: 400;
                }
                QPushButton:pressed {
                    background-color: #737373;
                }
            """)
        elif color == 'orange':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9500;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                    font-weight: 400;
                }
                QPushButton:pressed {
                    background-color: #FFB143;
                }
            """)
    
    def on_button_click(self, text):
        try:
            if text.isdigit():
                self.input_digit(text)
            elif text == '.':
                self.input_decimal()
            elif text == 'AC':
                self.reset()
                self.display.setText('0')
            elif text == 'C':
                self.current_number = '0'
                self.display.setText('0')
            elif text == '+/-':
                self.negative_positive()
                self.display.setText(self.current_number)
            elif text == '%':
                self.percent()
                self.display.setText(self.current_number)
            elif text in ['+', '-', '×', '÷', 'x^y']:
                self.set_operator(text)
            elif text == '=':
                result = self.equal()
                if result is not None:
                    self.display.setText(str(result))
            elif text == 'π':
                self.current_number = str(math.pi)
                self.display.setText(self.current_number)
            elif text == 'e':
                self.current_number = str(math.e)
                self.display.setText(self.current_number)
            elif text == 'sin':
                result = self.sin(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'cos':
                result = self.cos(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'tan':
                result = self.tan(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'sinh':
                result = self.sinh(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'cosh':
                result = self.cosh(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'tanh':
                result = self.tanh(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'x^2':
                result = self.square(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'x^3':
                result = self.cube(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == '√x':
                result = self.square_root(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'ln':
                result = self.natural_log(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'log':
                result = self.log10(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == '1/x':
                result = self.reciprocal(float(self.current_number))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'x!':
                result = self.factorial(int(float(self.current_number)))
                self.current_number = str(result)
                self.display.setText(self.current_number)
            elif text == 'mc':
                self.memory_clear()
            elif text == 'mr':
                self.current_number = str(self.memory)
                self.display.setText(self.current_number)
            elif text == 'm+':
                self.memory_add(float(self.current_number))
            elif text == 'm-':
                self.memory_subtract(float(self.current_number))
            elif text == 'Rand':
                self.current_number = str(random.random())
                self.display.setText(self.current_number)
            elif text == 'rad':
                self.angle_mode = 'deg' if self.angle_mode == 'rad' else 'rad'
                
        except (ValueError, ZeroDivisionError, OverflowError, ArithmeticError) as e:
            self.display.setText('Error')
            self.reset()
    
    def input_digit(self, digit):
        if self.waiting_for_operand:
            self.current_number = digit
            self.waiting_for_operand = False
        else:
            if self.current_number == '0':
                self.current_number = digit
            else:
                self.current_number += digit
        
        self.display.setText(self.current_number)
    
    def input_decimal(self):
        if self.waiting_for_operand:
            self.current_number = '0.'
            self.waiting_for_operand = False
        elif '.' not in self.current_number:
            self.current_number += '.'
        
        self.display.setText(self.current_number)
    
    def set_operator(self, operator):
        if self.operator and not self.waiting_for_operand:
            self.equal()
        
        self.previous_number = self.current_number
        self.operator = operator
        self.waiting_for_operand = True
    
    def equal(self):
        if self.operator and not self.waiting_for_operand:
            prev = float(self.previous_number)
            curr = float(self.current_number)
            
            if self.operator == '+':
                result = self.add(prev, curr)
            elif self.operator == '-':
                result = self.subtract(prev, curr)
            elif self.operator == '×':
                result = self.multiply(prev, curr)
            elif self.operator == '÷':
                result = self.divide(prev, curr)
            elif self.operator == 'x^y':
                result = self.power(prev, curr)
            else:
                result = curr
            
            self.current_number = str(result)
            self.operator = None
            self.waiting_for_operand = True
            return result
        return None
    
    # 삼각함수 메소드들
    def sin(self, x):
        if self.angle_mode == 'deg':
            x = math.radians(x)
        result = math.sin(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def cos(self, x):
        if self.angle_mode == 'deg':
            x = math.radians(x)
        result = math.cos(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def tan(self, x):
        if self.angle_mode == 'deg':
            x = math.radians(x)
        # tan의 특이점 체크
        if abs(math.cos(x)) < 1e-15:
            raise ArithmeticError("tan undefined")
        result = math.tan(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def sinh(self, x):
        result = math.sinh(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def cosh(self, x):
        result = math.cosh(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def tanh(self, x):
        result = math.tanh(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    # 기타 수학 함수들
    def square(self, x):
        result = x * x
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def cube(self, x):
        result = x * x * x
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def square_root(self, x):
        if x < 0:
            raise ArithmeticError("Square root of negative number")
        result = math.sqrt(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def power(self, base, exponent):
        try:
            result = math.pow(base, exponent)
            if abs(result) > 1e15:
                raise OverflowError
            return result
        except ValueError:
            raise ArithmeticError("Invalid power operation")
    
    def natural_log(self, x):
        if x <= 0:
            raise ArithmeticError("Log of non-positive number")
        result = math.log(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def log10(self, x):
        if x <= 0:
            raise ArithmeticError("Log of non-positive number")
        result = math.log10(x)
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def reciprocal(self, x):
        if x == 0:
            raise ZeroDivisionError
        result = 1.0 / x
        if abs(result) > 1e15:
            raise OverflowError
        return result
    
    def factorial(self, n):
        if n < 0 or n != int(n):
            raise ArithmeticError("Factorial of negative or non-integer")
        if n > 170:  # factorial(171) causes overflow
            raise OverflowError
        result = math.factorial(n)
        return result
    
    # 메모리 기능들
    def memory_clear(self):
        self.memory = 0.0
    
    def memory_add(self, value):
        self.memory += value
    
    def memory_subtract(self, value):
        self.memory -= value


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = EngineeringCalculator()
    calculator.show()
    sys.exit(app.exec_())