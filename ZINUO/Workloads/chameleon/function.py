import logging
import time

import six
from chameleon import PageTemplate

logging.basicConfig(level=logging.INFO)

BIGTABLE_ZPT = """\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()">
<span tal:define="d python: c + 1"
tal:attributes="class python: 'column-' + %s(d)"
tal:content="python: d" />
</td>
</tr>
</table>""" % six.text_type.__name__


def func():
    # get numbers of rows and columns
    num_of_rows = 1500
    num_of_cols = 1500

    tmpl = PageTemplate(BIGTABLE_ZPT)

    data = {}
    for i in range(num_of_cols):
        data[str(i)] = i

    table = [data for x in range(num_of_rows)]
    options = {'table': table}

    tmpl.render(options=options)


if __name__ == '__main__':
    start_t = time.perf_counter()

    func()

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
