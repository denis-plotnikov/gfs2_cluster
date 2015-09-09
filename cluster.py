#!/usr/bin/python

import subprocess
import sys

CLUSTER_NAME = "mycluster"
FENCE_DEV_NAME = "myfence"
FENCE_METHOD_NAME = "mthd1"
FAILOVER_DOMAIN = "failoverdomain1"
CLUSTER_NODES = ["10.30.29.183", "10.30.18.231"]
#CLUSTER_NODES = ["10.30.26.182"]	


priority_counter = 1
fs_counter = 1

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

def install(pkg_name):
	print("Installing pakage: {0}"
			.format(pkg_name))
	exe_interact("yum install {0}"
			.format(pkg_name))

def install_pkgs():
	pkg_list = [
		"ricci", "luci", "ccs", "cman", "gfs-utils",
		"gfs2-utils", "cmirror", "lvm2-cluster",
		"kmod-gfs", "kmod-cmirror", "rgmanager"]

	for pkg in pkg_list:
		install(pkg)
	print_message("Package installing: Done")

def start_service(service_name):
	exe_interact("service {0} restart"
			.format(service_name))

def enable_service(service_name):
	exe_interact("chkconfig {0} on"
			.format(service_name))

def set_user_passwd(user_name):
	exe_interact("passwd {0}".format(user_name))

def create_cluster():
	exe_interact("ccs -h localhost -i --createcluster {0}"
			.format(CLUSTER_NAME))
	print_message("Cluster created")

def add_cluster_node(node):
	exe_interact("ccs -h localhost --addnode {0}"
			.format(node))

def enable_cluster_fencing():
	exe_interact("ccs -h localhost --setfencedaemon post_fail_delay=0")
	exe_interact("ccs -h localhost --setfencedaemon post_join_delay=25")
	exe_interact("ccs -h localhost --addfencedev {0} agent=fence_virt"
			.format(FENCE_DEV_NAME))
	print_message("Cluster fancing added")

def add_fencing_method(node):
	exe_interact("ccs -h localhost --addmethod {0} {1}"
			.format(FENCE_METHOD_NAME, node))

def attach_fencing_dev(node):
	exe_interact("ccs -h localhost --addfenceinst {0} {1} {2}"
			.format(FENCE_DEV_NAME, node, FENCE_METHOD_NAME))

def create_failover_domain():
	exe_interact("ccs -h localhost --addfailoverdomain {0} ordered"
			.format(FAILOVER_DOMAIN))
	print_message("Failover domain created")

def attach_failover_domain(node):
	global priority_counter
	exe_interact("ccs -h localhost --addfailoverdomainnode {0} {1} {2}"
			.format(FAILOVER_DOMAIN, node, priority_counter))
	priority_counter += 1

def start_cluster():
	exe_interact("ccs -h localhost --sync --activate")
	exe_interact("ccs -h localhost --checkconf")
	exe_interact("ccs -h localhost --startall")
	exe_interact("clustat")

def stop_cluster():
	exe_interact("ccs -h localhost --stopall")

def add_gfs2(dev_path, mount_point):
	global fs_counter
	exe_interact("ccs -h localhost --addresource fs name=gfs2-{0} "
			"device={1} mountpoint={2} fstype=gfs2"
			.format(fs_counter, dev_path, mount_point))
	fs_counter += 1

def prepare_clustering():
	install_pkgs()
	set_user_passwd("ricci")

	service_list = ["cman", "clvmd", "gfs2", "rgmanager", "ricci"]
	for service_name in service_list:
		enable_service(service_name)
		start_service(service_name)

def build_cluster():
	create_cluster()
	create_failover_domain()

	enable_cluster_fencing()
	
	for node in CLUSTER_NODES:
		add_cluster_node(node)
		add_fencing_method(node)
		attach_fencing_dev(node)
		attach_failover_domain(node)

#	add_gfs2("/dev/gfs2-group/test1", "/gfs/test1/")
	#start_cluster()

	print "===== DONE ====="


if __name__ == '__main__':
	if len(sys.argv) == 1:
		prepare_clustering()
		build_cluster()
	else:
		cmd = sys.argv[1]
		if cmd == "install":
			prepare_clustering()
		elif cmd == "create":
			build_cluster() 
		elif cmd == "start":
			start_cluster()
		elif cmd == "stop":
			stop_cluster()
		else:
			print("unknown command: {0}"
					.format(cmd))
