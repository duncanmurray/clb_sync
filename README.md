clb_sync
========

A tool to automatically update a Rackspace cloud load balancer when new nodes are created or deleted based on metadata.

```
usage: clb_syncd.py [-h] [-r REGION] [-mk META_KEY] [-mv META_VALUE] -i CLB_ID
                    [-c CREDENTIALS_FILE] [-p LOG_DIRECTORY] [-v]

Automatically update load balancer nodes

optional arguments:
  -h, --help            show this help message and exit
  -r REGION, --region REGION
                        Region where servers should be built (defaults to
                        'LON'
  -mk META_KEY, --metakey META_KEY
                        Matadata key that desired node has
  -mv META_VALUE, --metavalue META_VALUE
                        Metadata value that desired node has
  -i CLB_ID, --clbid CLB_ID
                        Cloud Load Balancer ID
  -c CREDENTIALS_FILE, --credfile CREDENTIALS_FILE
                        The location of your pyrax configuration file
  -p LOG_DIRECTORY, --logpath LOG_DIRECTORY
                        The directory to create log files in
  -v, --verbose         Turn on debug verbosity
```

####INSTALLATION:

1. Download clb_sync.py
```
git clone https://github.com/duncanmurray/clb_sync.git \
&& cp clb_sync/clb_sync.py /usr/local/sbin/clb_sync.py
```

2. Download and install pyrax
```
pip install pyrax
```
4. Create pyrax configuration file "~/.rackspace_cloud_credentials"
```
[rackspace_cloud]
username = myusername
api_key = 01234567890abcdef
```
5. Create cronjob to run lsyncd_update.py
```
*/2 * * * * /usr/local/sbin/clb_sync.py -v
```
Or better yet use flock until this script it turned into a deamon.
```
*/2 * * * * /usr/bin/flock -n /var/lock/clb_sync.py.lock -c "/usr/local/sbin/clb_sync.py -v"
```

