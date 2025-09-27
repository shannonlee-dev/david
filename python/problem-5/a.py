import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt


class Calculator(QWidget):
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
                font-size: 48px;
                font-weight: 300;
                padding: 20px;
                border: none;
            }
        """)
        self.display.setFixedHeight(120)
        main_layout.addWidget(self.display)
        
        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        
        # 첫 번째 행: AC, +/-, %, ÷
        row1 = QHBoxLayout()
        self.create_button('AC', row1, 'gray', self.on_button_click)
        self.create_button('+/-', row1, 'gray', self.on_button_click)
        self.create_button('%', row1, 'gray', self.on_button_click)
        self.create_button('÷', row1, 'orange', self.on_button_click)
        button_layout.addLayout(row1)
        
        # 두 번째 행: 7, 8, 9, ×
        row2 = QHBoxLayout()
        self.create_button('7', row2, 'dark_gray', self.on_button_click)
        self.create_button('8', row2, 'dark_gray', self.on_button_click)
        self.create_button('9', row2, 'dark_gray', self.on_button_click)
        self.create_button('×', row2, 'orange', self.on_button_click)
        button_layout.addLayout(row2)
        
        # 세 번째 행: 4, 5, 6, -
        row3 = QHBoxLayout()
        self.create_button('4', row3, 'dark_gray', self.on_button_click)
        self.create_button('5', row3, 'dark_gray', self.on_button_click)
        self.create_button('6', row3, 'dark_gray', self.on_button_click)
        self.create_button('-', row3, 'orange', self.on_button_click)
        button_layout.addLayout(row3)
        
        # 네 번째 행: 1, 2, 3, +
        row4 = QHBoxLayout()
        self.create_button('1', row4, 'dark_gray', self.on_button_click)
        self.create_button('2', row4, 'dark_gray', self.on_button_click)
        self.create_button('3', row4, 'dark_gray', self.on_button_click)
        self.create_button('+', row4, 'orange', self.on_button_click)
        button_layout.addLayout(row4)
        
        # 다섯 번째 행: 0, ., =
        row5 = QHBoxLayout()
        # 0 버튼은 2배 넓이
        zero_button = QPushButton('0')
        zero_button.clicked.connect(lambda: self.on_button_click('0'))
        self.set_button_style(zero_button, 'dark_gray')
        zero_button.setFixedSize(180, 80)
        row5.addWidget(zero_button)
        
        self.create_button('.', row5, 'dark_gray', self.on_button_click)
        self.create_button('=', row5, 'orange', self.on_button_click)
        button_layout.addLayout(row5)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 윈도우 설정
        self.setWindowTitle('Calculator')
        self.setFixedSize(360, 640)
        self.setStyleSheet("QWidget { background-color: black; }")
    
    def create_button(self, text, layout, color, callback):
        button = QPushButton(text)
        button.clicked.connect(lambda: callback(text))
        self.set_button_style(button, color)
        button.setFixedSize(80, 80)
        layout.addWidget(button)
        return button
    
    def set_button_style(self, button, color):
        if color == 'gray':
            button.setStyleSheet("""
                QPushButton {
                    background-color: #A6A6A6;
                    color: black;
                    border: none;
                    border-radius: 40px;
                    font-size: 32px;
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
                    font-size: 32px;
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
                    border-radius: 40px;
                    font-size: 32px;
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
        elif text in ['+', '-', '×', '÷']:
            # 연산자 입력 (현재는 표시만)
            self.display.setText(current_text + ' ' + text + ' ')
        elif text == '=':
            # 계산 (현재는 구현되지 않음)
            pass
        elif text == '+/-':
            # 음수/양수 변환 (현재는 구현되지 않음)
            pass
        elif text == '%':
            # 퍼센트 (현재는 구현되지 않음)
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())