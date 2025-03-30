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

@pytest.mark.all
@pytest.mark.ph
def test_ph_peaks():
    """"
    Description: 
        Check how many PH peaks are in the ph data.
    """
    result = autotest.CheckPHPeaks()  
    assert result == True

@pytest.mark.all
@pytest.mark.ph
def test_ph_data():
    """"
    Description: 
        Check the PH data"
    """
    result = autotest.CheckPHdata()  
    assert result == True

@pytest.mark.all
@pytest.mark.ph
def test_ph_data_timestamp():
    """"
    Description: 
        Check the PH data timestamp
    """
    result = autotest.CheckPHTimestamp()  
    assert result == True