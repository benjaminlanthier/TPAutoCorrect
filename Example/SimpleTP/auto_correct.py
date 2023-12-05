import sys
import os
try:
    import tp_auto_correct as tac
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
    import tp_auto_correct as tac


def auto_correct():
    code_source = tac.SourceCode(os.path.join(os.path.dirname(__file__), "src"))
    print(code_source)
    code_source.setup_at(os.path.join(os.path.dirname(__file__), "temp"), overwrite=True)
    print(code_source)
    tests_source = tac.SourceTests(os.path.join(os.path.dirname(__file__), "tests"))
    print(tests_source)
    tests_source.setup_at(os.path.join(os.path.dirname(__file__), "temp"), overwrite=True)
    print(tests_source)
    # auto_corrector = tac.AutoCorrector(code_source, tests_source)
    # auto_corrector.run()


if __name__ == "__main__":
    auto_correct()

