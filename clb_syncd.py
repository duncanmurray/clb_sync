#!/usr/bin/env python

import pyrax
import json
import logging
import argparse
import os

def main():

    METADATA = {"MyGroup0":"clb0"}
    # Set default location of pyrax configuration file
    CREDFILE = "~/.rackspace_cloud_credentials"
    # Set the default location of log files
    LOGPATH = "/var/log/lsyncd/"

    parser = argparse.ArgumentParser(description=("Automatically update load balancer nodes"))

    parser.add_argument("-r", "--region", action="store", required=False,
                        metavar="REGION", type=str,
                        help=("Region where servers should be built (defaults"
                              " to 'LON'"), choices=["ORD", "DFW", "LON"],
                        default="LON")

    parser.add_argument("-m", "--meta", action="store", required=False,
                        metavar="METADATA_DICTIONARY", type=json.loads,
                        help=("Metadata used to identify nodes "
                              'Must be in format: {"key": "value"'
                              ', "key": "value", ...} '
                              "default: %s" % (METADATA)),
                        default=METADATA)

    parser.add_argument("-i", "--clbid", action="store", required=True,
                        metavar="CLBID", type=int,
                        help=("Cloud Load Balancer ID"))

    parser.add_argument("-c", "--credfile", action="store", required=False,
                        metavar="CREDENTIALS_FILE", type=str,
                        help=("The location of your pyrax configuration file"),
                        default=CREDFILE)

    parser.add_argument("-p", "--logpath", action="store", required=False,
                        metavar="LOG_DIRECTORY", type=str,
                        help=("The directory to create log files in"),
                        default=LOGPATH)

    parser.add_argument("-v", "--verbose", action="store_true", required=False,
                        help=("Turn on debug verbosity"),
                        default=False)
   
    args = parser.parse_args()

    logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    rootLogger = logging.getLogger()
    # Check what level we should log with
    if args.verbose:
        rootLogger.setLevel(logging.DEBUG)
    else:
        rootLogger.setLevel(logging.WARNING)
    # Configure logging to console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    # Configure logging to file
    try:
        fileHandler = logging.FileHandler("{0}/{1}.log".format(args.logpath, os.path.basename(__file__)))
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
    except IOError:
        rootLogger.critical("Unable to write to log file directory '%s'" % (logpath))
        exit(1) 

    # Define the authentication credentials file location and request that
    # pyrax makes use of it. If not found, let the client/user know about it.

    # Use a credential file in the following format:
    # [rackspace_cloud]
    # username = myusername
    # api_key = 01234567890abcdef
    # region = LON

    pyrax.set_setting("identity_type", "rackspace")

    # Test that the pyrax configuration file provided exists
    try:
        creds_file = os.path.expanduser(args.credfile)
        pyrax.set_credential_file(creds_file, args.region)
    # Exit if authentication fails
    except e.AuthenticationFailed:
        rootLogger.critical("Authentication failed. Please check and confirm"
                            "that the API username, key, and region are in place"
                            "and correct.")
        exit(1)
    # Exit if file does not exist
    except e.FileNotFound:
        rootLogger.critical("Credentials file '%s' not found" % (creds_file))
        rootLogger.info("%s", """Use a credential file in the following format:\n
                                 [rackspace_cloud]
                                 username = myuseername
                                 api_key = 01sdf444g3ffgskskeoek0349
                                 """
                       )
        exit(2)

    clb = pyrax.cloud_loadbalancers
    myclb = clb.find(id=args.clbid)

    #print clb.find(id=args.clbid)
    rootLogger.info(args.meta)
    rootLogger.info('Found Load Balancer, id: %i status: %s' % (myclb.id, myclb.status))

    clbips_enabled = []
    clbips_disabled = []

    for node in myclb.nodes:
        if node.condition == 'ENABLED':
            clbips_enabled.append(node.address)
        if node.condition == 'DISABLED':
            clbips_disabled.append(node.address)

    rootLogger.info('Enabled nodes: %s , Disabled nodes: %s' % (clbips_enabled, clbips_disabled))

if __name__ == '__main__':
    main()
