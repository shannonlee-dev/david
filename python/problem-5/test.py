class A:
    def a(self): print("A.a")

class B(A):
    def a(self):
        print("B.a before")
        super().a()           # A.a 호출
        print("B.a after")


a=B()

a.a()