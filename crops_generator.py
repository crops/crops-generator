#!/usr/bin/env python3

# generate-crops.py
#
# Copyright (C) 2023 Baylibre 
#
# SPDX-License-Identifier: GPL-2.0-only
#

import sys
import kconfiglib
import os
import shutil
import subprocess


kconf = kconfiglib.Kconfig(sys.argv[1])
dockerctx = sys.argv[2]

# We're going to cheat here. If it's a variable in the .config, we're just going
# to set it to c_<lowercase name>
for v in kconf.variables:
    locals()[v.lower().replace('config_','c_')]=kconf.variables[v].value.replace('"', '')


if not os.path.exists(dockerctx):
    os.makedirs(dockerctx)
entrypointdir = os.path.join(os.path.dirname(__file__), c_entrypoint_dir)

for fn in os.listdir(entrypointdir):
    source = os.path.join(entrypointdir, fn)
    dest = os.path.join(dockerctx, fn)
    # copy only files
    if os.path.isfile(source):
        shutil.copy(source, dest)

d_usermod = "RUN useradd -U -m -d {c_workdir} {c_user} \n".format(c_user=c_user, c_workdir=c_workdir)
d_usermod += "RUN chown {c_user}  {c_workdir} \n".format(c_user=c_user, c_workdir=c_workdir)

try:
    d_os_from = "FROM {c_registry_namespace}:{c_host_os}-{c_host_os_version}".format( \
                c_registry_namespace=c_registry_namespace, \
                c_host_os=c_host_os, \
                c_host_os_version=c_host_os_version)

    d_user = "USER {c_user}".format(c_user=c_user)
    d_workdir = "WORKDIR {c_workdir}".format(c_workdir=c_workdir)

except KeyError:
    print("Something is seriously wrong with your .config. Most likely \
           you are missing a required CONFIG_*. Please regenerate your \
          .config")

try: 
    repo_install=open(os.path.join(os.path.dirname(__file__),os.path.join(c_repo_install_path,c_repo_manager_script)), "r")
    d_repo_manager_script = repo_install.read()
    repo_install.close()
except NameError:
    d_repo_manager_script = ""

try: 
    pkgs_install=open(os.path.join(os.path.dirname(__file__),os.path.join(c_packages_path,"packages."+ c_host_os + "-" + c_host_os_version)), "r")
    d_packages_setup = pkgs_install.read()
    pkgs_install.close()
except NameError:
    d_packages_setup = ""


d_run_external_tc =""
d_copy_external_tc=""

try:
    try:
        c_dl_external_toolchain
        c_dl_external_toolchain = "wget " + c_dl_external_toolchain + " -c -N  -q -P ./" + dockerctx +"/"
        print("Downloading external toolchain, please wait...")
        p = subprocess.Popen(c_dl_external_toolchain, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()  
        p_status = p.wait()
    except:
        pass

    c_use_external_tc

    try:
        d_copy_external_tc = "COPY --chown={c_user}:{c_user} --chmod=755 {c_copy_external_toolchain} \n".format(c_copy_external_toolchain=c_copy_external_toolchain, c_user=c_user)
    except NameError:
        d_copy_external_tc =""

    try:
        d_run_external_tc = "RUN {c_run_external_toolchain} \n".format(c_run_external_toolchain=c_run_external_toolchain)
    except NameError:
        d_run_external_tc = ""

except NameError:
    d_external_tc_env = ""

d_envs_dir = os.path.join(os.path.dirname(__file__), c_envs_dir)
d_envs=""
for fn in os.listdir(d_envs_dir):
    env=open(os.path.join(d_envs_dir,fn), "r")
    val=env.read().strip()
    d_envs += "ENV {fn}=\"{val}\" \n".format(fn=fn,val=val)
    env.close()

for v in kconf.variables:
    if v.startswith("PT_"):
        d_envs += "ENV {fn}=\"{val}\" \n ".format(fn=fn.lstrip("PT_"), 
                                          val=kconf.variables[v].value.replace('"', ''))

d_tempconf = "COPY --chown={c_user}:{c_user} --chmod=755 template.conf /usr/local/bin/ \n".format(c_user=c_user, fn=fn)

entrypointfiles=os.listdir(entrypointdir)
entrypointfiles.reverse()

d_template = "USER root \n"

np_ep_files = []
for fn in entrypointfiles:
     d_template += "COPY --chown={c_user}:{c_user} --chmod=755 {fn} /usr/local/bin/ \n".format(c_user=c_user, fn=fn)
     np_ep_files.append("/usr/local/bin/" + fn)

d_entrypoint = "ENTRYPOINT {np_ep_files} \n".format(np_ep_files=np_ep_files)

try:
    f = open(os.path.join(dockerctx, "Dockerfile"), "w", encoding='utf-8')
    f.write(d_os_from + '\n\n')
    f.write(d_template + '\n')

    #USER root stage

    f.write(d_usermod + '\n\n')
    f.write(d_copy_external_tc + '\n')
    f.write(d_run_external_tc + '\n')
    f.write(d_packages_setup + '\n')

    #USER <yoctouser> stage

    f.write(d_user + '\n')
    f.write(d_envs + '\n')
    f.write(d_workdir + '\n')
    f.write(d_repo_manager_script + '\n')
    f.write(d_entrypoint + '\n')
except:
    print("Something has gone horribly wrong")
finally:
    f.close()

