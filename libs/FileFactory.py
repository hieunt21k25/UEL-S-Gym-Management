import json
import os


class JsonFileFactory:
    def write_data(self, arr_data, filename):
        """
        Parse a list of objects into a JSON string and save to file.
        :param arr_data: list of model objects
        :param filename: path to save the JSON file
        :return: True on success
        """
        json_string = json.dumps(
            [item.__dict__ for item in arr_data],
            default=str, indent=4, ensure_ascii=False
        )
        json_file = open(filename, 'w', encoding='utf-8')
        json_file.write(json_string)
        json_file.close()
        return True

    def read_data(self, filename, ClassName):
        """
        Read a JSON file and restore it as a list of ClassName instances.
        :param filename: path to the JSON file
        :param ClassName: model class to reconstruct
        :return: list of ClassName objects, or [] if file not found
        """
        if os.path.isfile(filename) == False:
            return []
        file = open(filename, 'r', encoding='utf-8')
        arr_data = json.loads(file.read(), object_hook=lambda cls: ClassName(**cls))
        file.close()
        return arr_data
