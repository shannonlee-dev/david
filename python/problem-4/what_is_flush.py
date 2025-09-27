import time

# 1) flush=False (기본): 어떤 환경에선 점들이 한꺼번에 몰아서 보일 수 있음
for _ in range(5):
    print(".", end="")  
    time.sleep(0.5)

# 2) flush=True: 점이 하나 찍힐 때마다 바로바로 보임
for _ in range(5):
    print(".", end="", flush=True)
    time.sleep(0.5)

