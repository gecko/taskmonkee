#!/bin/bash

cp -r taskmonkee-0.1 /usr/local/share

echo "#!/bin/bash" > taskmonkey.sh
echo "cd /usr/local/share/taskmonkee-0.1" >> taskmonkee.sh
echo "python taskmonkee.py" >> taskmonkee.sh
chmod +x taskmonkee.sh

mv taskmonkee.sh /usr/local/bin/taskmonkee

