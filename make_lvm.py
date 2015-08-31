#!/usr/bin/python

import subprocess
import sys
import cluster

VOL_GROUP_NAME = "gfs2-group"
DISK_DEV = "/dev/sdb"
ROOT_MOUNT_POINT = "/gfs"

# volume_name:volume_size
VOLUMES = {
	"test1":"4G",
	"test2":"3G",
			}

def print_message(message):
	indent = ">>>>> "
	print("{0} {1}".format(indent, message))

def exe(command):
	p = subprocess.Popen(command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	out, _ = p.communicate()
	return out

def exe_interact(command):
	p = subprocess.call(command, shell=True)

def get_dev_path(vol_name):
	return "/dev/{0}/{1}" \
		.format(VOL_GROUP_NAME, vol_name)

def remove():
	for vol_name, vol_size in VOLUMES.iteritems():
		dev_path = get_dev_path(vol_name)
		exe_interact("lvremove {0}"
				.format(dev_path))

	exe_interact("vgremove {0}"
			.format(VOL_GROUP_NAME))
	exe_interact("pvremove {0}"
			.format(DISK_DEV))


def build():
	nodes_amount = len(cluster.CLUSTER_NODES)
	# making volume group
	exe_interact("vgcreate {0} {1}"
			.format(VOL_GROUP_NAME, DISK_DEV))
	# making logical volumes
	for vol_name, vol_size in VOLUMES.iteritems():
		exe_interact("lvcreate -n {0} -L{1} {2}"
				.format(vol_name, vol_size, VOL_GROUP_NAME))
		dev_path = get_dev_path(vol_name)
		exe_interact("mkfs.gfs2 -p lock_dlm -t {0}:{1} -j {2} {3}"
				.format(cluster.CLUSTER_NAME, vol_name,
					nodes_amount, dev_path))
	exe_interact("lvdisplay")

def get_mount_point(vol_name):
        return "{0}/{1}".format(ROOT_MOUNT_POINT, vol_name)

def mount_all():
	exe_interact("mkdir -p -v {0}".format(ROOT_MOUNT_POINT))

	for vol_name in VOLUMES.keys():
		mount_point = get_mount_point(vol_name)
		exe_interact("mkdir -p -v {0}"
				.format(mount_point))
		exe_interact("mount.gfs2 {0} {1}"
				.format(get_dev_path(vol_name), mount_point))


def unmount_all():
	for vol_name in VOLUMES.keys():
		exe_interact("umount {0}"
				.format(get_mount_point(vol_name)))

if __name__ == '__main__':
        if len(sys.argv) == 1:
                build()
        else:
                cmd = sys.argv[1]
                if cmd == "build":
                        build()
                elif cmd == "remove":
                        remove()
                elif cmd == "rebuild":
			remove()
                        build()
		elif cmd == "mount":
			mount_all()
		elif cmd == "unmount":
			unmount_all()			
