#!/bin/bash
{
  echo  "$(date)" '-----Collection English ver. start....-----'
  python3 index.py --lang en
  echo "$(date)" '-----Collection English ver. finished!-----'
} >> /home/gao/project/Crawler/log/bash.log
sleep 3
{
  echo "$(date)" '-----Collection Japanese ver. start....-----'
  python3 index.py --lang ja
  echo "$(date)" '-----Collection Japanese ver. finished!-----'
  echo -e "\n"
} >> /home/gao/project/Crawler/log/bash.log
exit 0