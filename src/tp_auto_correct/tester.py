import json
from copy import deepcopy
from typing import Optional

import pytest
import pytest_cov
import pytest_jsonreport
from pytest_jsonreport.plugin import JSONReport
from pytest_cov.plugin import CovPlugin
import os
import sys
import shutil

from . import utils
from .source import Source, SourceCode, SourceTests
from .report import Report
from .utils import find_filepath, rm_pycache, rm_pyc_files
from .perf_test_case import PEP8TestCase


class Tester:
    CODE_COVERAGE_KEY = "code_coverage"
    PERCENT_PASSED_KEY = "percent_passed"
    MASTER_PERCENT_PASSED_KEY = "master_percent_passed"
    PEP8_KEY = "PEP8"
    DEFAULT_WEIGHTS = {
        CODE_COVERAGE_KEY        : 1.0,
        PERCENT_PASSED_KEY       : 1.0,
        MASTER_PERCENT_PASSED_KEY: 1.0,
        PEP8_KEY                 : 1.0,
    }
    MASTER_TESTS_RENAME_PATTERN = "{}_master.py"
    DOT_JSON_REPORT_NAME = ".report.json"
    
    def __init__(
            self,
            code_src: Optional[SourceCode] = SourceCode(),
            tests_src: Optional[SourceTests] = SourceTests(),
            master_tests_src: SourceTests = None,
            *args,
            **kwargs
    ):
        self.code_src = code_src
        self.tests_src = tests_src
        self.master_tests_src = master_tests_src
        self.args = args
        self.kwargs = kwargs
        
        self.test_cases_summary = None
        self.master_test_cases_summary = None
        self.report_dir = self.kwargs.get("report_dir", os.path.join(os.getcwd(), "report_dir"))
        self.report_filepath = self.kwargs.get("report_filepath", os.path.join(self.report_dir, "report.json"))
        self.report = Report(report_filepath=self.report_filepath)
        self.weights = self.kwargs.get("weights", self.DEFAULT_WEIGHTS)
    
    @property
    def dot_coverage_path(self):
        return find_filepath(".coverage")
    
    @property
    def coverage_json_path(self):
        return find_filepath("coverage.json")
    
    @property
    def coverage_xml_path(self):
        return find_filepath("coverage.xml")
    
    @property
    def dot_report_json_path(self):
        return find_filepath(self.DOT_JSON_REPORT_NAME)
    
    @property
    def pytest_plugins_options(self):
        return [
            f"--cov={self.code_src.local_path}",
            "--cov-report=json",
            "-p no:cacheprovider",
            "--json-report",
            f"--json-report-file={self.DOT_JSON_REPORT_NAME}",
            f"--json-report-summary",
            f"--json-report-indent=4",
        ]

    def run(self, *args, **kwargs):
        self.weights.update(kwargs.pop("weights", {}))
        save_report = kwargs.pop("save_report", True)
        clear_pytest_temporary_files = kwargs.pop("clear_pytest_temporary_files", True)
        clear_temporary_files = kwargs.pop("clear_temporary_files", False)
        self.code_src.setup_at(self.report_dir, **kwargs)
        self.tests_src.setup_at(self.report_dir, **kwargs)
        if self.master_tests_src is not None:
            self.master_tests_src.setup_at(self.report_dir, **kwargs)
        self._run()
        if save_report:
            self.report.save(self.report_filepath)
        if clear_pytest_temporary_files:
            self.clear_pytest_temporary_files()
        if clear_temporary_files:
            self.clear_temporary_files()
    
    def _run(self):
        self.clear_pycache()
        self._run_pytest()
        self.report.add(
            self.CODE_COVERAGE_KEY,
            self.get_code_coverage(),
            weight=self.weights[self.CODE_COVERAGE_KEY],
        )
        self.test_cases_summary = deepcopy(self.get_test_cases_summary())
        self.report.add(
            self.PERCENT_PASSED_KEY,
            self.test_cases_summary[self.PERCENT_PASSED_KEY],
            weight=self.weights[self.PERCENT_PASSED_KEY],
        )
        self.report.add(
            self.PEP8_KEY,
            self.get_pep8_score(),
            weight=self.weights[self.PEP8_KEY],
        )
        
        if self.master_tests_src is not None:
            self.master_tests_src.rename_test_files(pattern=self.MASTER_TESTS_RENAME_PATTERN)
            self._run_master_pytest()
            self.master_test_cases_summary = deepcopy(self.get_test_cases_summary())
            self.report.add(
                self.MASTER_PERCENT_PASSED_KEY,
                self.master_test_cases_summary[self.PERCENT_PASSED_KEY],
                weight=self.weights[self.MASTER_PERCENT_PASSED_KEY],
            )
        
        self.clear_pycache()
    
    def _run_pytest(self):
        os.system(f"pytest {self.tests_src.local_path} {' '.join(self.pytest_plugins_options)}")
        self.clear_pycache()
    
    def _run_master_pytest(self):
        if self.master_tests_src is None:
            return
        os.system(f"pytest {self.master_tests_src.local_path} {' '.join(self.pytest_plugins_options)}")
        self.clear_pycache()
    
    def get_code_coverage(self) -> float:
        r"""
        Use pytest-cov to get code coverage of the code source using the tests source.
        
        :return: code coverage
        :rtype: float
        """
        coverage_file = self.coverage_json_path
        coverage_data = json.load(open(coverage_file))
        json.dump(coverage_data, open(coverage_file, "w"), indent=4)
        summaries = [d["summary"] for f, d in coverage_data["files"].items() if f.endswith(".py")]
        mean_percent_covered = sum([s["percent_covered"] for s in summaries]) / len(summaries)
        return mean_percent_covered
    
    def get_test_cases_summary(self):
        json_plugin_report_data = json.load(open(self.dot_report_json_path))
        passed_tests = json_plugin_report_data["summary"].get("passed", 0)
        failed_tests = json_plugin_report_data["summary"].get("failed", 0)
        total_tests = json_plugin_report_data["summary"]["total"]
        if total_tests > 0:
            ratio_passed = passed_tests / total_tests
            ratio_failed = failed_tests / total_tests
        else:
            ratio_passed = 1.0
            ratio_failed = 1.0
        percent_passed = 100 * ratio_passed
        percent_failed = 100 * ratio_failed
        return {
            "passed": passed_tests,
            "failed": failed_tests,
            "total": total_tests,
            "ratio_passed": ratio_passed,
            "ratio_failed": ratio_failed,
            self.PERCENT_PASSED_KEY: percent_passed,
            "percent_failed": percent_failed,
        }
    
    def get_pep8_score(self):
        src_test_case = PEP8TestCase(self.PEP8_KEY, self.code_src.local_path)
        src_test_case_result = src_test_case.run()
        tests_test_case = PEP8TestCase(self.PEP8_KEY, self.tests_src.local_path)
        tests_test_case_result = tests_test_case.run()
        return (src_test_case_result.percent_value + tests_test_case_result.percent_value) / 2.0
    
    def clear_pycache(self):
        rm_pycache(self.report_dir)
        rm_pyc_files(self.report_dir)
        
    def clear_pytest_temporary_files(self):
        self.clear_pycache()
        tmp_files = [
            self.dot_coverage_path,
            self.coverage_json_path,
            self.coverage_xml_path,
            self.dot_report_json_path,
        ]
        for f in tmp_files:
            utils.rm_file(f)
    
    def clear_temporary_files(self):
        self.clear_pytest_temporary_files()
        sources = [self.code_src, self.tests_src, self.master_tests_src]
        for src in sources:
            if src is not None:
                src.clear_temporary_files()
