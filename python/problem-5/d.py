import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from calculator import Calculator


class EngineeringCalculator(Calculator):
    
    def __init__(self):
        # Calculator의 초기화를 먼저 실행하지 않고 직접 속성들을 설정
        QWidget.__init__(self)
        self.current_number = '0'
        self.previous_number = '0'
        self.operator = None
        self.waiting_for_operand = False
        self.percent_pending = False  
        self.expression = ''
        self.error_state = False
        self.parentheses_count = 0  # 열린 괄호 개수
        self.pending_function = None  # 대기 중인 함수
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 120, 20, 30)
        main_layout.setSpacing(15)
        
        
        # 디스플레이
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.display.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 70px;
                font-weight: 500; 
                padding-right: 10px;
                padding-bottom: 0px;
                padding-top: 0px;
                border: none
            }
        """)
        self.display.setFixedHeight(100)
        main_layout.addWidget(self.display)
        
        # 버튼 그리드 (아이폰 가로 모드 완전 재현)s 
        buttons = [
            # 행 1
            ['(', ')', 'mc', 'm+', 'm-', 'mr', 'AC', '+/-', '%', '÷'],
            # 행 2  
            ['2nd', 'x²', 'x³', 'xʸ', 'eˣ', '10ˣ', '7', '8', '9', '×'],
            # 행 3
            ['1/x', '²√x', '³√x', 'ʸ√x', 'ln', 'log₁₀', '4', '5', '6', '-'],
            # 행 4
            ['x!', 'sin', 'cos', 'tan', 'e', 'EE', '1', '2', '3', '+'],
            # 행 5
            ['⚏', 'sinh', 'cosh', 'tanh', 'π', 'Deg', 'Rand', '0', '.', '=']
        ]
        
        # 작동하는 기능들 정의
        self.active_functions = {
            # 기본 계산
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', 
            '+', '-', '×', '÷', '=', 'AC', '+/-', '%',
            # 괄호
            '(', ')',
            # 핵심 공학 기능
            'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh', 'x²', 'x³', 'π'
        }
        
        for row in buttons:
            h_layout = QHBoxLayout()
            h_layout.setSpacing(10)
            for i, text in enumerate(row):
                button = self.create_button(text, self.get_color(text))
                h_layout.addWidget(button)
                    
            main_layout.addLayout(h_layout)
        
        self.setLayout(main_layout)
        self.setWindowTitle('공학용 계산기')
        self.setFixedSize(1400, 700)
        self.setStyleSheet("QWidget { background-color: black; }")
    
    def create_button(self, text, color):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.on_button_click(text))
        
        text_color = 'white'
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: {text_color};
                border: none; border-radius: 30px; font-size: 25px; font-weight: 550;
            }}
            QPushButton:pressed {{ background-color: #555; }}
        """)
        button.setFixedSize(110, 80)
        return button
    
    def get_color(self, text):

        if text.isdigit() or text == '.' or text == 'Rand':
            return '#505050'

        elif text in ['+', '-', '×', '÷', '=']:
            return '#FF9500'

        elif text in ['AC', '+/-', '%']:
            return '#A6A6A6'
        else:
            return '#333'    
    
    def update_display(self):
        # 부모 클래스의 표시 로직 사용
        current_for_view = self.current_number + '%' if self.percent_pending else self.current_number

        if self.expression and not self.waiting_for_operand:
            display_text = self.expression + current_for_view
        elif self.expression and self.waiting_for_operand:
            display_text = self.expression.rstrip()
        else:
            display_text = current_for_view
        
        # 에러 메시지 및 긴 텍스트에 대한 폰트 크기 조정
        if display_text == '정의되지 않음':
            font_size = 50
        elif display_text == '오버플로':
            font_size = 50
        elif len(display_text) >= 15:
            font_size = 48
        elif len(display_text) > 12:
            font_size = 56
        else:
            font_size = 70
            
        self.display.setStyleSheet(f"""
            QLabel {{
                background-color: black;
                color: white;
                font-size: {font_size}px;
                font-weight: 500;
                padding-right: 10px;
                padding-bottom: 10px;
                padding-top: 0px;
                border: none
            }}
        """)
        self.display.setText(display_text)
    
    def on_button_click(self, text):
        
        if text not in self.active_functions:
            return 
        
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
        
        # === 괄호 처리 ===
        elif text == '(':
            self.input_open_parenthesis()
        elif text == ')':
            self.input_close_parenthesis()
        
        # === 추가된 공학 함수들 ===
        elif text == 'π':
            self.input_constant(math.pi)
        elif text in ['sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh']:
            self.input_function(text)
        elif text == 'x²':
            self.apply_function(self.square)
        elif text == 'x³':
            self.apply_function(self.cube)
        else:
            pass  # 기타 버튼
    
    def input_constant(self, value):
        """상수 입력"""
        self.current_number = f"{value:.10g}"
        self.waiting_for_operand = False
        self.update_display()
    
    def input_function(self, func_name):
        """함수 입력 (sin, cos 등)"""
        if self.current_number == '0' or self.waiting_for_operand:
            self.current_number = ''
        
        self.current_number += f"{func_name}("
        self.parentheses_count += 1
        self.waiting_for_operand = True
        self.update_display()
    
    def input_open_parenthesis(self):
        """여는 괄호 입력"""
        if self.current_number == '0' or self.waiting_for_operand:
            self.current_number = '('
        else:
            self.current_number += '('
        
        self.parentheses_count += 1
        self.waiting_for_operand = True
        self.update_display()
    
    def input_close_parenthesis(self):
        """닫는 괄호 입력"""
        if self.parentheses_count > 0:
            if self.current_number.endswith('('):
                # 빈 괄호는 허용하지 않음
                return
            
            self.current_number += ')'
            self.parentheses_count -= 1
            self.waiting_for_operand = False
            self.update_display()
    
    def apply_function(self, func):
        """단일 인수 함수 적용"""
        try:
            result = func(float(self.current_number))
            # 결과 포맷팅
            if isinstance(result, float) and result.is_integer():
                self.current_number = str(int(result))
            else:
                if abs(result) < 1e-6 or abs(result) > 1e12:
                    self.current_number = f"{result:.6e}"
                else:
                    self.current_number = f"{result:.10g}"
            self.waiting_for_operand = False
            self.update_display()
        except Exception as e:
            self.display.setText('Error')
            print(f"Function error: {e}")
    
    def equal(self):
        """계산 실행 - 공학 함수 지원"""
        if self.error_state:
            self.error_state = False
            self.reset()
            return

        # 괄호가 열려있으면 자동으로 닫기
        while self.parentheses_count > 0:
            self.current_number += ')'
            self.parentheses_count -= 1

        try:
            # 식에 함수가 포함되어 있으면 eval로 계산
            if any(func in self.current_number for func in ['sin(', 'cos(', 'tan(', 'sinh(', 'cosh(', 'tanh(']):
                result = self.evaluate_expression(self.current_number)
            else:
                # 기본 계산은 부모 클래스 메서드 사용
                super().equal()
                return
            
            # 결과 포맷팅
            if isinstance(result, float) and result.is_integer():
                self.current_number = str(int(result))
            else:
                if abs(result) < 1e-6 or abs(result) > 1e12:
                    self.current_number = f"{result:.6e}"
                else:
                    self.current_number = f"{result:.10g}"
            
            self.expression = ''
            self.operator = None
            self.waiting_for_operand = True
            self.update_display()
            
        except Exception as e:
            self.current_number = '오류'
            self.error_state = True
            self.expression = ''
            self.operator = None
            self.waiting_for_operand = True
            self.update_display()
            print(f"Calculation error: {e}")
    
    def evaluate_expression(self, expression):

        safe_dict = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'pi': math.pi,
        }
        
        try:
            # 기본 연산자 변환
            expression = expression.replace('×', '*').replace('÷', '/')
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return result
        except:
            raise ValueError("계산 오류")
    
    def reset(self):
        """초기화 - 괄호 상태도 포함"""
        super().reset()
        self.parentheses_count = 0
        self.pending_function = None
    
    # 일부 기본 계산기 메서드들은 부모 클래스에서 상속받음
    
    # ===== 작동하는 공학 함수 메소드들 =====
    
    def sin(self, x):
        """사인 함수 (라디안)"""
        return math.sin(x)
    
    def cos(self, x):
        """코사인 함수 (라디안)"""
        return math.cos(x)
    
    def tan(self, x):
        """탄젠트 함수 (라디안)"""
        result = math.tan(x)
        # tan(π/2) 등의 경우 무한대 처리
        if abs(result) > 1e15:
            raise ValueError("Undefined")
        return result
    
    def sinh(self, x):
        """하이퍼볼릭 사인"""
        return math.sinh(x)
    
    def cosh(self, x):
        """하이퍼볼릭 코사인"""
        return math.cosh(x)
    
    def tanh(self, x):
        """하이퍼볼릭 탄젠트"""
        return math.tanh(x)
    
    def square(self, x):
        """제곱 (x²)"""
        return x * x
    
    def cube(self, x):
        """세제곱 (x³)"""
        return x * x * x


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = EngineeringCalculator()
    calculator.show()
    sys.exit(app.exec_())