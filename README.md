# vfio-usb.py

VFIO-USB handler for KVM based VMs triggering on udev rules according to config file

## Install

1. Copy `vfio-usb.py` to somewhere in your path
2. Edit the provided configfile that lists USB devices with their respective vendor and model attributes (ID) and which VM they should attach/detach to

To find out which ID a USB device has the command `lsusb` can be used.

### Generate and reload udev rules

    vfio-usb.py udev > /etc/udev/rules.d/90-vfio-usb.rules
    udevadm control --reload-rules
