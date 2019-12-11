#!/bin/bash
echo  "$(date)" '-----Collection English ver. start..-----' > ./log/bash.log
python3 index.py --lang en > ./log/bash.log
echo "$(date)" '-----Collection English ver. finished!-----' > ./log/bash.log
sleep 3
echo "$(date)" '-----Collection Japanese ver. start..-----' > ./log/bash.log
python3 index.py --lang ja > ./log/bash.log
echo "$(date)" '-----Collection Japanese ver. finished!-----' > ./log/bash.log
echo -e "\n" > ./log/bash.log
exit 0