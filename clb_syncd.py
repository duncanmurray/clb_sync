#!/usr/bin/env python

# Duncan Murray 2013

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Load some modules
import pyrax
import json
import logging
import argparse
import os
from pyrax import exceptions as e

def main():

    # Set default metadata key to search for
    METAKEY = "MyGroup0"
    # Set default metadata value to search for
    METAVALUE = "clb0"
    # Set default location of pyrax configuration file
    CREDFILE = "~/.rackspace_cloud_credentials"
    # Set the default location of log files
    LOGPATH = "/var/log/"

    # A short description
    parser = argparse.ArgumentParser(description=("Automatically update load balancer nodes"))
    # Set argument for the region
    parser.add_argument("-r", "--region", action="store", required=False,
                        metavar="REGION", type=str,
                        help=("Region where servers should be built (defaults"
                              " to 'LON'"), choices=["ORD", "DFW", "LON" "IAD", "SYD"],
                        default="LON")
    # Set argument for the metadata key
    parser.add_argument("-mk", "--metakey", action="store", required=False,
                        metavar="META_KEY", type=str,
                        help=("Matadata key that desired node has"),
                        default=METAKEY)
    # Set argument for the metadata value
    parser.add_argument("-mv", "--metavalue", action="store", required=False,
                        metavar="META_VALUE", type=str,
                        help=("Metadata value that desired node has"),
                        default=METAVALUE)
    # Set argument for the cloud load balancer ID
    parser.add_argument("-i", "--clbid", action="store", required=True,
                        metavar="CLB_ID", type=int,
                        help=("Cloud Load Balancer ID"))
    # Set argument for the pyrax credentials file loacation
    parser.add_argument("-c", "--credfile", action="store", required=False,
                        metavar="CREDENTIALS_FILE", type=str,
                        help=("The location of your pyrax configuration file"),
                        default=CREDFILE)
    # Set argument for the log file directory
    parser.add_argument("-p", "--logpath", action="store", required=False,
                        metavar="LOG_DIRECTORY", type=str,
                        help=("The directory to create log files in"),
                        default=LOGPATH)
    # Set argument for verbosity
    parser.add_argument("-v", "--verbose", action="store_true", required=False,
                        help=("Turn on debug verbosity"),
                        default=False)
    
    # Parse the arguments
    args = parser.parse_args()

    # Configure logging
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
                                 """)
        exit(2)

    # Shorten some pyrax calls
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers

    # Check that we have some servers in this region
    if not cs.servers.list():
        rootLogger.critical("No servers found in region '%s'" % (args.region))
        exit(3)
    # Check that we have the load balancer in this region
    if not clb.find(id=args.clbid):
        rootLogger.critical("No matching load balancer found in region '%s'" % (args.region))
        exit(4)

    # Find our load balancer
    myclb = clb.find(id=args.clbid)
    # Let the user know we found the load balancer
    rootLogger.info('Found Load Balancer, id: %i status: %s' % (myclb.id, myclb.status))

    # Create some empty lists
    clbips = []
    csips = []

    # Make a list of nodes currently in out load balancer.
    for node in myclb.nodes:
        if node.condition == 'ENABLED' or 'DISABLED':
            clbips.append(node.address)

    # Let the user know what nodes we found
    rootLogger.info('Current load balancer nodes: %s' % (clbips))

    # Make a list of servers that match out metadata
    for server in cs.servers.list():   
        # filter out only ACTIVE ones
        if server.status == 'ACTIVE':
            # Check for servers that match both your meta key and value
            if args.metakey in server.metadata and server.metadata[args.metakey] == args.metavalue:
                # Grab the private ip address of matching server
                csips.append(server.networks['private'][0])

    # Let the user know what servers match our metadata
    rootLogger.info('Cloud servers matching metadata: %s' % (csips))

    if set(clbips) == set(csips):
        rootLogger.info("No update required")
        exit(0)
    else: 
        pass

    # Make a list of new ip's to add into load balancer
    newips = [x for x in csips if x not in clbips]

    # Make a list of old ip's to remove from load balancer
    oldips = [x for x in clbips if x not in csips]

    # Check out verbosity
    if args.verbose:
        v = True
    else:
        v = False

    # Set our load balancing port
    myport = myclb.port

    # If we have new ip's then add them
    if newips:
        # Let the user know what IP's we are adding
        rootLogger.warning('New nodes to add to load balancer %i: %s' % (myclb.id, newips))
        for ip in newips:
            new_node = clb.Node(address=ip, port=myport, condition="ENABLED")
            myclb.add_nodes([new_node])
            # Wait for the load balancer to update
            pyrax.utils.wait_until(myclb, "status", "ACTIVE", interval=1, 
                                   attempts=30, verbose=v)

    # If we have old ip'd then remove them
    if oldips:
        # Let the user know what ips' we are removing
        rootLogger.warning('Old nodes to remove from load balancer %i: %s' % (myclb.id, oldips))
        for node in myclb.nodes:
            if node.address in oldips:
                node.delete()
                pyrax.utils.wait_until(myclb, "status", "ACTIVE", interval=1, 
                                       attempts=30, verbose=v)
         
    exit(0)

if __name__ == '__main__':
    main()
