from QuaboAutoTest import *
import pytest

autotest_config = Util.read_json('configs/autotest_config.json')
connector = autotest_config['SiPMsimulator']
boardrev = autotest_config['BoardRev']
autotest = SiPMSimTest(boardrev, connector, 'configs/quabo_ip.json')

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
@pytest.mark.ph_peaks
def test_ph_peaks():
    """"
    Description: 
        Check how many PH peaks are in the ph data.
    """
    result = autotest.CheckPHPeaks()  
    assert result == True

@pytest.mark.all
@pytest.mark.ph
@pytest.mark.ph_data
def test_ph_data():
    """"
    Description: 
        Check the PH data"
    """
    result = autotest.CheckPHdata()  
    assert result == True

@pytest.mark.all
@pytest.mark.ph
@pytest.mark.ph_timing
def test_ph_data_timestamp():
    """"
    Description: 
        Check the PH data timestamp
    """
    result = autotest.CheckPHTimestamp()  
    assert result == True

@pytest.mark.all
@pytest.mark.ph
@pytest.mark.ph_pattern
def test_ph_pattern():
    """"
    Description: 
        Check the PH pattern
    """
    result = autotest.CheckPHPattern()  
    assert result == True