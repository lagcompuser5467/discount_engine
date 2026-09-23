class ConfigProvider:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.discounts = []

        return cls._instance

    def set_discounts(self, discounts):
        self.discounts = discounts

    def get_discounts(self):
        return self.discounts