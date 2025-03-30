from QuaboAutoTest import *
import pytest

autotest = QuaboTest('configs/quabo_ip.json')

@pytest.mark.all
@pytest.mark.hk
def test_hk_vals():
    """
    Description: 
        Check the HK values
    """
    result = autotest.CheckHKPktVals()  
    assert result == True

@pytest.mark.all
@pytest.mark.hk
def test_hk_timestamp():
    """"
    Description: 
        Check the HK timestamp"
    """
    result = autotest.CheckHKTimestamp()  
    assert result == True

@pytest.mark.all
@pytest.mark.maroc
def test_maroc_config():
    """"
    Description: 
        Check the MAROC config
    """
    result = autotest.CheckMarocConfig()  
    assert result == True

@pytest.mark.all
@pytest.mark.mac
def test_destination_mac():
    """"
    Description: 
        Check the destination MAC address
    """
    result = autotest.CheckDestMac()  
    assert result == True


