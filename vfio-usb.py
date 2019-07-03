#!/usr/bin/env python3
#
# Magnus Strahlert @ 190703
#   Handle USB attachment/detachment from KVM VMs based on udev rules

import yaml
import argparse
import sys
import os
import tempfile
from subprocess import PIPE, Popen

def cmdline(command):
  process = Popen(args = command, stdout = PIPE, shell = True, universal_newlines = True)
  return process.communicate()[0]

def parse_config(configfile):
  try:
    with open(configfile) as f:
      config = yaml.load(f, Loader=yaml.BaseLoader)
  except Exception:
    return False

  if not "usb-devices" in config.keys():
    print("Missing required key")
    return False

  return list(config["usb-devices"].items())

def match_id(config, id):
  for k, v in config:
    if v['id'] == id:
      return k, v['vm']

  return False, False

def gen_xml(vendor, product):
  return """<hostdev mode='subsystem' type='usb'>
  <source>
    <vendor id='0x{vendor}'/>
    <product id='0x{product}'/>
  </source>
</hostdev>""".format(vendor=vendor, product=product)

def gen_udev(id):
  return '''ACTION=="add", \\
    SUBSYSTEM=="usb", \\
    ENV{{ID_VENDOR_ID}}=="{vendor}", \\
    ENV{{ID_MODEL_ID}}=="{product}", \\
    RUN+="vfio-usb.py add --vendor {vendor} --product {product}"
ACTION=="remove", \\
    SUBSYSTEM=="usb", \\
    ENV{{ID_VENDOR_ID}}=="{vendor}", \\
    ENV{{ID_MODEL_ID}}=="{product}", \\
    RUN+="vfio-usb.py remove --vendor {vendor} --product {product}"'''.format(vendor=id.split(":")[0], product=id.split(":")[1])

def main():
  parser = argparse.ArgumentParser(description='VFIO-USB handler')
  subparsers = parser.add_subparsers(dest="subparser_name")

  add_parser = subparsers.add_parser("add", help="Attaches device to configured VM")
  add_parser.add_argument("--vendor", required=True)
  add_parser.add_argument("--product", required=True)

  remove_parser = subparsers.add_parser("remove", help="Detaches device from configured VM")
  remove_parser.add_argument("--vendor", required=True)
  remove_parser.add_argument("--product", required=True)

  udev_parser = subparsers.add_parser("udev", help="Generate udev rules")

  parser.add_argument("--config", default="vfio-usb.conf", help="Configfile (default: %(default)s)")

  results = parser.parse_args()

  if results.subparser_name == None:
    parser.print_help()
    sys.exit(0)

  config = parse_config(results.config)

  if results.subparser_name == 'add' or results.subparser_name == 'remove':
    # Find a match for given usb-id to one found in config
    label, vm = match_id(config, ":".join([results.vendor, results.product]))
    if vm:
      # If match found, generate xml to tempfile
      xml = gen_xml(results.vendor, results.product)

      fd, tmpxml = tempfile.mkstemp(text=True)
      fo = os.fdopen(fd, 'wt')
      fo.write(xml)
      fo.close()

      if results.subparser_name == 'add':
        print("Attaching {label} to {vm}".format(label=label, vm=vm))
        cmdline("virsh attach-device {vm} {xml}".format(vm=vm, xml=tmpxml))
      elif results.subparser_name == 'remove':
        print("Detaching {label} from {vm}".format(label=label, vm=vm))
        cmdline("virsh detach-device {vm} {xml}".format(vm=vm, xml=tmpxml))

      os.remove(tmpxml)
  elif results.subparser_name == 'udev':
    # Generate udev config file
    for k, v in config:
      print(gen_udev(v['id']))

if __name__ == "__main__":
  main()
