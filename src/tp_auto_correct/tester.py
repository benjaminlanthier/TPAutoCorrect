import json
from copy import deepcopy
import pytest
import pytest_cov
import pytest_jsonreport
from pytest_jsonreport.plugin import JSONReport
from pytest_cov.plugin import CovPlugin
import os
import sys
import shutil
from .source import Source, SourceCode, SourceTests
from .report import Report
from .utils import find_filepath, rm_pycache, rm_pyc_files


class Tester:
    def __init__(
            self,
            code_src: SourceCode,
            tests_src: SourceTests,
            master_tests_src: SourceTests = None,
            *args,
            **kwargs
    ):
        self.code_src = code_src
        self.tests_src = tests_src
        self.master_tests_src = master_tests_src
        self.args = args
        self.kwargs = kwargs
        
        self.json_plugin = JSONReport()
        self.test_cases_summary = None
        self.master_test_cases_summary = None
        self.report_dir = os.path.join(os.getcwd(), "report_dir")
        self.report_filepath = os.path.join(self.report_dir, "report.json")
        self.report = Report(report_filepath=self.report_filepath)

    def run(self, *args, **kwargs):
        overwrite = kwargs.get("overwrite", True)
        debug = kwargs.get("debug", False)
        self.code_src.setup_at(
            self.report_dir,
            overwrite=overwrite,
            debug=debug
        )
        self.tests_src.setup_at(
            self.report_dir,
            overwrite=overwrite,
            debug=debug
        )
        if self.master_tests_src is not None:
            self.master_tests_src.setup_at(
                self.report_dir,
                overwrite=overwrite,
                debug=debug
            )
        self._run()
        if kwargs.get("save_report", True):
            self.report.save(self.report_filepath)
    
    def _run(self):
        self._run_pytest()
        self.report.add("code_coverage", self.get_code_coverage())
        self.test_cases_summary = deepcopy(self.get_test_cases_summary())
        self.report.add("percent_passed", self.test_cases_summary["percent_passed"])
        
        if self.master_tests_src is not None:
            self.master_tests_src.rename_test_files(pattern="{}_master.py")
            self._run_master_pytest()
            self.master_test_cases_summary = deepcopy(self.get_test_cases_summary())
            self.report.add("master_percent_passed", self.master_test_cases_summary["percent_passed"])
        
        self.clear_pycache()
    
    def _run_pytest(self):
        pytest.main(
            [
                self.tests_src.local_path,
                f"--cov={self.code_src.local_path}",
                "--cov-report=json",
                "-p no:cacheprovider",
            ],
            plugins=[
                self.json_plugin,
            ]
        )
        self.clear_pycache()
    
    def _run_master_pytest(self):
        if self.master_tests_src is None:
            return
        pytest.main(
            [
                self.master_tests_src.local_path,
                f"--cov={self.code_src.local_path}",
                "--cov-report=json",
                "-p no:cacheprovider",
            ],
            plugins=[
                self.json_plugin,
            ]
        )
        self.clear_pycache()
    
    def get_code_coverage(self) -> float:
        r"""
        Use pytest-cov to get code coverage of the code source using the tests source.
        
        :return: code coverage
        :rtype: float
        """
        coverage_file = find_filepath("coverage.json")
        coverage_data = json.load(open(coverage_file))
        json.dump(coverage_data, open(coverage_file, "w"), indent=4)
        summaries = [d["summary"] for f, d in coverage_data["files"].items() if f.endswith(".py")]
        mean_percent_covered = sum([s["percent_covered"] for s in summaries]) / len(summaries)
        return mean_percent_covered
    
    def get_test_cases_summary(self):
        passed_tests = self.json_plugin.report["summary"].get("passed", 0)
        failed_tests = self.json_plugin.report["summary"].get("failed", 0)
        total_tests = self.json_plugin.report["summary"]["total"]
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
            "percent_passed": percent_passed,
            "percent_failed": percent_failed,
        }
    
    def clear_pycache(self):
        rm_pycache(self.report_dir)
        rm_pyc_files(self.report_dir)
