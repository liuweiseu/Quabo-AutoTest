from QuaboAutoTest import *
import json

autotest = QuaboTest('configs/quabo_ip.json')

def test_hk_vals():
    """
    Description: 
        Check the HK values
    """
    result = autotest.CheckHKPktVals()  
    assert result == True

def test_hk_timestamp():
    """"
    Description: 
        Check the HK timestamp"
    """
    result = autotest.CheckHKTimestamp()  
    assert result == True

def test_maroc_config():
    """"
    Description: 
        Check the MAROC config
    """
    result = autotest.CheckMarocConfig()  
    assert result == True

def test_destination_mac():
    """"
    Description: 
        Check the destination MAC address
    """
    result = autotest.CheckDestMac()  
    assert result == True

def test_ph_data():
    """"
    Description: 
        Check the PH data"
    """
    result = autotest.CheckPHdata()  
    assert result == True

def test_ph_data_timestamp():
    """"
    Description: 
        Check the PH data timestamp
    """
    result = autotest.CheckPHTimestamp()  
    assert result == True