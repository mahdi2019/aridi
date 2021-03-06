#!/usr/bin/env python3
#-*- coding: utf-8 -*-

__author__ = "Daniel Pozo"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "ozopip@gmail.com"
__status__ = "Development"

import sys
import reporting
import argparse
import traceback
import gathering0
from gathering1 import getgeneralinfo
from gathering2 import getspecificinfo
from gathering3 import getvolatileinfo
from gathering4 import getotherinfo
from scan import scaninfrastructure
from graph import makegraph


def finish(report, message):
    with open("aridi.log", "w") as f:
        f.writelines(report.view_log())
    sys.exit(message)


def save(filename, text):
    with open(filename, "w") as f:
        f.writelines(text)


def main():
    # It keeps all the logs and reports
    try:
        report = reporting.Reporting()
    except Exception as e:
        sys.exit("ERROR: Failed to create the reporting class.\n" + str(e))

    # CLI Options
    try:
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        parser.add_argument("-a", "--all", help="Try to gather all", action="store_true")
        parser.add_argument("-g", "--general",
                            help="Try to gather general information (default option)",
                            action="store_true")
        parser.add_argument("-s", "--specific", help="Try to gather specific information",
                            action="store_true")
        parser.add_argument("-v", "--volatile", help="Try to gather volatile information",
                            action="store_true")
        parser.add_argument("-c", "--carving", help="Try to gather other information",
                            action="store_true")
        parser.add_argument("--scan", help="Scan the local network and the gathered IPs",
                            action="store_true")
        parser.add_argument("--graph", help="If graphviz is installed, draw the network graph",
                            action="store_true")
        parser.add_argument("-V", "--verbose", metavar="level",
                            help="Increase verbosity level (from -1 lower to 3 higher, 2 default)",
                            type=int)
        group.add_argument("-of", "--output-full", help="Shows all the reports",
                           action="store_true")
        group.add_argument("-os", "--output-sum", help="Shows a summarized report (default)",
                           action="store_true")
        group.add_argument("-od", "--output-det", help="Shows a detailed report",
                           action="store_true")
        group.add_argument("-oi", "--output-inf", help="Shows a report with the infrastructure",
                           action="store_true")
        parser.add_argument("filename", nargs='?', metavar="FILE",
                            help="Shows a report with the infrastructure")
        args = parser.parse_args()

        # Adjunst verbosity level
        if args.verbose:
            report.log("DEBUG", "Verbosity level " + str(args.verbose))
            report.verbose = args.verbose

        # Adjust options for all, specific and the default general option
        if args.all:
            args.general = True
            args.specific = True
            args.volatile = True
            args.carving = True
        elif args.specific:
            args.general = True
        elif not args.volatile and not args.carving:
            # Default option
            args.general = True
    except Exception as e:
        report.log("DEBUG", str(e))
        finish(report, "ERROR: Failed in the argument parsing stage."
                       " See the log for more information.")

    # Precheck phase
    try:
        print("Starting aridi...")
        report.log("INFO", "aridi started")
        report.log("DEBUG", "starting precheck...")
        precheck = gathering0.Precheck()
        if precheck.loadports("./services.csv"):
            report.log("INFO", "{} port names loaded".format(len(precheck.portnames)))
        else:
            message = "aridi can't load port names."
            if args.scan:
                message += " Scan flag was disabled"
                args.scan = None
            report.log("ERROR", message)

        if precheck.root:
            report.log("DEBUG", "Executed with uid 0")
        else:
            report.log("DEBUG", "Executed as a user")
            report.log("WARNING", "aridy.py has been invoked with restricted privileges")
            print("\naridy.py has been invoked with restricted privileges. Some information "
                  "can't be gathered. If you want better results, execute aridy.py with "
                  "root privileges. Do you want to continue anyway? (y/N) ", end="")
            ans = str(input()).lower().lstrip()
            if len(ans) == 0 or 'y' not in ans[0]:
                finish(report, 0)

        report.log("DEBUG", "Precheck finished")
    except Exception as e:
        report.log("DEBUG", str(e))
        report.log("DEBUG", traceback.format_exc())
        finish(report, "ERROR: Failed in the precheck stage. See the log for more information.")

    # Run differents gathering levels
    if args.general:
        try:
            report.log("INFO", "Starting general information gathering...")
            getgeneralinfo(report, precheck)
            report.log("INFO", "General information gathering finished")
        except Exception as e:
            report.log("ERROR", "General information gathering failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    if args.specific:
        try:
            report.log("INFO", "Starting specific information gathering...")
            getspecificinfo(report, precheck)
            report.log("INFO", "Specific information gathering finished")
        except Exception as e:
            report.log("ERROR", "Specific information gathering failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    if args.volatile:
        try:
            report.log("INFO", "Starting volatile information gathering...")
            getvolatileinfo(report, precheck)
            report.log("INFO", "Volatile information gathering finished")
        except Exception as e:
            report.log("ERROR", "Volatile information gathering failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    if args.carving:
        try:
            report.log("INFO", "Starting other information gathering...")
            getotherinfo(report, precheck)
            report.log("INFO", "Other information gathering finished")
        except Exception as e:
            report.log("ERROR", "Other information gathering failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    # Do the scan
    if args.scan:
        try:
            report.log("INFO", "Starting scan stage...")
            scaninfrastructure(report, precheck, 22)
            report.log("INFO", "Scan stage finished")
        except Exception as e:
            report.log("ERROR", "Scan stage failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    # Do the graph
    if args.graph:
        try:
            report.log("INFO", "Creating graph...")
            if makegraph(report):
                report.log("INFO", "Graph generated")
            else:
                report.log("INFO", "Graph didn't generate")
        except Exception as e:
            report.log("ERROR", "Graph creation failed")
            report.log("DEBUG", str(e))
            report.log("DEBUG", traceback.format_exc())

    # Output file or console. It depends of -o* options
    try:
        if args.output_full:
            text = report.view_all(execution=False, general=args.general,
                                   specific=args.specific, volatile=args.volatile,
                                   other=args.carving, infrastructure=args.scan)
            if args.filename:
                save(args.filename, text)
                report.log("INFO", "{} saved".format(args.filename))
            else:
                print(text)
        elif args.output_det:
            text = report.view_detailed(execution=False, general=args.general,
                                        specific=args.specific, volatile=args.volatile,
                                        other=args.carving, infrastructure=args.scan)
            if args.filename:
                save(args.filename, text)
                report.log("INFO", "{} saved".format(args.filename))
            else:
                print(text)
        elif args.output_inf:
            text = report.view_infrastructure()
            if args.filename:
                save(args.filename, text)
                report.log("INFO", "{} saved".format(args.filename))
            else:
                print(text)
        else:
            # Default option
            text = report.view_summarized(execution=False, general=args.general,
                                          specific=args.specific, volatile=args.volatile,
                                          other=args.carving, infrastructure=args.scan)
            if args.filename:
                save(args.filename, text)
                report.log("INFO", "{} saved".format(args.filename))
            else:
                print(text)
    except Exception as e:
        report.log("DEBUG", str(e))
        finish(report, "ERROR: Something goes wrong with the report. "
                       "See the log for more information.")

    report.log("INFO", "aridi.py completed successfully")
    if args.filename:
        print("\nAridi has finished. Report saved to {}.\n".format(args.filename))
    else:
        print("\nAridi has finished\n")
    finish(report, 0)


if __name__ == '__main__':
    main()
