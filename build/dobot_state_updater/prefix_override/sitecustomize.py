import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ssafy/finalPJT/SelfFound/install/dobot_state_updater'
