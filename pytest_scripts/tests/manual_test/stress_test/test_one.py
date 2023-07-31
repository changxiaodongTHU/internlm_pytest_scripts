import pytest
import time
import os
import sys
import requests
import logging
print(os.path.basename(sys.argv[0]))



def setup_module(self):
    print("begin check failure envionment health")
    url = "http://10.140.0.73:31767/api/system/health"
    result = requests.get(url,timeout=3)
    print("#####")
    print(result.status_code)
    # assert result.json().["status"]==0
    print(result.json())
    print("########")

def teardown_module(self):
    print("end")


class TestStress:
 

  def setup_class(self):
      print(f"{kkk}") 


  def teardown_class(self):
      print("pass")

  @pytest.mark.skip()
  @pytest.mark.cluster_env("kk_one") 
  @pytest.mark.P1 
  def test_stress_b(self):
    print("i am test_stress_001")
    logging.info("waiting")
    time.sleep(1)

  @pytest.mark.P0 
  def test_stress_a(self):
    print("i am test_stress_02")
    time.sleep(2)

  @pytest.mark.cluster_env("kk_two")
  @pytest.mark.P2
  def test_stress_d(self):
    print("i am test_stress_00")
    time.sleep(100)

  @pytest.mark.cluster_env("kk_one") 
  @pytest.mark.P1
  def test_stress_c(self):
    print("i am test_stress_01")
    time.sleep(2)
   
