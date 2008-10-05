#-*- coding: utf-8 -*-
from pocoo.utils.path import path

def main(root, search):
    LOC = 0

    root = path(root).realpath()
    offset = len(root) + 1

    print '+%s+' % ('=' * 78)
    print '| Lines of Code %s |' % (' ' * 62)
    print '+%s+' % ('=' * 78)

    for folder in search:
        pr = 0
        print '+%s  %s  %s+' % ('='*(78/2-len(folder)), folder,
                                '='*(70/2))
        folder = path(root).joinpath(folder).realpath()
        for fn in folder.walk():
            if fn.endswith('.py') or fn.endswith('.js') or fn.endswith('.cs') or fn.endswith('.html'):
                try:
                    fp = file(fn)
                    lines = sum(1 for l in fp.read().splitlines() if l.strip())
                except:
                    print '%-70sskipped' % fn
                else:
                    pr += lines
                    LOC += lines
                    print '| %-68s %7d |' % (fn[offset:], lines)
                fp.close()

        print '+%s  %s lines %s+' % ('='*(69/2-len(str(pr))), pr,
                                     '='*(70/2))
        print '+%s+' % ('='*78)
    print '+%s+' % ('-' * 78)
    print '| Total Lines of Code: %55d |' % LOC
    print '+%s+' % ('-' * 78)


if __name__ == '__main__':
    main('/home/shoxi/Projects', ['dmlt', 'dmlt-sharp', 'globby', 'misc', 'nms', 'toodoya', 'ubuntuusers', 'webpage'])
