import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
        self.percent_pending = False  
        self.expression = ''
        self.error_state = False
        self.init_ui()
    
    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 140, 20, 30) 

        # 디스플레이
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.display.setStyleSheet("""
            QLabel {ㄴ
                background-color: black;
                color: white;
                font-size: 70px;
                font-weight: 500;                       
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
        
        # 다섯 번째 행: (아이콘), 0, ., =
        row5 = QHBoxLayout()
        row5.setSpacing(15)
        self.create_button('⚏', row5, 'dark_gray', self.on_button_click)        
        self.create_button('0', row5, 'dark_gray', self.on_button_click)
        self.create_button('.', row5, 'dark_gray', self.on_button_click)
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
        # 안전한 연결(checked 인자 무시)
        button.clicked.connect(lambda checked=False, t=text: callback(t))
        self.set_button_style(button, color)
        button.setFixedSize(80, 80)
        layout.addWidget(button)
        return button
    
    def set_button_style(self, button, color):
        if color == 'light_gray':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #5C5C5F;
                    color: white;
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
                    background-color: #2A2A2C;
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
    
    def update_display(self):
        """화면 표시 업데이트"""
        # 퍼센트 지연 상태면 현재 숫자에 %를 붙여 보여줌
        current_for_view = self.current_number + '%' if self.percent_pending else self.current_number

        if self.expression and not self.waiting_for_operand:
            display_text = self.expression + current_for_view
        elif self.expression and self.waiting_for_operand:
            display_text = self.expression.rstrip()
        else:
            display_text = current_for_view
        
        if display_text == '정의되지 않음':
            font_size = 50
        elif display_text == '오버플로':
            font_size = 50
        elif len(display_text) >= 10:
            font_size = 50
        elif len(display_text) > 8:
            font_size = 60
        
        else:
            font_size = 70
            
        self.display.setStyleSheet(f"""
            QLabel {{
                background-color: black;
                color: white;
                font-size: {font_size}px;
                font-weight: 500;
                border: none;
            }}
        """)
        self.display.setText(display_text)
    
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
        else:
            pass  # 기타 버튼
    
    def input_digit(self, digit):

        if self.error_state:
            self.error_state = False
            self.reset()  

        if self.percent_pending and self.operator is None and not self.waiting_for_operand:
            self.operator = '%'                          # 모듈로 연산자
            self.expression = self.current_number + ' % '
            self.previous_number = self.current_number
            self.waiting_for_operand = True
            self.percent_pending = False

        if self.waiting_for_operand:
            self.current_number = digit
            self.waiting_for_operand = False

        else:
            if self.current_number == '0':
                self.current_number = digit
            else:
                self.current_number += digit
  
        self.update_display()
    
    def input_decimal(self):
        if self.error_state:
            self.error_state = False
            self.reset() 

        if self.percent_pending and self.operator is None and not self.waiting_for_operand:
            self.percent_pending = False

        if self.waiting_for_operand:
            self.current_number = '0.'
            self.waiting_for_operand = False
        elif '.' not in self.current_number:
            self.current_number += '.'
        
        self.update_display()
    
    def set_operator(self, operator):
        # 퍼센트 지연 중에 다른 연산자를 누르면, 현재 값을 실제 % 값으로 변환 후 진행
        if self.error_state:
            self.error_state = False
            self.reset() 

        if self.percent_pending:
            self.current_number = str(float(self.current_number) / 100)
            self.percent_pending = False

        if self.operator and not self.waiting_for_operand:
            # 연속 연산인 경우 먼저 계산
            self.equal()
        
        # 수식에 현재 숫자와 연산자 추가
        self.expression = self.current_number + f' {operator} '
        self.previous_number = self.current_number
        self.operator = operator
        self.waiting_for_operand = True
        self.update_display()
    
    def equal(self):
        # 1) 연산자 없이 "%, ="만: 단독 퍼센트 변환
        if self.error_state:
            self.error_state = False
            self.reset() 

        if self.operator is None and self.percent_pending:
            value = float(self.current_number) / 100
            self.current_number = str(int(value)) if value == int(value) else str(value)
            self.percent_pending = False
            self.waiting_for_operand = True
            self.expression = ''
            self.update_display()
            return

        # 2) 일반 계산 (모듈로 포함)
        if self.operator and not self.waiting_for_operand:
            try:
                result = self.calculate()

                # 결과 포맷
                if result == int(result):
                    result_str = str(int(result))
                else:
                    result_str = format(result, '.9g')
                
                self.current_number = result_str
                self.expression = ''
                self.operator = None
                self.waiting_for_operand = True
                self.update_display()
            except ZeroDivisionError:
                self.current_number = '정의되지 않음'
                self.error_state = True
                self.expression = ''
                self.operator = None
                self.waiting_for_operand = True
                self.update_display()
            except OverflowError:
                self.current_number = '오버플로'
                self.error_state = True
                self.expression = ''
                self.operator = None
                self.waiting_for_operand = True
                self.update_display()

        else:
            self.update_display()
    
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
        elif self.operator == '%':
            return self.modulo(prev, curr)
        

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
    
    def modulo(self, a, b):
        # 정수 나머지로 해석
        bi = int(b)
        if bi == 0:
            raise ZeroDivisionError
        ai = int(a)
        result = ai % bi
        if abs(result) > 1e15:
            raise OverflowError
        return float(result)
    
    def reset(self):
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
        self.percent_pending = False
        self.expression = ''
        self.update_display()
    
    def negative_positive(self):

        if self.error_state:
            self.error_state = False
            self.reset() 

        if self.current_number[-1] == '.':
            return

        if self.percent_pending:
            value = float(self.current_number) / 100
            self.current_number = str(int(value)) if value == int(value) else str(value)
            self.percent_pending = False

        if self.current_number != '0':
            if self.current_number.startswith('-'):
                self.current_number = self.current_number[1:]
            else:
                self.current_number = '-' + self.current_number

        self.update_display()
    
    def percent(self):

        if self.error_state:
            self.error_state = False
            self.reset() 

        self.percent_pending = True
        self.update_display()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())
