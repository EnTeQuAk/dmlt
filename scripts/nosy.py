#-*- coding: utf-8 -*-
"""
Watch for changes in all .py files. If changes, run nosetests.
"""
from __future__ import with_statement

import glob, os, stat, time, datetime, sys
from os import path
import subprocess
from hashlib import md5

BLOCKSIZE = 8192

def sum_file(sum, fileobj):
    while True:
        data = fileobj.read(BLOCKSIZE)
        if not data:
            break
        sum.update(data)
    return sum


def check_sum():
    sum = md5()
    for root, dirs, filenames in os.walk('./lib/dmlt'):
        if '.svn' in root:
            continue
        for fn in filenames:
            if fn.endswith('.pyc'):
                continue
            with file(path.join(root, fn), 'r') as f:
                sum = sum_file(sum, f)
            print "check %s" % fn
    return sum.hexdigest()


last=0
while True:
    new = check_sum()
    if new != last:
        print "%s: %s" % (new, last)
        sys.stdout.write("run tests...")
        sys.stdout.flush()
        process = subprocess.Popen(
            ['nosetests', '-v', '-d', '--with-doctest', '--doctest-test',
            'tests'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()
        with file('tests.log', 'a') as f:
            dt = datetime.datetime.now()
            f.writelines([
                'new tests from %s\n' % (
                    dt.strftime('%m/%d/%y %H:%M')
                ),
                process.stdout.read(),
                '\nErrors:\n',
                process.stderr.read(),
                '\n\n'
            ])
        sys.stdout.write("finished\n")
        last = new
    #XXX: change me
    time.sleep(5)
