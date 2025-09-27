import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
        self.init_ui()
    
    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 40, 20, 30)
        main_layout.setSpacing(15)
        
        # 상단 여백 (상태바 공간)
        top_spacer = QLabel()
        top_spacer.setFixedHeight(100)
        main_layout.addWidget(top_spacer)
        
        # 디스플레이
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.display.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 80px;
                font-weight: 200;
                padding: 0px 20px 20px 20px;
                border: none;
            }
        """)
        self.display.setFixedHeight(120)
        main_layout.addWidget(self.display)
        
        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # 첫 번째 행: AC, +/-, %, ÷
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        self.create_button('AC', row1, 'light_gray', self.on_button_click)
        self.create_button('+/-', row1, 'light_gray', self.on_button_click)
        self.create_button('%', row1, 'light_gray', self.on_button_click)
        self.create_button('÷', row1, 'orange', self.on_button_click)
        button_layout.addLayout(row1)
        
        # 두 번째 행: 7, 8, 9, ×
        row2 = QHBoxLayout()
        row2.setSpacing(15)
        self.create_button('7', row2, 'dark_gray', self.on_button_click)
        self.create_button('8', row2, 'dark_gray', self.on_button_click)
        self.create_button('9', row2, 'dark_gray', self.on_button_click)
        self.create_button('×', row2, 'orange', self.on_button_click)
        button_layout.addLayout(row2)
        
        # 세 번째 행: 4, 5, 6, -
        row3 = QHBoxLayout()
        row3.setSpacing(15)
        self.create_button('4', row3, 'dark_gray', self.on_button_click)
        self.create_button('5', row3, 'dark_gray', self.on_button_click)
        self.create_button('6', row3, 'dark_gray', self.on_button_click)
        self.create_button('-', row3, 'orange', self.on_button_click)
        button_layout.addLayout(row3)
        
        # 네 번째 행: 1, 2, 3, +
        row4 = QHBoxLayout()
        row4.setSpacing(15)
        self.create_button('1', row4, 'dark_gray', self.on_button_click)
        self.create_button('2', row4, 'dark_gray', self.on_button_click)
        self.create_button('3', row4, 'dark_gray', self.on_button_click)
        self.create_button('+', row4, 'orange', self.on_button_click)
        button_layout.addLayout(row4)
        
        # 다섯 번째 행: 계산기 아이콘, 0, ., =
        row5 = QHBoxLayout()
        row5.setSpacing(15)
        
        # 계산기 아이콘 버튼 (왼쪽 하단)
        calc_icon_button = QPushButton('⚏')  # 계산기 아이콘 대신 기호 사용
        calc_icon_button.clicked.connect(lambda: self.on_button_click('calc'))
        self.set_button_style(calc_icon_button, 'dark_gray')
        calc_icon_button.setFixedSize(80, 80)
        row5.addWidget(calc_icon_button)
        
        # 0 버튼
        self.create_button('0', row5, 'dark_gray', self.on_button_click)
        
        # 소수점 버튼
        self.create_button('.', row5, 'dark_gray', self.on_button_click)
        
        # = 버튼
        self.create_button('=', row5, 'orange', self.on_button_click)
        
        button_layout.addLayout(row5)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 윈도우 설정
        self.setWindowTitle('Calculator')
        self.setFixedSize(400, 700)
        self.setStyleSheet("QWidget { background-color: black; }")
    
    def create_button(self, text, layout, color, callback):
        button = QPushButton(text)
        button.clicked.connect(lambda: callback(text))
        self.set_button_style(button, color)
        button.setFixedSize(80, 80)
        layout.addWidget(button)
        return button
    
    def set_button_style(self, button, color):
        if color == 'light_gray':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #A5A5A5;
                    color: black;
                    border: none;
                    border-radius: 40px;
                    font-size: 36px;
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
                    border-radius: 40px;
                    font-size: 36px;
                    font-weight: 300;
                }
                QPushButton:pressed {
                    background-color: #737373;
                }
            """)
        elif color == 'orange':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9F0A;
                    color: white;
                    border: none;
                    border-radius: 40px;
                    font-size: 36px;
                    font-weight: 400;
                }
                QPushButton:pressed {
                    background-color: #FFB143;
                }
            """)
    
    def on_button_click(self, text):
        if text.isdigit():
            self.input_digit(text)
        elif text == '.':
            self.input_decimal()
        elif text == 'AC':
            self.reset()
        elif text == '+/-':
            self.negative_positive()
        elif text == '%':
            self.percent()
        elif text in ['+', '-', '×', '÷']:
            self.set_operator(text)
        elif text == '=':
            self.equal()
        elif text == 'calc':
            # 계산기 아이콘 클릭 시 (추가 기능을 위한 예약)
            pass
    
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
            try:
                result = self.calculate()
                self.current_number = str(result)
                self.display.setText(self.current_number)
                self.operator = None
                self.waiting_for_operand = True
            except ZeroDivisionError:
                self.display.setText('Error')
                self.reset()
            except OverflowError:
                self.display.setText('Error')
                self.reset()
    
    def calculate(self):
        prev = float(self.previous_number)
        curr = float(self.current_number)
        
        if self.operator == '+':
            return self.add(prev, curr)
        elif self.operator == '-':
            return self.subtract(prev, curr)
        elif self.operator == '×':
            return self.multiply(prev, curr)
        elif self.operator == '÷':
            return self.divide(prev, curr)
        
        return curr
    
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
        self.display.setText('0')
    
    def negative_positive(self):
        if self.current_number != '0':
            if self.current_number.startswith('-'):
                self.current_number = self.current_number[1:]
            else:
                self.current_number = '-' + self.current_number
            self.display.setText(self.current_number)
    
    def percent(self):
        try:
            value = float(self.current_number) / 100
            self.current_number = str(value)
            self.display.setText(self.current_number)
        except ValueError:
            self.display.setText('Error')
            self.reset()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())