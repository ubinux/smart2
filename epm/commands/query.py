from epm.option import OptionParser
from epm.control import Control
from epm.cache import Provides
from epm import *
import string
import re

USAGE="epm query [options]"

def parse_options(argv):
    parser = OptionParser(usage=USAGE)
    parser.add_option("--provides", action="store_true",
                      help="show provides for the given packages")
    parser.add_option("--requires", action="store_true",
                      help="show requires for the given packages")
    parser.add_option("--conflicts", action="store_true",
                      help="show conflicts for the given packages")
    parser.add_option("--obsoletes", action="store_true",
                      help="show requires for the given packages")
    parser.add_option("--satisfies", action="store_true",
                      help="show packages satisifying dependencies")
    parser.add_option("--whoprovides", action="append", default=[], metavar="DEP",
                      help="show only packages providing the given dependency")
    parser.add_option("--whorequires", action="append", default=[], metavar="DEP",
                      help="show only packages requiring the given dependency")
    parser.add_option("--whoconflicts", action="append", default=[], metavar="DEP",
                      help="show only packages conflicting with the given "
                           "dependency")
    parser.add_option("--whoobsoletes", action="append", default=[], metavar="DEP",
                      help="show only packages obsoleting the given dependency")
    opts, args = parser.parse_args(argv)
    opts.args = args
    return opts

def main(opts):
    ctrl = Control(opts)
    ctrl.standardInit()

    whoprovides = []
    nulltrans = string.maketrans('', '')
    isre = lambda x: x.translate(nulltrans, '^{[*') != x

    cache = ctrl.getCache()
    packages = []
    if not opts.args:
        for pkg in cache.getPackages():
            packages.append(pkg)
    else:
        for name in opts.args:
            if isre(name):
                p = re.compile(name)
                for pkg in cache.getPackages():
                    if p.match(pkg.name):
                        packages.append(pkg)
            else:
                for pkg in cache.getPackages(name):
                    packages.append(pkg)

    for name in opts.whoprovides:
        if '=' in name:
            name, version = name.split('=')
        else:
            version = None
        if isre(name):
            p = re.compile(name)
            for prv in cache.getProvides():
                if p.match(prv.name):
                    whoprovides.append(Provides(prv.name, version))
        else:
            whoprovides.append(Provides(name, version))
    whorequires = []
    for name in opts.whorequires:
        if '=' in name:
            name, version = name.split('=')
        else:
            version = None
        if isre(name):
            p = re.compile(name)
            for req in cache.getRequires():
                if p.match(req.name):
                    whorequires.append(Provides(req.name, version))
        else:
            whorequires.append(Provides(name, version))
    whoobsoletes = []
    for name in opts.whoobsoletes:
        if '=' in name:
            name, version = name.split('=')
        else:
            version = None
        if isre(name):
            p = re.compile(name)
            for obs in cache.getObsoletes():
                if p.match(obs.name):
                    whoobsoletes.append(Provides(obs.name, version))
        else:
            whoobsoletes.append(Provides(name, version))
    whoconflicts = []
    for name in opts.whoconflicts:
        if '=' in name:
            name, version = name.split('=')
        else:
            version = None
        if isre(name):
            p = re.compile(name)
            for cnf in cache.getConflicts():
                if p.match(cnf.name):
                    whoconflicts.append(Provides(cnf.name, version))
        else:
            whoconflicts.append(Provides(name, version))

    if whoprovides or whorequires or whoobsoletes or whoconflicts:
        newpackages = []
        for whoprv in whoprovides:
            for prv in cache.getProvides(whoprv.name):
                if not whoprv.version or prv.name == prv.version:
                    for pkg in prv.packages:
                        if pkg in packages:
                            newpackages.append(pkg)
        for whoreq in whorequires:
            for req in cache.getRequires(whoreq.name):
                if req.matches(whoreq):
                    for pkg in req.packages:
                        if pkg in packages:
                            newpackages.append(pkg)
        for whoobs in whoobsoletes:
            for obs in cache.getObsoletes(whoobs.name):
                if obs.matches(whoobs):
                    for pkg in obs.packages:
                        if pkg in packages:
                            newpackages.append(pkg)
        for whocnf in whoconflicts:
            for cnf in cache.getConflicts(whocnf.name):
                if cnf.matches(whocnf):
                    for pkg in cnf.packages:
                        if pkg in packages:
                            newpackages.append(pkg)
        packages = newpackages

    packages.sort()
    lastpkg = None
    for pkg in packages:
        if pkg == lastpkg:
            continue
        lastpkg = pkg
        print pkg
        if pkg.provides and (opts.provides or whoprovides):
            pkg.provides.sort()
            first = True
            for prv in pkg.provides:
                if whoprovides:
                    for whoprv in whoprovides:
                        if (prv.name == whoprv.name and
                            (not whoprv.version or
                             prv.version == whoprv.version)):
                            break
                    else:
                        continue
                if first:
                    first = False
                    print "  Provides:"
                print "   ", prv
        if pkg.requires and (opts.requires or whorequires):
            pkg.requires.sort()
            first = True
            for req in pkg.requires:
                if whorequires:
                    for whoreq in whorequires:
                        if req.matches(whoreq):
                            break
                    else:
                        continue
                if first:
                    first = False
                    print "  Requires:"
                print "   ", req
                if opts.satisfies and req.providedby:
                    print "      Provided By:"
                    for prv in req.providedby:
                        prv.packages.sort()
                        lastprvpkg = None
                        for pkg in prv.packages:
                            if pkg == lastprvpkg:
                                continue
                            lastprvpkg = pkg
                            print "       ", "%s (%s)" % (pkg, prv)
        if pkg.obsoletes and (opts.obsoletes or whoobsoletes):
            pkg.obsoletes.sort()
            first = True
            for obs in pkg.obsoletes:
                if whoobsoletes:
                    for whoobs in whoobsoletes:
                        if obs.matches(whoobs):
                            break
                    else:
                        continue
                if first:
                    first = False
                    print "  Obsoletes:"
                print "   ", obs
                if opts.satisfies and obs.providedby:
                    print "      Provided By:"
                    for prv in obs.providedby:
                        prv.packages.sort()
                        lastprvpkg = None
                        for pkg in prv.packages:
                            if pkg == lastprvpkg:
                                continue
                            lastprvpkg = pkg
                            print "       ", "%s (%s)" % (pkg, prv)
        if pkg.conflicts and (opts.conflicts or whoconflicts):
            pkg.conflicts.sort()
            first = True
            for cnf in pkg.conflicts:
                if whoconflicts:
                    for whocnf in whoconflicts:
                        if cnf.matches(whocnf):
                            break
                    else:
                        continue
                if first:
                    first = False
                    print "  Conflicts:"
                print "   ", cnf
                if opts.satisfies and cnf.providedby:
                    print "      Provided By:"
                    for prv in cnf.providedby:
                        prv.packages.sort()
                        lastprvpkg = None
                        for pkg in prv.packages:
                            if pkg == lastprvpkg:
                                continue
                            lastprvpkg = pkg
                            print "       ", "%s (%s)" % (pkg, prv)

    ctrl.standardFinalize()

# vim:ts=4:sw=4:et