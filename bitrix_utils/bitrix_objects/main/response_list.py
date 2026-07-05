
class ResponseList(list):
    # класс для написания доп методова
    # TODO хорошо бы классу знать о типе обьекта

    # def __init__(self, instance, object_type=None):
    #     self.object_type = object_type
    #     super(ResponseList, self).__init__(instance)

    def to_ids_list(self):
        # Превратить список объектов в список id
        return [int(x['ID']) for x in self]

    def __getitem__(self, item):
        # чтобы работало slice qq = q[0:10]
        return ResponseList(super().__getitem__(item))

    def to_objects(self, object_type):
        return [object_type(x) for x in self.to_ids_list()]
