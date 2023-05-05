import sys
import kconfiglib
import os
import shutil
import subprocess

class crops:
    def __init__(self, kconfig, dockerctx, topdir):
        self.topdir = topdir
        self.kconf = kconfiglib.Kconfig(kconfig)
        self.dockerctx = os.path.join(self.topdir, dockerctx)
        for v in self.kconf.variables:
            setattr(self, v.lower().replace('config_','c_'),self.kconf.variables[v].value.replace('"', ''))

    def MakeDockerDir(self):
        if not os.path.exists(self.dockerctx):
            os.makedirs(self.dockerctx)

    def SetEntrypoints(self):
        self.entrypointdir = os.path.join(self.topdir, self.c_entrypoint_dir)
        for fn in os.listdir(self.entrypointdir):
            source = os.path.join(self.entrypointdir, fn)
            dest = os.path.join(self.dockerctx, fn)
            # copy only files
            if os.path.isfile(source):
                shutil.copy(source, dest)
        self.entrypointfiles=os.listdir(self.entrypointdir)
        self.entrypointfiles.reverse()

    def SetUseradd(self):
        self.d_usermod = "ARG USERNAME={c_user} \n".format(c_user=self.c_user)
        self.d_usermod += "RUN useradd -U -m -d {c_workdir} {c_user} \n".format(c_user=self.c_user, c_workdir=self.c_workdir)
        self.d_usermod += "RUN chown {c_user}  {c_workdir} \n".format(c_user=self.c_user, c_workdir=self.c_workdir)

    def SetHostOS(self):
        try:
            self.d_os_from = "FROM {c_registry_namespace}:{c_host_os}-{c_host_os_version}".format( \
                    c_registry_namespace=self.c_registry_namespace, \
                    c_host_os=self.c_host_os, \
                    c_host_os_version=self.c_host_os_version)

            self.d_user = "USER {c_user}".format(c_user=self.c_user)
            self.d_workdir = "WORKDIR {c_workdir}".format(c_workdir=self.c_workdir)

        except KeyError:
            print("Something is seriously wrong with your .config. Most likely \
                   you are missing a required CONFIG_*. Please regenerate your \
                  .config")

    def UnpackTC(self):
        print("Downloading external toolchain, please wait...")
        runtcscript=os.path.join(self.topdir,os.path.join(self.c_tc_dir,self.c_tc_run_script)) + " -d " + self.dockerctx
        print(runtcscript)
        p = subprocess.Popen(runtcscript, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        
        p_status = p.wait()

    def SetTC(self):
        self.d_tc_manager_script = ""
        try: 
            tc_install=open(os.path.join(self.topdir,os.path.join(self.c_tc_dir,self.c_tc_manager_script)), "r")
            self.d_tc_manager_script = tc_install.read()
            tc_install.close()
        except AttributeError:
            self.d_tc_manager_script = ""

    def SetRepo(self):
        self.d_repo_manager_script = ""
        try: 
            repo_install=open(os.path.join(self.topdir,os.path.join(self.d_repo_dir,self.d_repo_manager_script)), "r")
            self.d_repo_manager_script = repo_install.read()
            repo_install.close()
        except AttributeError:
            self.d_repo_manager_script = ""

    def SetPackages(self):
        self.d_packages_setup = ""
        try: 
            pkgs_install=open(os.path.join(self.topdir,os.path.join(self.c_packages_dir,"packages."+ self.c_host_os + "-" + self.c_host_os_version)), "r")
            self.d_packages_setup = pkgs_install.read()
            pkgs_install.close()
        except AttributeError:
            self.d_packages_setup = ""

    def SetEnvs(self):
        self.d_envs_setup = ""
        try: 
            envs_install=open(os.path.join(self.topdir,os.path.join(self.c_envs_dir,"envs."+ self.c_host_os + "-" + self.c_host_os_version)), "r")
            self.d_envs_setup = envs_install.read()
            envs_install.close()
        except AttributeError:
            self.d_envs_setup = ""


    def SetTemplate(self):
        self.d_tempconf = "COPY --chown={c_user}:{c_user} --chmod=755 template.conf /usr/local/bin/ \n".format(c_user=self.c_user)
        self.d_template = "USER root \n"
        np_ep_files = []
        for fn in self.entrypointfiles:
            self.d_template += "COPY --chown={c_user}:{c_user} --chmod=755 {fn} /usr/local/bin/ \n".format(c_user=self.c_user, fn=fn)
            np_ep_files.append("/usr/local/bin/" + fn)
        self.d_entrypoint = "ENTRYPOINT {np_ep_files} \n".format(np_ep_files=np_ep_files)

    def WriteDockerFile(self):
        f = open(os.path.join(self.dockerctx, "Dockerfile"), "w", encoding='utf-8')
        f.write(self.d_os_from + '\n\n')
        f.write(self.d_template + '\n')

        #USER root stage

        f.write(self.d_usermod + '\n\n')
        f.write(self.d_tc_manager_script + '\n')
        f.write(self.d_packages_setup + '\n')

        #USER <yoctouser> stage

        f.write(self.d_user + '\n')
        f.write(self.d_envs_setup + '\n')
        f.write(self.d_workdir + '\n')
        f.write(self.d_repo_manager_script + '\n')
        f.write(self.d_entrypoint + '\n')

        f.close()


