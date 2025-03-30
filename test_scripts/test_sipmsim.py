from QuaboAutoTest import *
import pytest

autotest_config = Util.read_json('configs/autotest_config.json')
autotest = SiPMSimTest(autotest_config['SiPMsimulator'], 'configs/quabo_ip.json')

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