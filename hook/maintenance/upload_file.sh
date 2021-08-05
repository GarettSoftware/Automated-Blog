#!/bin/bash

# MIT License

# Copyright (c) 2021 Garett MacGowan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Get the script directory (useful for moving files to and from VM)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Start up the VM
. ./common/start_vm.sh || { echo "Failed to start VM. Check your setup.config file."; return 1; }

### Upload a file to the VM ###

# Request file paths from user
LOCAL_FILE_PATH=""
VM_FILE_PATH=""

echo "Please enter the local file path relative this script's directory:"
read -r LOCAL_FILE_PATH
echo "LOCAL_FILE_PATH set to $LOCAL_FILE_PATH"

echo "Please enter the VM file path:"
read -r VM_FILE_PATH
echo "VM_FILE_PATH set to $VM_FILE_PATH"

# Upload the file from the local machine to the VM
gcloud compute scp "$SCRIPT_DIR""$LOCAL_FILE_PATH" "$COMPUTE_INSTANCE_NAME":"$VM_FILE_PATH" --zone="$ZONE" \
|| { echo "ERROR: Failed to copy the logs.zip file off the VM"; return 1; }

# Shut down the VM
. ./common/stop_vm.sh  || { echo "Failed to stop VM. Check your setup.config file."; return 1; }