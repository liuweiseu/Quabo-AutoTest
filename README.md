# QuaboAutoTest
This software is used for testing new Quabos automatically, which is based on pytest.  
Here are the tests we do in this software:  
1. Housekeeping test  
    (a) `hk_vals`: check all of the values in the HK packets, including high voltage, FPGA voltage, IP address and so on;  
    (b) `hk_time`: check the HK packets interval time.  
2. MAROC chip config  
    (a) `maroc`: check the MAROC chip configuration by writing/reading back the values to/from all of the registers.  
3. MAC address  
    (a) `mac`: check if the Microblaze core gets the correct MAC address for PH and MOVIE packets.  
4. White Rabbit Timing/Movie mode  
    (a) `wr_timing`: check the timestamps in the MOVIE packets to see if White Rabbit works or not, which includes the max timestamps and the timestamps difference.
5. PH mode(**SiPM simulator board is required**)  
    (a) `ph_data`: check the mean/std/max/min of the pulse height;  
    (b) `ph_timing`: check the interval time for the PH packets, which is related to SiPM simulator board setting;  
    (c) `ph_peaks`: check how many pulses are in each PH packet;  
    (d) `ph_pattern`: check the pulse pattern in PH events.

# Get Start
## Environment Setup
1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)(optional)  
Miniconda is recommended to create a vritual python environment, so that it won't mess up the python environment on your system.  
If miniconda is installed, please create and activate the python environment.
    ```
    conda create -n quabo python=3.12
    conda activate quabo
    ``` 
2. Install required packages
    ```
    pip install -r requirements.txt
    ```
## Config files
There are several config files in `configs`:
1. `autotest_config.json`  
    (a) `BoardRev`: this defines which version of board you're testing.  
    (b) `SiPMsimulator`: this shows the SiPM simulator is attached to which connector.  
    (c) `NPhPkt`: this defines the received pkt number for the PH event test.  
    (d) `NPhPeaks`: this defines the received pkt number for the PH peaks test.  
    (e) `PHThreshold`: this defines the threshold for the PH peaks test.  
    (f) `NMoviePkt`: this defines the received pkt number for the MOVINE mode/WR timing test.  
    (g) `IntegrationTime`: this defines the integration time for the MOVINE mode/WR timing test.
2. `expected_results.json`  
    This file defines the expected test results.  
    Here is an example of `hk_interval`:
    ```
    "hk_interval": {
        "val": 2.5,
        "deviation": 0.5,
        "valid": true
    }
    ```
    `val` means the expected interval time is 2.5s, `deviation` means the calculated result's deviation is +-0.5s, `valid` is `true` means we will check hk_interval when we run the test scripts.
3. `quabo_ip.json`  
    We set the IP address of the Quabo in this file.  
    **Note: Normally, users don't need to modify this file, unless the IP setting jumper on Mini-Mobo is changed.**  
4. `quabo_config.json`  
    We set the default configurations for the Quabo in this file, including the MAROC chip configuration, MASK configuration, ACQ configuration, HV configuration and HK/PH/MOVIE packet's Destination IP address.  
    **Note: Normally, users don't need to modify this file.**  
5. `firmware_config.json`  
    It defines the firmware information for the quabo.
## Upload firmware
When we get a new Quabo, there is no firmware running on the Quabo. We have to upload the necessary firmware to the Quabo.
1. upload bit file to the Quabo  
    (a) connect JTAG to the Qubao;  
    (b) open vivado, and upload `vivado_bit/quabo_fwid.bit` to the Quabo.
2. uploald Golden, Silver firmware and wrpc filesys to the Quabo
    ```
    python upload_firmware.py
    ```
After uploading firmware, you have to disconnect JTAG, and then power cycle the board.
## Run tests
1. test quabo
    ```
    python run_tests.py -r -t quabo
    ```
    **Note: If you don't power cycle the board, and you want to re-run the tests, you can get rid of `-r`, which will skip the reboot Quabo step.**
2. test all of the pixel inputs
    ```
    python run_tests.py -r -t sipmsim -c J1A -b bga
    ```
    **Note: `-c` option tells the software on which connector you attach the SiPM simulator board to.**  
After all of the tests are done, you will see the results in `reports` directory.

