#!/bin/bash
source /etc/profile
{
  echo  "$(date)" '-----Collect English ver. start....-----'
  /usr/bin/python3 /home/gao/project/Crawler/index.py --lang en
  echo "$(date)" '-----Collect English ver. finished!-----'
} >> /home/gao/project/Crawler/log/bash.log
sleep 3
{
  echo "$(date)" '-----Collect Japanese ver. start....-----'
  /usr/bin/python3 /home/gao/project/Crawler/index.py --lang ja
  echo -e "$(date)" '-----Collect Japanese ver. finished!-----\n'
} >> /home/gao/project/Crawler/log/bash.log
exit 0