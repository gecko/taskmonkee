#!/bin/bash

cp -r taskmonkey-0.1 /usr/local/share

echo "#!/bin/bash" > taskmonkey.sh
echo "cd /usr/local/share/taskmonkey-0.1" >> taskmonkey.sh
echo "python taskmonkey.py" >> taskmonkey.sh
chmod +x taskmonkey.sh

mv taskmonkey.sh /usr/local/bin/taskmonkey

