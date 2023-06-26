"""
Simple Lithops example using the map method.
In this example the map() method will launch one
map function for each entry in 'iterdata'. Finally
it will print the results for each invocation with
fexec.get_result()
"""
import os
import time
from pprint import pprint

import lithops


def my_map_function(id, x):
    time.sleep(5)
    print(f"I'm activation number {id}")
    return x + 7

if __name__ == "__main__":
    iterdata = list(range(130))
    fexec = lithops.FunctionExecutor()
    future_list = fexec.map(my_map_function, iterdata)
    print(fexec.get_result())
    fexec.plot(dst='./')
    i = 0
    # all in same file result.csv
    # delete previous file result.csv
    try:
        os.remove('result.csv')
    except OSError:
        pass
    for future in future_list:
        #     get worker_start_tstamp and worker_end_tstamp
        #      and save it with index of future_list in csv file
        worker_start_tstamp = future.stats['worker_start_tstamp']
        worker_end_tstamp = future.stats['worker_end_tstamp']

        # write in file result.csv
        with open('result.csv', 'a') as f:
            f.write(f'{i},{worker_start_tstamp},{worker_end_tstamp}\n')
        i += 1

    fexec.clean()
