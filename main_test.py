class Testing:
    def __init__(self):
        self.att = True
        self.name = "This is a Testing class!"

    def __str__(self):
        return self.name


testing = Testing()
print(testing)