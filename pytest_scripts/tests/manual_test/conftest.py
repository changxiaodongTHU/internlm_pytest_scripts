import logging
import os
import time
import pathlib

import pytest

import uniscale
#from tests.common.cluster import UniscaleCluster

from framework.db_operator.uploader import Uploader

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG,
                    filename='test.log',
                    filemode='a')
global prefix_id

prefix_id=str(int(time.time()*1000))

@pytest.hookimpl(hookwrapper=True, tryfirst=True)

def pytest_runtest_makereport(item, call):
    uploader = Uploader()
    uploader.set_db('uniscale_tmpk')
    uploader.set_collection("uniscale_case_result_tmpk")
    out = yield
    res = out.get_result()
    caseid = item.name + "_" + prefix_id
    if res.when == "setup":
       set_up_result={}
       set_up_result={"caseid":caseid,"nodeid":res.nodeid,"result":res.outcome,"stage":res.when,"detail":str(res.longrepr),"duration":res.duration}
       result=set_up_result
       print(f"set up result is :\n{result}")
       uploader.upload(result)

    if res.when == "call" :
       call_result={}
       call_result={"caseid":caseid,"nodeid":res.nodeid,"result":res.outcome,"stage":res.when,"detail":str(res.longrepr),"duration":res.duration}
       result=call_result
       print(f"call阶段更新数据,a is:\n {result}")
       uploader.update({"caseid":caseid}, {"result":res.outcome,"stage":res.when,"detail":str(res.longrepr),"duration":res.duration})
    
    uploader.close_client()

def pytest_terminal_summary(terminalreporter, exitstatus, config):  # pylint: disable=W0613
    """
    collect test results, identify error and failed tests
    """
    path = pathlib.Path().resolve()
    testresult_path = os.path.join(path, "pytest.out")
    pass_len = len(terminalreporter.stats.get("passed", []))
    errors = terminalreporter.stats.get("error", [])
    faileds = terminalreporter.stats.get("failed", [])
    failed_len = len(errors)
    err_len = len(faileds)

    with open(testresult_path, "w", encoding="utf-8") as f:
        f.write(f"number of pass tests: {pass_len}\n")
        f.write(f"number of error tests: {err_len}\n")
        f.write(f"number of failed tests: {failed_len}\n")
        if err_len > 0:
            for error in errors:
                f.write(error.caplog + "\n")
        if failed_len > 0:
            for failed in faileds:
                f.write(failed.caplog + "\n")


@pytest.fixture(scope="module")
def default_cluster(request):
    cluster_info = None
    confile = "./tests/cases/env_default.yaml"
    try:
        ins = UniscaleCluster(confile)
        cluster_info = ins.install()
        uniscale.init(server_address=cluster_info["head_node_addr"] + ":10001")
    except Exception as e:  # pylint: disable=W0703
        ins.uninstall()
        pytest.exit(f"{e},Uniscale install failed ...")

    def fin():
        if ins:
            uniscale.shutdown()
            ins.uninstall()

    request.addfinalizer(fin)
    return cluster_info


@pytest.fixture
def env(request):
    marker = request.node.get_closest_marker("custom_cluster")
    cluster_info = None
    if marker is not None and len(marker.args):
        confile_path = marker.args[0]
        ins = UniscaleCluster(confile_path)
        cluster_info = ins.install()
        uniscale.init(server_address=cluster_info["head_node_addr"] + ":10001")

        def fin():
            if cluster_info:
                uniscale.shutdown()
                ins.uninstall()

        request.addfinalizer(fin)
    return cluster_info


@pytest.fixture(scope="module")
def standalone(request):
    cluster_info = None
    confile = None
    try:
        ins = UniscaleCluster(confile)
        cluster_info = ins.install()
        uniscale.init()
    except Exception as e:  # pylint: disable=W0703
        print(e)
        # TODO:add logger.error
        pytest.exit("Uniscale install failed ...")

    def fin():
        if ins:
            uniscale.shutdown()
            ins.uninstall()

    request.addfinalizer(fin)
    return cluster_info
