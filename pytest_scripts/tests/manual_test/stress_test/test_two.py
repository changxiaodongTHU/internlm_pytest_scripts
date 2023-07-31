import pytest
import time
import os
import sys
print(os.path.basename(sys.argv[0]))

class TestStressnn:
  
  @pytest.mark.cluster_env("kk_one")
  @pytest.mark.P3  
  def test_twostress_b(self):
    print("i am test_twostress_001")
    time.sleep(1.888)

  @pytest.mark.cluster_env("kk_one")
  @pytest.mark.P1 
  @pytest.mark.smoke
  def test_twostress_a(self):
    print("i am test_twostress_02")
    print(os.path.basename(sys.argv[0]))
    time.sleep(2.678)

  @pytest.mark.P0
  def test_twostress_d(self):
    print("i am test_twostress_00")
    time.sleep(2.0999)
    print(f"caseid is {prefix_id}")

  @pytest.mark.cluster_env("kk_two")
  def test_twostress_c(self):
    print("i am test_twostress_01")
    time.sleep(2.999)
   
