from QuaboAutoTest import *
import json

quabo_ip = Util.read_json('configs/quabo_ip.json')
quabo = tftpw(quabo_ip['ip'])
uid = quabo.get_flashuid()
autotest = QuaboTest(uid)

def test_hk():
    # get quabo ip
    quabo_ip = Util.read_json('configs/quabo_ip.json')
    # configure quabo, setting HV
    qc = QuaboConfig(quabo_ip['ip'])
    qc.SetHkPacketDest()
    mac = qc.SetDataPktDest()
    qc.SetHv('on')
    qc.close()
    # get hk packets
    hk = HKRecv(quabo_ip['ip'])
    expected_results = Util.read_json('configs/expected_results.json')
    e_hk = expected_results['hk']
    # get the hk packets
    d, t = hk.RecvData()
    hkpkt = hk.ParseData(d, t)
    hk.close()
    # check the hk packets
    result = autotest.CheckResults(e_hk, hkpkt)
    assert result == True