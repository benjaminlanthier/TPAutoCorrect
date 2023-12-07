import json

import numpy as np


class Report:
    VALUE_KEY = "value"
    WEIGHT_KEY = "weight"
    
    def __init__(self, data: dict = None, report_filepath: str = None, *args, **kwargs):
        self.data = data
        self.report_filepath = report_filepath
        self.args = args
        self.kwargs = kwargs
        
        self._initialize_data_()
    
    @property
    def grade(self) -> float:
        return self.get_grade()
    
    @property
    def is_normalized(self) -> bool:
        return np.isclose(sum([self.get_weight(k) for k in self.keys()]), 1.0)
    
    def _initialize_data_(self):
        if self.data is None:
            self.data = {}
    
    def get_state(self) -> dict:
        return {
            "grade"          : self.grade,
            "data"           : self.data,
            "report_filepath": self.report_filepath,
            "args"           : self.args,
            "kwargs"         : self.kwargs,
        }
    
    def set_state(self, state: dict):
        self.data = state["data"]
        self.report_filepath = state["report_filepath"]
        self.args = state["args"]
        self.kwargs = state["kwargs"]
    
    def add(self, key, value, weight=1.0):
        self.data[key] = {self.VALUE_KEY: value, self.WEIGHT_KEY: weight}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def get_value(self, key, default=None):
        value = self.get(key, default)
        if value is None:
            return value
        return value[self.VALUE_KEY]
    
    def get_weight(self, key, default=None):
        value = self.get(key, default)
        if value is None:
            return value
        return value[self.WEIGHT_KEY]
    
    def get_weighted(self, key, default=None):
        value = self.get_value(key, default)
        weight = self.get_weight(key, default)
        if value is None or weight is None:
            return None
        return value * weight
    
    def get_item(self, key, default=None):
        return key, self.get(key, default)
    
    def keys(self):
        return self.data.keys()
    
    def __getitem__(self, item):
        return self.data[item]
    
    def __setitem__(self, key, value, weight=1.0):
        if isinstance(value, tuple):
            assert len(value) == 2, "value must be a tuple of length 2"
            self.data[key] = value
        else:
            self.data[key] = (value, weight)
    
    def normalize_weights_(self) -> "Report":
        total_weight = sum([self.get_weight(k) for k in self.keys()])
        for k in self.keys():
            self.data[k][self.WEIGHT_KEY] = self.get_weight(k) / total_weight
        return self
    
    def get_normalized(self) -> "Report":
        total_weight = sum([self.get_weight(k) for k in self.keys()])
        return Report(
            {
                k: {self.VALUE_KEY: self.get_value(k), self.WEIGHT_KEY: self.get_weight(k) / total_weight}
                for k in self.keys()
            }
        )
    
    def get_grade(self) -> float:
        if self.is_normalized:
            report = self
        else:
            report = self.get_normalized()
        grade = sum([report.get_weighted(k) for k in report.keys()])
        return grade
    
    def save(self, report_filepath: str = None):
        if report_filepath is not None:
            self.report_filepath = report_filepath
        assert self.report_filepath is not None, "report_filepath must be initialized before saving"
        with open(self.report_filepath, "w") as f:
            json.dump(self.get_state(), f, indent=4)
        return self.report_filepath
    
    def load(self, report_filepath: str = None):
        if report_filepath is not None:
            self.report_filepath = report_filepath
        assert self.report_filepath is not None, "report_filepath must be initialized before loading"
        with open(self.report_filepath, "r") as f:
            self.set_state(json.load(f))
        return self
    
    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"grade={self.grade}, "
                f"data={self.data}, "
                f"report_filepath={self.report_filepath}"
                f")")
    
    def __str__(self):
        json_str = json.dumps(self.get_state(), indent=4)
        return f"{self.__class__.__name__}({json_str})"
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)
    
    def __contains__(self, item):
        return item in self.data
