#!/usr/bin/env python
from ConfigParser import RawConfigParser, NoOptionError, NoSectionError, \
                         Error as ConfigParserError
from sys import exit
from os import listdir, unlink
from os.path import abspath, dirname, exists, join
from subprocess import Popen, PIPE


class Error(Exception):
    pass


class NotSyncedException(Error):
    """Exception raised when the remote file isn't synced, meaning that it's
    state isn't identical to the local file state before the commit.
    """
    def __init__(self, file):
        self.msg = "File wasn't sync'ed (someone probably modified it on the" \
                   "remote location without using this repository)." \
                   "Synchronizing it now will result in data loss.\n%s" % file


def is_top_git_directory(filepath):
    git_path = join(filepath, ".git")
    return exists(git_path)


def find_git_root_directory():
    filepath = abspath(".")
    while True:
        if not is_top_git_directory(filepath):
            filepath = dirname(filepath)
        else:
            break

    return filepath

GIT_ROOT = find_git_root_directory()
SITES_ROOT = join(GIT_ROOT, "sites")


def run_command(command):
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    output, errors = process.communicate()

    return output.split('\n'), errors.split('\n')


def process_git_status():
    out, err = run_command("git --no-pager status -s")

    if err != ['']:
        raise Exception(err)

    files_to_update = []
    files_to_delete = []

    for line in out:
        if "  " in line:
            status, name = line.split("  ")

            if status == "D":
                files_to_delete.append(abspath(name))
            elif status == "A" or status == "M":
                files_to_update.append(abspath(name))

    return files_to_update, files_to_delete


def site_from_file(filename):
    return filename.split(SITES_ROOT + "/")[1].split("/")[0]


class GitFilesSync:

    def __init__(self):
        self._configs = {}
        self._modified_sites = []

        self._global_conf = RawConfigParser()
        self._global_conf.read(join(GIT_ROOT, "global.cfg"))

        self._special_values = {"_SPECIAL_GIT_ROOT_": GIT_ROOT}

        for site in listdir(SITES_ROOT):
            self.read_config_from_site(site)

    def read_config_from_site(self, site):
        config = RawConfigParser()
        config.read(join(SITES_ROOT, site, "site.cfg"))

        self._configs[site] = config

    def config_get(self, site, section, item):
        site_config = self._configs[site]

        try:
            return site_config.get(section, item)
        except ConfigParserError, e:
            if isinstance(e, NoOptionError) or isinstance(e, NoSectionError):
                return self._global_conf.get(section, item)
            else:
                raise e

    def config_has_section(self, site, section):
        return self._configs[site].has_section(section) or \
               self._global_conf.has_section(section)

    def config_items(self, site, section):
        global_config_items = dict(self._global_conf.items(section))
        site_config_items = dict(self._configs[site].items(section))

        global_config_items.update(site_config_items)

        for item in global_config_items:
            if "_SPECIAL_" in global_config_items[item]:
                value = global_config_items[item]
                value = value % self._special_values
                global_config_items[item] = value

        return global_config_items

    def process_file_to_update(self, filepath):
        site = site_from_file(filepath)

        self._special_values["_SPECIAL_SITE_"] = join(SITES_ROOT, "sites")

        if self._modified_sites and site not in self._modified_sites:
            print "Warning, 2 sites or more modified"

        # What command should be used to update the file
        global_items = self.config_items(site, "global")

        relative_src_path = filepath.split(join(SITES_ROOT, site, "files"))[1]

        # Is the file marked as to be synced ?
        if not self.config_has_section(site, relative_src_path):
            # Won't be synced
            print "%s - Not marked to be synced." % filepath
            return

        try:
            dst_path = self.config_get(site, relative_src_path, "dst")
        except ConfigParserError, e:
            if isinstance(e, NoOptionError) or isinstance(e, NoSectionError):
                dst_path = relative_src_path
            else:
                raise e

        # Preparing to sync
        global_items.update({"remote_file": dst_path,
                             "local_file": filepath})

        # Check that the file was correctly synced before updating it
        if self.remote_file_exists(global_items):
            if not self.check_synced(global_items):
                raise NotSyncedException(filepath)

        print "%s - Syncing." % relative_src_path
        update_command = global_items["update_command"] % global_items
        output, err = run_command(update_command)

        if err != ['']:
            raise Error(err)

    def remote_file_exists(self, config_items):
        remote_exists = config_items["remote_exists"] % config_items

        output, errors = run_command(remote_exists)

        if errors != ['']:
            raise Exception(errors)

        return output[0] == "yes"

    def check_synced(self, config_items):
        orig_file_command = config_items["orig_file_command"] % config_items
        output, errors = run_command(orig_file_command)
        orig_file = output[0]

        config_items.update({"orig_file": orig_file})

        remote_diff = config_items["remote_diff"] % config_items
        output, errors = run_command(remote_diff)

        unlink(orig_file)

        return output == [""] and errors == [""]


if __name__ == "__main__":
    if not exists(join(GIT_ROOT, "global.cfg")):
        exit("At present state of development, you need to have a global.cfg "
             "file on the root of the git repository.")

    main_object = GitFilesSync()

    # What are the modified files (to update or to delete)
    files_to_update, files_to_delete = process_git_status()

    # There shouldn't be more than one site modified per commit
    # Process each file
    for filename in files_to_update:
        if "sites" in filename:
            try:
                main_object.process_file_to_update(filename)
            except NotSyncedException, e:
                exit(e.message)

    # If the site can't be reached, ask the user if he wants to delay the update
    # or abord the commit. TODO
