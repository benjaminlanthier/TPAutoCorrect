import sys
import os
try:
    import tp_auto_correct as tac
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    import tp_auto_correct as tac


def auto_correct():
    code_source = tac.SourceCode(os.path.join(os.path.dirname(__file__), "src"))
    print(code_source)
    tests_source = tac.SourceTests(os.path.join(os.path.dirname(__file__), "tests"))
    print(tests_source)
    master_tests_source = tac.SourceTests(os.path.join(os.path.dirname(__file__), "master_tests"))
    print(master_tests_source)
    auto_corrector = tac.Tester(code_source, tests_source, master_tests_src=master_tests_source)
    auto_corrector.run(overwrite=True, debug=True)
    print(auto_corrector.report)


def auto_correct_from_git():
    path_to_example = os.path.join(".", "Example")
    repo_url = "https://github.com/JeremieGince/TPAutoCorrect.git"
    code_source = tac.SourceCode(os.path.join(path_to_example, "src"), url=repo_url)
    print(code_source)
    code_source.setup_at("./temp")
    print(code_source)
    # tests_source = tac.SourceTests(os.path.join(path_to_example, "tests"), url=repo_url)
    # print(tests_source)
    # master_tests_source = tac.SourceTests(os.path.join(path_to_example, "master_tests"), url=repo_url)
    # print(master_tests_source)
    # auto_corrector = tac.Tester(code_source, tests_source, master_tests_src=master_tests_source)
    # auto_corrector.run(overwrite=True, debug=True)
    # print(auto_corrector.report)


if __name__ == "__main__":
    # auto_correct()
    auto_correct_from_git()

