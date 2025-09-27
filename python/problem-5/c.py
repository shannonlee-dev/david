import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class EngineeringCalculator(QWidget):
    def __init__(self):
        super().__init__()
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
        
        # 두 번째 행: x!, (x^y), rad, sin, cos
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
        # 버튼 클릭 이벤트 처리
        current_text = self.display.text()
        
        if text.isdigit():
            # 숫자 입력
            if current_text == '0':
                self.display.setText(text)
            else:
                self.display.setText(current_text + text)
        elif text == '.':
            # 소수점 입력
            if '.' not in current_text:
                self.display.setText(current_text + '.')
        elif text == 'AC':
            # 초기화
            self.display.setText('0')
        elif text == 'C':
            # 현재 입력 지우기
            self.display.setText('0')
        elif text in ['+', '-', '×', '÷']:
            # 연산자 입력 (현재는 표시만)
            self.display.setText(current_text + ' ' + text + ' ')
        elif text in ['sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh']:
            # 삼각함수 (현재는 표시만)
            self.display.setText(text + '(' + current_text + ')')
        elif text in ['x^2', 'x^3', '√x', 'ln', 'log', '1/x', 'x!']:
            # 단항 연산자 (현재는 표시만)
            if text == 'x^2':
                self.display.setText(current_text + '^2')
            elif text == 'x^3':
                self.display.setText(current_text + '^3')
            elif text == '√x':
                self.display.setText('√(' + current_text + ')')
            else:
                self.display.setText(text + '(' + current_text + ')')
        elif text == 'π':
            # 파이 상수
            self.display.setText('π')
        elif text == 'e':
            # 자연상수 e
            self.display.setText('e')
        elif text == '=':
            # 계산 (현재는 구현되지 않음)
            pass
        elif text == '+/-':
            # 음수/양수 변환 (현재는 구현되지 않음)
            pass
        elif text == '%':
            # 퍼센트 (현재는 구현되지 않음)
            pass
        elif text in ['(', ')']:
            # 괄호 입력
            self.display.setText(current_text + text)
        elif text in ['mc', 'mr', 'm+', 'm-']:
            # 메모리 기능 (현재는 구현되지 않음)
            pass
        elif text == 'Rand':
            # 랜덤 수 생성 (현재는 구현되지 않음)
            pass
        elif text == 'EE':
            # 과학적 표기법 (현재는 구현되지 않음)
            pass
        elif text == 'x^y':
            # 거듭제곱 (현재는 표시만)
            self.display.setText(current_text + '^')
        elif text == '2nd':
            # 2차 함수 모드 (현재는 구현되지 않음)
            pass
        elif text == 'rad':
            # 라디안 모드 (현재는 구현되지 않음)
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = EngineeringCalculator()
    calculator.show()
    sys.exit(app.exec_())