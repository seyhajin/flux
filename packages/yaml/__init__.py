from sys import version_info
if version_info[0] < 3:
    from packages.yaml.yaml2 import *
else:
    from packages.yaml.yaml3 import *
