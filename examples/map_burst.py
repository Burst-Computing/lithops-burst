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

NUM_ACTIVATIONS = 20     # This value defines number of activations to be spawned in burst mode
BURST_ENABLED = True    # This value defines if burst mode is enabled or not

def my_map_function(id, x):
    """
    This function will be executed in burst mode in Openwhisk
    Sleeps for 5 seconds to simulate a long-running function
    """
    print(f"I'm activation number {id}")
    time.sleep(5)
    return x


if __name__ == "__main__":
    iterdata = range(NUM_ACTIVATIONS)
    fexec = lithops.FunctionExecutor()
    fexec.map(my_map_function, iterdata, burst=BURST_ENABLED, runtime_memory=2048, granularity=5, join=True)
    future_list = fexec.get_result()
    print(future_list)
    # dump future_list to a file
    try:
        os.remove('result.csv')
    except OSError:
        pass
    with open('result.csv', 'a') as f:
        for i in range(NUM_ACTIVATIONS):
            if i == 0:
                f.write(','.join(fexec.futures[i].stats.keys()) + '\n')
            f.write(','.join(str(i) for i in fexec.futures[i].stats.values()) + '\n')
    fexec.plot()
    f.close()
    fexec.clean()
