class Package:
    def __init__(self, package_id, name, duration_unit, duration_value, price, description):
        self.package_id     = package_id
        self.name           = name
        self.duration_unit  = duration_unit   # days | months
        self.duration_value = duration_value  # int
        self.price          = price           # float
        self.description    = description
