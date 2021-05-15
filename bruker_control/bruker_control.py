# Bruker 2-Photon Experiment Control
# Jeremy Delahanty May 2021
# Harvesters written by Kazunari Kudo
# https://github.com/genicam/harvesters
# pySerialTransfer written by PowerBroker2
# https://github.com/PowerBroker2/pySerialTransfer
# Genie Nano manufactured by Teledyne DALSA

# Version Number
__version__ = "0.20"

###############################################################################
# Import Packages
###############################################################################

# -----------------------------------------------------------------------------
# Custom Modules: Bruker Control
# -----------------------------------------------------------------------------
# Import config_utils functions for manipulating config files
import config_utils

# Import video_utils functions for using Harvesters for camera
import video_utils

# -----------------------------------------------------------------------------
# Python Libraries
# -----------------------------------------------------------------------------
# File Types
# Import JSON for configuration file
import json

# Import ordered dictionary to ensure order in json file
from collections import OrderedDict

# Import argparse if you want to create a configuration on the fly
import argparse

# Import glob for finding and writing files/directories

# Trial Array Generation
# Import scipy.stats truncated normal distribution for ITI Array
from scipy.stats import truncnorm

# Import numpy for trial array generation/manipulation and Harvesters
import numpy as np

# Import numpy default_rng
from numpy.random import default_rng

# Serial Transfer
# Import pySerialTransfer for serial comms with Arduino
from pySerialTransfer import pySerialTransfer as txfer

# Import os to change directories and write files to disk
import os

# Import glob for searching for files and grabbing relevant configs
import glob

# Import sys for exiting program safely
import sys

# NOTE Prairie View Interface
# win32com client installation: Do NOT use pip install, use conda.
# conda install pywin32
import win32com.client
pl = win32com.client.Dispatch("PrairieLink.Application")

###############################################################################
# Functions
###############################################################################

###############################################################################
# Random Array Generation: One Packet
###############################################################################


# -----------------------------------------------------------------------------
# Trial Array Generation: One Packet
# -----------------------------------------------------------------------------


def gen_trialArray_onepacket(totalNumberOfTrials):

    # Always initialize trial array with 3 reward trials
    trialArray = [1, 1, 1]

    # Define number of samples needed from generator
    num_samples = totalNumberOfTrials - len(trialArray)

    # Define probability that the animal will receive sucrose 50% of the time
    sucrose_prob = 0.5

    # Initialize random number generator with default_rng
    rng = default_rng(2)

    # Generate a random trial array with Generator.binomial.  Use n=1 to pull
    # one sample at a time and p=0.5 as probability of sucrose.  Use
    # num_samples to generate the correct number of trials.  Finally, use
    # tolist() to convert random_trials from an np.array to a list.
    random_trials = rng.binomial(
                                 n=1, p=sucrose_prob, size=num_samples
                                ).tolist()

    # Append the two arrays together
    for i in random_trials:
        trialArray.append(i)

    # If the total number of trials is larger than 45, which is the max size
    # that can be transmitted in one packet, a different function will be used
    # to send that information.

    # TODO: Write out the trial array into JSON as part of experiment config

    # Return trialArray
    return trialArray

# -----------------------------------------------------------------------------
# ITI Array Generation: One Packet
# -----------------------------------------------------------------------------


def gen_ITIArray_onepacket(totalNumberOfTrials):

    # Initialize empty iti array
    iti_array = []

    # Define lower and upper limits on ITI values in ms
    iti_lower, iti_upper = 2500, 3500

    # Define mean and variance for ITI values
    mu, sigma = 3000, 1000

    # Upper bound calculation
    upper_bound = (iti_upper - mu)/sigma

    # Lower bound calculation
    lower_bound = (iti_lower - mu)/sigma

    # Generate array by sampling from truncated normal distribution w/scipy
    iti_array = truncnorm.rvs(
                              lower_bound, upper_bound, loc=mu, scale=sigma,
                              size=totalNumberOfTrials
                             )

    # ITI Array generated will have decimals in it and be float type
    # Use np.round() to round the elements in the array and type them as int
    iti_array = np.round(iti_array).astype(int)

    # Finally, generate ITIArray as a list for pySerialTransfer
    ITIArray = iti_array.tolist()

    # Return ITI Array
    return ITIArray


# -----------------------------------------------------------------------------
# Noise Array Generation: One Packet
# -----------------------------------------------------------------------------


def gen_noiseArray_onepacket(totalNumberOfTrials):

    # Initialize empty noise array
    noise_array = []

    # Define lower and upper limits on ITI values in ms
    noise_lower, noise_upper = 2500, 3500

    # Define mean and variance for ITI values
    mu, sigma = 3000, 1000

    # Upper bound calculation
    upper_bound = (noise_upper - mu)/sigma

    # Lower bound calculation
    lower_bound = (noise_lower - mu)/sigma

    # Generate array by sampling from truncated normal distribution w/scipy
    noise_array = truncnorm.rvs(
                                lower_bound, upper_bound, loc=mu, scale=sigma,
                                size=totalNumberOfTrials
                                )

    # Noise Array generated will have decimals in it and be float type.
    # Use np.round() to round the elements in the array and type them as int.
    noise_array = np.round(noise_array).astype(int)

    # Finally, generate noiseArray as a list for pySerialTransfer.
    noiseArray = noise_array.tolist()

    # Return the noiseArray
    return noiseArray


###############################################################################
# Random Array Generation: Multi-packet
###############################################################################

# -----------------------------------------------------------------------------
# Trial Array Generation: Multi-packet
# -----------------------------------------------------------------------------


def gen_trialArray_multipacket(totalNumberOfTrials):

    # Always initialize trial array with 3 reward trials
    trialArray = [1, 1, 1]

    # Define number of samples needed from generator
    num_samples = totalNumberOfTrials - len(trialArray)

    # Define probability that the animal will receive sucrose 50% of the time
    sucrose_prob = 0.5

    # Initialize random number generator with default_rng
    rng = default_rng(2)

    # Generate a random trial array with Generator.binomial.  Use n=1 to pull
    # one sample at a time and p=0.5 as probability of sucrose.  Use
    # num_samples to generate the correct number of trials.  Finally, use
    # tolist() to convert random_trials from an np.array to a list.
    random_trials = rng.binomial(
                                 n=1, p=sucrose_prob,
                                 size=num_samples
                                ).tolist()

    # Append the two arrays together
    for i in random_trials:
        trialArray.append(i)

    # Use np.array_split() to divide list into smaller sizes
    split_array = np.array_split(trialArray, 2)

    # First index of split array is content of first packet
    first_trialArray = split_array[0].tolist()

    # Second index of split array is content of second packet
    second_trialArray = split_array[1].tolist()

    # TODO: Write out the trial array into JSON as part of experiment config

    # Return trial arrays
    return first_trialArray, second_trialArray


# -----------------------------------------------------------------------------
# ITI Array Generation: Multi-packet
# -----------------------------------------------------------------------------


def gen_ITIArray_multipacket(totalNumberOfTrials):

    # Initialize empty iti array
    iti_array = []

    # Define lower and upper limits on ITI values in ms
    iti_lower, iti_upper = 2500, 3500

    # Define mean and variance for ITI values
    mu, sigma = 3000, 1000

    # Upper bound calculation
    upper_bound = (iti_upper - mu)/sigma

    # Lower bound calculation
    lower_bound = (iti_lower - mu)/sigma

    # Generate array by sampling from truncated normal distribution w/scipy
    iti_array = truncnorm.rvs(
                              lower_bound, upper_bound, loc=mu, scale=sigma,
                              size=totalNumberOfTrials
                             )

    # ITI Array generated will have decimals in it and be float type
    # Use np.round() to round the elements in the array and type them as int
    iti_array = np.round(iti_array).astype(int)

    split_array = np.array_split(iti_array, 2)
    first_ITIArray = split_array[0].tolist()
    second_ITIArray = split_array[1].tolist()

    # TODO: Write out the ITI array into JSON as part of experiment config

    # Return first and second ITI Arrays
    return first_ITIArray, second_ITIArray


# -----------------------------------------------------------------------------
# Noise Array Generation: Multi-packet
# -----------------------------------------------------------------------------


def gen_noiseArray_multipacket(totalNumberOfTrials):

    # Initialize empty noise array
    noise_array = []

    # Define lower and upper limits on ITI values in ms
    noise_lower, noise_upper = 2500, 3500

    # Define mean and variance for ITI values
    mu, sigma = 3000, 1000

    # Upper bound calculation
    upper_bound = (noise_upper - mu)/sigma

    # Lower bound calculation
    lower_bound = (noise_lower - mu)/sigma

    # Generate array by sampling from truncated normal distribution w/scipy
    noise_array = truncnorm.rvs(
                                lower_bound, upper_bound, loc=mu, scale=sigma,
                                size=totalNumberOfTrials
                                )

    # Noise Array generated will have decimals in it and be float type.
    # Use np.round() to round the elements in the array and type them as int.
    noise_array = np.round(noise_array).astype(int)

    split_array = np.array_split(noise_array, 2)
    first_noiseArray = split_array[0].tolist()
    second_noiseArray = split_array[1].tolist()

    # TODO:  Write out the noise array into JSON as part of experiment config

    # Return the first and second noise arrays
    return first_noiseArray, second_noiseArray

###############################################################################
# Serial Transfer to Arduino: One Packet
###############################################################################

# -----------------------------------------------------------------------------
# Configuration/Metadata File Transfer
# -----------------------------------------------------------------------------


def serialtransfer_metadata(config):

    try:
        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # stuff TX buffer (https://docs.python.org/3/library/struct.html#format-characters)
        metaData_size = 0
        metaData_size = link.tx_obj(config['metadata']['totalNumberOfTrials']['value'],       metaData_size, val_type_override='B')
        metaData_size = link.tx_obj(config['metadata']['punishTone']['value'],                metaData_size, val_type_override='H')
        metaData_size = link.tx_obj(config['metadata']['rewardTone']['value'],                metaData_size, val_type_override='H')
        metaData_size = link.tx_obj(config['metadata']['USDeliveryTime_Sucrose']['value'],    metaData_size, val_type_override='B')
        metaData_size = link.tx_obj(config['metadata']['USDeliveryTime_Air']['value'],        metaData_size, val_type_override='B')
        metaData_size = link.tx_obj(config['metadata']['USConsumptionTime_Sucrose']['value'], metaData_size, val_type_override='H')

        link.open()

        link.send(metaData_size, packet_id=0)

        while not link.available():
            pass

        # Receive packet from Arduino
        # Create rxmetaData dictionary
        rxmetaData = {}
        rxmetaData_size = 0

        rxmetaData['totalNumberOfTrials'] = link.rx_obj(obj_type='B', start_pos=rxmetaData_size)
        rxmetaData_size += txfer.ARRAY_FORMAT_LENGTHS['B']
        rxmetaData['punishTone'] = link.rx_obj(obj_type='H', start_pos=rxmetaData_size)
        rxmetaData_size += txfer.ARRAY_FORMAT_LENGTHS['H']
        rxmetaData['rewardTone'] = link.rx_obj(obj_type='H', start_pos=rxmetaData_size)
        rxmetaData_size += txfer.ARRAY_FORMAT_LENGTHS['H']
        rxmetaData['USDeliveryTime_Sucrose'] = link.rx_obj(obj_type='B', start_pos=rxmetaData_size)
        rxmetaData_size += txfer.ARRAY_FORMAT_LENGTHS['B']
        rxmetaData['USDeliveryTime_Air'] = link.rx_obj(obj_type='B', start_pos=rxmetaData_size)
        rxmetaData_size += txfer.ARRAY_FORMAT_LENGTHS['B']
        rxmetaData['USConsumptionTime_Sucrose'] = link.rx_obj(obj_type='H', start_pos=rxmetaData_size)

        print(rxmetaData)

        # TODO: Put error checking outside the function
        # Check if metaData was sent correctly:
        # if config == rxmetaData:
        #     print("Confirmed Metadata!")
        #     metaData_status = True
        # else:
        #     print("Metadata error! Exiting...")
        #     sys.exit()

        link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass
    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


# -----------------------------------------------------------------------------
# Trial Array Transfer: One Packet
# -----------------------------------------------------------------------------


def serialtransfer_trialArray_onepacket(trialArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # Initialize trialArray_size of 0
        trialArray_size = 0

        # Stuff packet with size of trialArray
        trialArray_size = link.tx_obj(trialArray)

        # Open communication link
        link.open()

        # Send array
        link.send(trialArray_size, packet_id=0)

        print("Sent Trial Array")
        print(trialArray)

        while not link.available():
            pass

        # Receive trial array:
        rxtrialArray = link.rx_obj(obj_type=type(trialArray),
                                   obj_byte_size=trialArray_size,
                                   list_format='i')

        print("Received Trial Array")
        print(rxtrialArray)

        # TODO: Move error handling outside of function; need to learn how...

        # if trialArray == rxtrialArray:
        #     print("Trial Array transfer successful!")
        #
        # else:
        #     link.close()
        #     print("Trial Array error! Exiting...")
        #     sys.exit()

        # Close the communication link
        link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass

    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


# -----------------------------------------------------------------------------
# ITI Array Transfer: One Packet
# -----------------------------------------------------------------------------


def serialtransfer_ITIArray_onepacket(ITIArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # Send ITI array:
        ITIArray_size = 0
        ITIArray_size = link.tx_obj(ITIArray)
        link.open()
        link.send(ITIArray_size, packet_id=0)

        print(ITIArray)

        while not link.available():
            pass

        # Receive ITI Array
        rxITIArray = link.rx_obj(obj_type=type(ITIArray),
                                 obj_byte_size=ITIArray_size,
                                 list_format='i')

        print(rxITIArray)

        # TODO: Move error checking outside function
        # Confirm data was sent/received properly:
        # if ITIArray == rxITIArray:
        #     print("Confrimed ITI Array!")
        # else:
        #     link.close()
        #     print("ITI Array error! Exiting...")
        #     sys.exit()
        #
        # link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass
    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


# -----------------------------------------------------------------------------
# Noise Array Transfer: One Packet
# -----------------------------------------------------------------------------


def serialtransfer_noiseArray_onepacket(noiseArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)
        noiseArray_size = 0
        noiseArray_size = link.tx_obj(noiseArray)
        link.open()
        link.send(noiseArray_size, packet_id=0)

        print(noiseArray)

        while not link.available():
            pass

        # Receive Noise Duration Array
        rxnoiseArray = link.rx_obj(obj_type=type(noiseArray),
                                   obj_byte_size=noiseArray_size,
                                   list_format='i')

        print(rxnoiseArray)

        # TODO: Move error checking outside function
        # if noiseArray == rxnoiseArray:
        #     print("Noise Array transfer successful")
        # else:
        #     link.close()
        #     print("Noise Array transfer failure")
        #     print("Exiting...")
        #     sys.exit()

        link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass
    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


###############################################################################
# Serial Transfer to Arduino: Multi-packet
###############################################################################

# -----------------------------------------------------------------------------
# Trial Array Transfer: Multi-packet
# -----------------------------------------------------------------------------


def serialtransfer_trialArray_multipacket(first_trialArray, second_trialArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # Initialize first packet size of 0
        first_trialArray_size = 0

        # Stuff the packet with the first trial array
        first_trialArray_size = link.tx_obj(first_trialArray)

        # Open the communication link
        link.open()

        # Send the first packet with a packet_id of 0
        link.send(first_trialArray_size, packet_id=0)

        print("First Half of Trials Sent")
        print(first_trialArray)

        while not link.available():
            pass

        # Receive the first half of trials from Arduino
        rxfirst_trialArray = link.rx_obj(obj_type=type(first_trialArray),
                                         obj_byte_size=first_trialArray_size,
                                         list_format='i')

        print("First Half of Trials Received")
        print(rxfirst_trialArray)

        # TODO Move error checking outside this function

        # # Confirm packet was sent correctly
        # if first_trialArray == rxfirst_trialArray:
        #     print("First Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("First Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()

        # Initialize second packet size of 0
        second_trialArray_size = 0

        # Stuff the packet with second trial array
        second_trialArray_size = link.tx_obj(second_trialArray)

        # Send the second packet with a packet_id of 1
        link.send(second_trialArray_size, packet_id=1)

        print("Second Half of Trials Sent")
        print(second_trialArray)

        while not link.available():
            pass

        # Receive second half of trials from Arduino
        rxsecond_trialArray = link.rx_obj(obj_type=type(second_trialArray),
                                          obj_byte_size=second_trialArray_size,
                                          list_format='i')

        print("Second Half of Trials Received")
        print(rxsecond_trialArray)

        # TODO Put error checking outside this function
        # if second_trialArray == rxsecond_trialArray:
        #     print("Second Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("Second Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()
        #
        # link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass

    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


def serialtransfer_ITIArray_multipacket(first_ITIArray, second_ITIArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # Initialize first packet size of 0
        first_ITIArray_size = 0

        # Stuff the packet with the first trial array
        first_ITIArray_size = link.tx_obj(first_ITIArray)

        # Open the communication link
        link.open()

        # Send the first packet with a packet_id of 0
        link.send(first_ITIArray_size, packet_id=0)

        print("First Half of ITIs Sent")
        print(first_ITIArray)

        while not link.available():
            pass

        # Receive the first half of trials from Arduino
        rxfirst_ITIArray = link.rx_obj(obj_type=type(first_ITIArray),
                                       obj_byte_size=first_ITIArray_size,
                                       list_format='i')

        print("First Half of ITIs Received")
        print(rxfirst_ITIArray)

        # TODO Move error checking outside this function

        # # Confirm packet was sent correctly
        # if first_ITIArray == rxfirst_ITIArray:
        #     print("First Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("First Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()

        # Initialize second packet size of 0
        second_ITIArray_size = 0

        # Stuff the packet with second trial array
        second_ITIArray_size = link.tx_obj(second_ITIArray)

        # Send the second packet with a packet_id of 1
        link.send(second_ITIArray_size, packet_id=1)

        print("Second Half of ITIs Sent")
        print(second_ITIArray)

        while not link.available():
            pass

        # Receive second half of trials from Arduino
        rxsecond_ITIArray = link.rx_obj(obj_type=type(second_ITIArray),
                                        obj_byte_size=second_ITIArray_size,
                                        list_format='i')

        print("Second Half of ITIs Received")
        print(rxsecond_ITIArray)

        # TODO Put error checking outside this function
        # if second_ITIArray == rxsecond_ITIArray:
        #     print("Second Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("Second Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()
        #
        # link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass

    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass


def serialtransfer_noiseArray_multipacket(first_noiseArray, second_noiseArray):

    try:

        # Initialize COM Port for Serial Transfer
        link = txfer.SerialTransfer('COM12', 115200, debug=True)

        # Initialize first packet size of 0
        first_noiseArray_size = 0

        # Stuff the packet with the first trial array
        first_noiseArray_size = link.tx_obj(first_noiseArray)

        # Open the communication link
        link.open()

        # Send the first packet with a packet_id of 0
        link.send(first_noiseArray_size, packet_id=0)

        print("First Half of Noises Sent")
        print(first_noiseArray)

        while not link.available():
            pass

        # Receive the first half of trials from Arduino
        rxfirst_noiseArray = link.rx_obj(obj_type=type(first_noiseArray),
                                       obj_byte_size=first_noiseArray_size,
                                       list_format='i')

        print("First Half of Noises Received")
        print(rxfirst_noiseArray)

        # TODO Move error checking outside this function

        # # Confirm packet was sent correctly
        # if first_noiseArray == rxfirst_noiseArray:
        #     print("First Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("First Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()

        # Initialize second packet size of 0
        second_noiseArray_size = 0

        # Stuff the packet with second trial array
        second_noiseArray_size = link.tx_obj(second_noiseArray)

        # Send the second packet with a packet_id of 1
        link.send(second_noiseArray_size, packet_id=1)

        print("Second Half of Noises Sent")
        print(second_noiseArray)

        while not link.available():
            pass

        # Receive second half of trials from Arduino
        rxsecond_noiseArray = link.rx_obj(obj_type=type(second_noiseArray),
                                          obj_byte_size=second_noiseArray_size,
                                          list_format='i')

        print("Second Half of Noises Received")
        print(rxsecond_noiseArray)

        # TODO Put error checking outside this function
        # if second_noiseArray == rxsecond_noiseArray:
        #     print("Second Half Trial Array Transfer Successful!")
        # else:
        #     link.close()
        #     print("Second Half Trial Array Transfer Failure!")
        #     print("Exiting...")
        #     sys.exit()
        #
        # link.close()

    except KeyboardInterrupt:
        try:
            link.close()
        except:
            pass

    except:
        import traceback
        traceback.print_exc()

        try:
            link.close()
        except:
            pass

###############################################################################
# Prairie View Control
###############################################################################


# -----------------------------------------------------------------------------
# PrairieLink Abort Function
# -----------------------------------------------------------------------------

def prairie_abort():
    print("Connected to Prairie View")
    pl.Connect()
    pl.SendScriptCommands("-Abort")
    pl.Disconnect()
    print("Disconnected from Prairie View")


###############################################################################
# Main Function
###############################################################################


if __name__ == "__main__":

    # Create argument parser for metadata configuration
    metadata_parser = argparse.ArgumentParser(description='Set Metadata',
                                              epilog="Good luck on your work!",
                                              prog='Bruker Experiment Control')

    # Add configuration file argument
    metadata_parser.add_argument('-c', '--config_file',
                                 type=str,
                                 action='store',
                                 dest='config',
                                 help='Config Filename (yyyymmdd_animalid)',
                                 default=None,
                                 required=False)

    # Add modify configuration file argument
    metadata_parser.add_argument('-m', '--modify',
                                 action='store_true',
                                 dest='modify',
                                 help='Modify given config file (bool flag)',
                                 required=False)

    # Add template configuration file argument
    metadata_parser.add_argument('-t', '--template',
                                 action='store_true',
                                 dest='template',
                                 help='Use template config file (bool flag)',
                                 required=False)

    # Add project name argument
    metadata_parser.add_argument('-p', '--project',
                                 type=str,
                                 action='store',
                                 dest='project',
                                 help='Project Name (required)',
                                 choices=['specialk', 'food_dep'],
                                 required=True)

    # Add program version argument
    metadata_parser.add_argument('--version',
                                 action='version',
                                 version='%(prog)s v. ' + __version__)

    # Parse the arguments given by the user
    metadata_args = vars(metadata_parser.parse_args())

    # Use config_utils module to parse metadata_config
    config, project_name, config_filename = config_utils.config_parser(metadata_args)

    # TODO: Let user change configurations/create them on the fly with parser

    # Gather total number of trials
    trials = config["metadata"]["totalNumberOfTrials"]["value"]

    print(trials)
    # Preview video for headfixed mouse placement
    video_utils.capture_preview()
#
    # If only one packet is required, use single packet generation and
    # transfer.  Single packets are all that's needed for sizes less than 45.
    if trials <= 45:

        # Send configuration file
        serialtransfer_metadata(config)

        # Generate single packet arrays
        trialArray = gen_trialArray_onepacket(trials)
        ITIArray = gen_ITIArray_onepacket(trials)
        noiseArray = gen_noiseArray_onepacket(trials)

        # Use single packet serial transfer for arrays
        # serialtransfer_trialArray_onepacket(trialArray)
        # serialtransfer_ITIArray_onepacket(ITIArray)
        # serialtransfer_noiseArray_onepacket(noiseArray)

        # TODO Gather number of frames expected from microscope for num_frames
        # Now that the packets have been sent, the Arduino will start soon.  We
        # now start the camera for recording the experiment!
        video_utils.capture_recording(60, project_name, config_filename)
    #
    #     # Now that video is done recording, tell the user
    #     print("Video Complete")
    #
    #     # End Prairie View's imaging session with abort command
    #     # prairie_abort()
    #
    #     # Now that the microscopy session has ended, let user know the
    #     # experiment is complete!
    #     print("Experiment Over!")
    #
    #     # Exit the program
    #     print("Exiting...")
    #     sys.exit()
    #
    # # If there's multiple packets required, use multipacket generation and
    # # transfer.  Multiple packets are required for sizes greater than 45.
    # elif trials > 45:
    #
    #     # Send configuration file
    #     serialtransfer_metadata(config)
    #
    #     # Generate multipacket arrays
    #     first_trialArray, second_trialArray = gen_trialArray_multipacket(trials)
    #     first_ITIArray, second_ITIArray = gen_ITIArray_multipacket(trials)
    #     first_noiseArray, second_noiseArray = gen_noiseArray_multipacket(trials)
    #
    #     # Use multipacket serial transfer for arrays
    #     serialtransfer_trialArray_multipacket(first_trialArray,
    #                                           second_trialArray)
    #     serialtransfer_ITIArray_multipacket(first_ITIArray,
    #                                         second_ITIArray)
    #     serialtransfer_noiseArray_multipacket(first_noiseArray,
    #                                           second_noiseArray)
    #
    #     # Now that the packets have been sent, the Arduino will start soon.  We
    #     # now start the camera for recording the experiment!
    #     video_utils.capture_recording(600)
    #
    #     # Once recording is done, let user know
    #     print("Video Complete")
    #
    #     # End Prairie View's imaging session with abort command
    #     prairie_abort()
    #
    #     # Now that the microscopy session has ended, let user know the
    #     # experiment is complete!
    #     print("Experiment Over!")
    #
    #     # Exit the program
    #     print("Exiting...")
    #     sys.exit()

    # If some other value that doesn't fit in these categories is given, there
    # is something wrong. Let the user know and exit the program.
    else:
        print("Something is wrong with the config file's # of trials...")
        print("Exiting...")
        sys.exit()
