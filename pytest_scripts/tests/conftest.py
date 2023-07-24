import json


def pytest_addoption(parser):
    '''
    parser the input.
    '''
    parser.addoption("--test_json_file",
                     help="test json file path",
                     default="")
    parser.addoption("--case_name",
                     help="select a model to run, default to run all model",
                     default="ALL")


def pytest_generate_tests(metafunc):
    '''
    process the test case and enter the main test program
    '''

    test_json_path = metafunc.config.getoption("test_json_file")
    case_name = metafunc.config.getoption("case_name")
    testcase_dict = dict()
    with open(test_json_path) as f:
        testcase_configs = json.load(f)

        if case_name == "" or case_name.lower() == "all":
            case_name = testcase_configs.keys()
        else:
            case_name = [item.strip()
                          for item in metafunc.config.getoption("case_name").split(",")]

        for cur_key in case_name:
            if cur_key not in testcase_configs:
                testcase_dict[cur_key] = ["echo {} not in cases/*.json && exit -1".format(cur_key)]
                continue

            for idx, testcase in enumerate(testcase_configs[cur_key]["testcases"]):
                testcase_dict["{}: {}".format(cur_key, testcase)] = [
                    "pushd {}".format(testcase_configs[cur_key]["directory"]),
                    "if [ -f requirements.txt ]; then pip install -r requirements.txt ; fi",
                    testcase,
                    "popd"
                ]

    metafunc.parametrize("testcase",
                         list(testcase_dict.values()),
                         ids=list(testcase_dict.keys()))
