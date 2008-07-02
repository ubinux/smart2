#
# Copyright (c) 2004 Conectiva, Inc.
#
# Written by Gustavo Niemeyer <niemeyer@conectiva.com>
#
# Archlinux module written by Cody Lee (aka. platinummonkey) <platinummonkey@archlinux.us>
#
# This file is part of Smart Package Manager.
#
# Smart Package Manager is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# Smart Package Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Smart Package Manager; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
from smart.backends.arch.loader import ArchDBLoader
from smart.channel import PackageChannel
from smart import *
import os

class ArchSysChannel(PackageChannel):

    def __init__(self, *args):
        super(ArchSysChannel, self).__init__(*args)

    def fetch(self, fetcher, progress):
        dir = os.path.join(sysconf.get("arch-root", "/"),
                           sysconf.get("arch-packages-dir",
                                       "var/cache/pacman/pkg"))
        digest = os.path.getmtime(dir)
        if digest == self._digest:
            return True
        self.removeLoaders()
        loader = ArchDBLoader()
        loader.setChannel(self)
        self._loaders.append(loader)
        self._digest = digest
        return True

def create(alias, data):
    if data["removable"]:
        raise Error, _("%s channels cannot be removable") % data["type"]
    return ArchSysChannel(data["type"],
                           alias,
                           data["name"],
                           data["manual"],
                           data["removable"],
                           data["priority"])

# vim:ts=4:sw=4:et
