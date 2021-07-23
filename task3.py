class A():
    


    def met_a(self):
        print(type(self), self.__dict__)

    @classmethod
    def met_b(self):
        print(type(self), self.__dict__)

class B(A):
    def met_a(self):
        print(type(self), self.__dict__)

a = A()

a.met_a()
a.met_b()

b = B()

b.met_a()
b.met_b()