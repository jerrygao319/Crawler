#!/bin/bash
echo  "$(date)" '-----Collection English ver. start..-----' > ./log/bash.log
python3 index.py --lang en
echo "$(date)" '-----Collection English ver. finished!-----' > ./log/bash.log
sleep 3
echo "$(date)" '-----Collection Japanese ver. start..-----' > ./log/bash.log
python3 index.py --lang ja
echo "$(date)" '-----Collection Japanese ver. finished!-----' > ./log/bash.log
echo -e "\n" > ./log/bash.log
exit 0