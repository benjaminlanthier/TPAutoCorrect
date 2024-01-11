import argparse
import sys

from . import (
    SourceCode,
    SourceTests,
    SourceMasterCode,
    SourceMasterTests,
    Tester,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--code-src-path",
        type=str,
        default=None,
        help="Path to the directory containing the code to be tested.",
    )
    parser.add_argument(
        "--tests-src-path",
        type=str,
        default=None,
        help="Path to the directory containing the tests for the code to be tested.",
    )
    parser.add_argument(
        "--master-code-src-path",
        type=str,
        default=None,
        help="Path to the directory containing the master code to be tested.",
    )
    parser.add_argument(
        "--master-tests-src-path",
        type=str,
        default=None,
        help="Path to the directory containing the master tests for the code to be tested.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default=None,
        help="Path to the directory to save the report.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug messages.",
    )
    parser.add_argument(
        "--push_report_to",
        type=str,
        default=None,
        help="Push report file to a git repository. "
             "If equal to 'auto' the repository of the current project will be used if found.",
    )
    parser.add_argument(
        "--clear-pytest-temporary-files",
        action="store_true",
        help="Clear pytest temporary files.",
    )
    for key, default_weight in Tester.DEFAULT_WEIGHTS.items():
        parser.add_argument(
            f"--{key}-weight",
            type=float,
            default=default_weight,
            help=f"Weight of the {key} test in the final score.",
        )
    parser.add_argument(
        "--rm-report-dir",
        action="store_true",
        help="Remove the report directory. "
             "This option is useful when the report file is pushed to a git repository"
             " and the report directory is no longer needed.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    code_source = SourceCode(src_path=args.code_src_path)
    test_source = SourceTests(src_path=args.tests_src_path)
    logging_func = print if args.debug else Tester.DEFAULT_LOGGING_FUNC
    if args.master_code_src_path is None:
        master_code_source = None
    else:
        master_code_source = SourceMasterCode(src_path=args.master_code_src_path)
    if args.master_tests_src_path is None:
        master_tests_source = None
    else:
        master_tests_source = SourceMasterTests(src_path=args.master_tests_src_path)
    weights = Tester.DEFAULT_WEIGHTS.copy()
    weights.update({
        key: getattr(args, f"{key}_weight", default_weight)
        for key, default_weight in Tester.DEFAULT_WEIGHTS.items()
    })
    tester = Tester(
        code_source, test_source,
        master_code_src=master_code_source,
        master_tests_src=master_tests_source,
        report_dir=args.report_dir,
        logging_func=logging_func,
        weights=weights,
    )
    tester.run(
        overwrite=args.overwrite,
        debug=args.debug,
        clear_pytest_temporary_files=args.clear_pytest_temporary_files
    )
    if args.push_report_to is not None:
        tester.push_report_to(args.push_report_to)
    if args.rm_report_dir:
        tester.rm_report_dir()


if __name__ == '__main__':
    # Example of command:
    # python -m tac --code-src-path="Example/SimpleTP/src" --tests-src-path="Example/SimpleTP/tests" --debug --overwrite
    sys.exit(main())
