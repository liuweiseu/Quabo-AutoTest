import pytest
from QuaboAutoTest import *
from argparse import ArgumentParser

if __name__ == "__main__":
    # Step 0: parse the arguments
    parser = ArgumentParser(prog=os.path.basename(__file__))
    parser.add_argument('--ip-config', dest='ip_config', type=str, 
                        default='configs/quabo_ip.json',
                        help='IP config file. Default: configs/quabo_ip.json')
    parser.add_argument('-r', '--reboot', dest='reboot', action='store_true',
                        default=False,
                        help='reboot the Quabo.')
    opts = parser.parse_args()
    # Step 1: get the quabo ip
    quabo_ip = Util.read_json(opts.ip_config)
    if quabo_ip == None:
        print('quabo_ip.json is not found.')
        exit(1)
    # Step 2: ping the quabo first
    print('ping quabo: %s'%quabo_ip['ip'])
    status = Util.ping(quabo_ip['ip'])
    if status == False:
        print('Quabo is not reachable.')
        exit(1)
    # Step 3: get the flash uid
    quabo = tftpw(quabo_ip['ip'])
    uid = quabo.get_flashuid()
    if uid == None:
        print('Failed to get the flash uid.')
        exit(1)
    # Step 4: create a logger based on the uid
    logger = Util.create_logger('logs/Quabo-%s.log'%uid)
    logger.info('Start Quabo Auto Test')
    logger.info('UID: %s'%uid)
    logger.info('MAC: 00:%s:%s:%s:%s:%s', uid[10:12], uid[8:10], uid[6:8], uid[4:6], uid[2:4])
    # Step 5: Reboot the quabo
    # reboot the quabo
    if opts.reboot == False:
        print('Reboot is not required.')
    else:
        logger.info('Rebooting Quabo...')
        quabo.reboot()
        status = Util.ping(quabo_ip['ip'])
        if status == False:
            print('Quabo is not reachable.')
            exit(1)
        logger.info('Quabo Rebooted successfully')
    # Step 6: ping the quabo to make sure the quabo is rebooted
    print('ping quabo: %s'%quabo_ip['ip'])
    status = Util.ping(quabo_ip['ip'])
    if status == False:
        print('Quabo is not reachable.')
        exit(1)
    # Step 7: run the tests
    #pytest.main(["./test_scripts", "--html=reports/%s/reports.html"%uid, "-p no:logging", "-v"])
    pytest.main(["./test_scripts", "--html=reports/%s/reports.html"%uid, "-v"])