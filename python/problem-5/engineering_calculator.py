import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from calculator import Calculator


class TrigExpressionBuffer:
    """삼각 함수 괄호 안 입력을 관리하는 버퍼"""

    OPERATORS = {'+', '-', '×', '÷'}

    def __init__(self):
        self.expression = ''
        self.negative = False

    def reset(self):
        self.expression = ''
        self.negative = False

    def input2_digit(self, digit: str):
        self.expression += digit

    def input2_decimal(self):
        segment = self._current_segment()  # 3.14 + 2 에서 '.' 입력시 문제를 해결 하기 위해
        if '.' in segment:
            return
        if not self.expression or self.expression[-1] in self.OPERATORS:
            self.expression += '0.'
        else:
            self.expression += '.'

    def input2_operator(self, operator: str):
        if not self.expression:
            return
        if self.expression[-1] in self.OPERATORS:  #연산자 교체 
            self.expression = self.expression[:-1] + operator
        else:
            self.expression += operator

    def insert_pi(self):
        if not self.expression:
            self.expression = 'π'
        elif self.expression[-1] in self.OPERATORS:
            self.expression += 'π'

    def toggle_sign(self):
        self.negative = not self.negative

    def display(self) -> str:
        prefix = '-' if self.negative else ''    # -/+ 버튼
        return prefix + self.expression

    def evaluate(self) -> float:
        expr = self.expression.strip()
        if not expr:
            value = 0.0
        else:
            if expr[-1] in self.OPERATORS:
                raise ValueError
            python_expr = expr.replace('×', '*').replace('÷', '/').replace('π', f'({math.pi})')
            try:
                value = eval(python_expr, {"__builtins__": None}, {})  # 시스템 암살 방지
            except Exception:
                raise ValueError
            if not isinstance(value, (int, float)):
                raise ValueError
        value = float(value)
        return -value if self.negative else value

    def _current_segment(self) -> str:
        if not self.expression:
            return ''
        last_index = max(self.expression.rfind(op) for op in self.OPERATORS)
        if last_index == -1:   # 연산자가 없는 상황
            return self.expression
        return self.expression[last_index + 1:]


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
        self.trig_active = False
        self.trig_function_name = None
        self.trig_buffer = TrigExpressionBuffer()
        self.close_paren_button = None
        self.trig_function_map = {
            'sin': self.sin,
            'cos': self.cos,
            'tan': self.tan,
            'sinh': self.sinh,
            'cosh': self.cosh,
            'tanh': self.tanh,
        }
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
            ')',
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
        if text == '(':
            button.setEnabled(False)
        elif text == ')':
            button.setEnabled(False)
            self.close_paren_button = button
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
        if self.trig_active:
            inner = self.trig_buffer.display()
            prefix = self.expression if self.expression else ''
            display_text = f"{prefix}{self.trig_function_name}({inner}"
        else:
            current_for_view = self.current_number + '%' if self.percent_pending else self.current_number

            if self.expression and not self.waiting_for_operand:
                display_text = self.expression + current_for_view
            elif self.expression and self.waiting_for_operand:
                display_text = self.expression.rstrip()
            else:
                display_text = current_for_view
        
        # 에러 메시지 및 긴 텍스트에 대한 폰트 크기 조정
        if display_text == '정의되지 않음':
            font_size = 54
        elif display_text == '오버플로':
            font_size = 54
        elif len(display_text) > 28:
            font_size = 54
        elif len(display_text) > 27:
            font_size = 66
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

        if self.trig_active:   #삼각함수 입력중일 EO
            if text == ')':
                self.finish_trig_function()
            elif text == 'AC':
                self.reset()
            elif text == '+/-':
                self.trig_toggle_sign()
            elif text == '.':
                self.trig_input2_decimal()
            elif text == 'π':
                self.trig_insert_pi()
            elif text.isdigit():
                self.trig_input2_digit(text)
            elif text in ['+', '-', '×', '÷']:
                self.trig_input2_operator(text)
            elif text == '=':
                if self.finish_trig_function():
                    self.equal()
            else:

                pass
            return

        if text not in self.active_functions:
            return

        if text in self.trig_function_map:
            self.start_trig_function(text)
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
        elif text == ')':
            # 삼각 함수 입력 중이 아닐 때는 무시
            return
        elif text == '=':
            self.equal()
        elif text == 'π':
            self.input_constant(math.pi)
        elif text == 'x²':
            self.apply_function(self.square)
        elif text == 'x³':
            self.apply_function(self.cube)
        else:
            pass
    
    def input_constant(self, value):
        """상수 입력"""
        self.current_number = self._format_number(float(value))
        self.waiting_for_operand = False
        self.update_display()
    

    def start_trig_function(self, func_name):
        """삼각/쌍곡 함수 입력 시작"""
        if self.error_state:
            self.error_state = False
            self.reset()

        self.trig_active = True
        self.trig_function_name = func_name
        self.trig_buffer.reset()
        if self.close_paren_button:
            self.close_paren_button.setEnabled(True)
        self.waiting_for_operand = False
        self.update_display()

    def trig_input2_digit(self, digit):
        self.trig_buffer.input2_digit(digit)
        self.update_display()

    def trig_input2_decimal(self):
        self.trig_buffer.input2_decimal()
        self.update_display()

    def trig_insert_pi(self):
        self.trig_buffer.insert_pi()
        self.update_display()

    def trig_toggle_sign(self):
        self.trig_buffer.toggle_sign()
        self.update_display()

    def trig_input2_operator(self, operator):
        self.trig_buffer.input2_operator(operator)
        self.update_display()

    def finish_trig_function(self):
        if not self.trig_active:
            return False

        try:
            func_name = self.trig_function_name
            func = self.trig_function_map.get(func_name)
            value = self.trig_buffer.evaluate()

            if func_name == 'tan' and abs(math.cos(value)) < 1e-12:
                raise ZeroDivisionError

            self.trig_active = False
            self.trig_function_name = None
            self.trig_buffer.reset()
            if self.close_paren_button:
                self.close_paren_button.setEnabled(False)

            self.current_number = str(value)
            if func:
                self.apply_function(func)
            else:
                self.update_display()
            return True
        except ValueError:
            self._set_error('정의되지 않음')
            return False
        except ZeroDivisionError:
            self._set_error('정의되지 않음')
            return False


    def _set_error(self, message):
        self.error_state = True
        self.current_number = message
        self.expression = ''
        self.operator = None
        self.waiting_for_operand = True
        self.percent_pending = False
        self.previous_number = '0'

        self.trig_active = False
        self.trig_function_name = None
        self.trig_buffer.reset()
        if self.close_paren_button:
            self.close_paren_button.setEnabled(False)

        self.update_display()

    def _format_number(self, value: float) -> str:
        epsilon = 1e-12
        if abs(value) < epsilon:
            value = 0.0
        else:
            nearest_int = round(value)
            if math.isclose(value, nearest_int, abs_tol=epsilon):
                value = float(nearest_int)

        if abs(value) < 1e-6 and value != 0.0:
            return f"{value:.6e}"
        if abs(value) > 1e12:
            return f"{value:.6e}"
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.10g}"

    def apply_function(self, func):
        """단일 인수 함수 적용"""
        try:
            value = float(self.current_number)
            raw_result = func(value)
            
            if not isinstance(raw_result, (int, float)):
                raise ValueError

            result = float(raw_result)
            if not math.isfinite(result):
                raise OverflowError

            self.current_number = self._format_number(result)
            self.waiting_for_operand = False
            self.update_display()
        except OverflowError:
            self._set_error('오버플로')
        except ValueError:
            self._set_error('정의되지 않음')
        except Exception as e:
            self._set_error('정의되지 않음')    
    
    def reset(self):
        self.trig_active = False
        self.trig_function_name = None
        self.trig_buffer.reset()
        if self.close_paren_button:
            self.close_paren_button.setEnabled(False)
        super().reset()
    
    
    
    #===================================
    #          추가한   메서드            #
    #===================================
    def sin(self, x):
        return math.sin(x)
    
    def cos(self, x):
        return math.cos(x)
    
    def tan(self, x):
        result = math.tan(x)

        if abs(result) > 1e15:
            raise ValueError("정의되지 않음")
        return result
    
    def sinh(self, x):
        return math.sinh(x)
    
    def cosh(self, x):
        return math.cosh(x)
    
    def tanh(self, x):
        return math.tanh(x)
    
    def square(self, x):
        return x * x
    
    def cube(self, x):
        return x * x * x


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = EngineeringCalculator()
    calculator.show()
    sys.exit(app.exec_())