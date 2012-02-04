=============
Git Sync Hook
=============

This small project aims as providing a simple way to use a git repository to
maintain and synchronize a set of configuration files over a network of
servers.

-------------
Prerequisites
-------------

git, ssh, scp and of course, Python, should be installed.

You must have (provided by this project) the following files:

- **pre-commit.py**

- **global.cfg.template**

- **site.cfg.template**

--------------
How to install
--------------

Unless you already have a configuration files repository, you will want to
create a new repository.

Copy the **pre-commit.py** file to the **.git/hooks** directory. Rename it to
**pre-commit** and change the permissions so that it is executable.

Copy **global.cfg.template** to the root of your repository and rename it to
**global.cfg**. You can have a look and see if you want to change anything,
but it should be pretty standard.

-----------------
Adding a new site
-----------------

If it's not already done, create a **sites/** directory in your repository.
Inside **sites/**, create a directory named after the site. For instance:
**paris_server**.

Copy **site.cfg.template** to **sites/paris_server/** and rename it to
**site.cfg**. You will then need to adapt it, in particular for *remote* and
*key* (if needed) of the "global" section.

-------------------------------
Adding a new configuration file
-------------------------------

In your site directory, create a **files/** directory. Create or move a
configuration file (for instance **hosts**) in this directory.

Edit the **site.cfg** file and add a new section with the name of the
configuration file. You can also set the dst item to the remote path.

For instance::

    [hosts]
    dst=/etc/hosts

There is another way to store the configuration file: you can store it in
**files/remote/path/to/file/file.conf**. For instance::

    files/etc/hosts

That way, you won't have to specify the remote location of the file in the
**site.cfg** file::

    [/etc/hosts]

**Note**: don't forget to use the absolute remote path (including first /).

---------------
Keys management
---------------

Using ssh, you'll probably want to use cryptographic keys. Create a **keys/**
directory in your site directory and copy or create a pair of keys in
**keys/**. For instance::

    paris_server/keys/server.pub
    paris_server/keys/server

Edit **site.cfg** to specify the name of the private key::

    key=-i $(_SPECIAL_SITE_)s/keys/server

------------------------------------------
Special values for the configuration files
------------------------------------------

In order to be able to specify paths in the configuration file, we need some
dynamic variables (need for an system-independant specification + we can't use
relative paths, a git commit can be made from everywhere in the repository).

You can use these for specifying your paths::

    $(_SPECIAL_SITE_)s    : replaced by the absolute path to your site directory
    $(_SPECIAL_GIT_ROOT)s : replaced by the absolute path to the root of the repository

--------------------------
Amending and synchronizing
--------------------------

TODO
