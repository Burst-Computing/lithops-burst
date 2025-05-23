#
# (C) Copyright IBM Corp. 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import copy
import os

DEFAULT_CONFIG_KEYS = {
    'runtime_timeout': 600,  # Default: 10 minutes
    'runtime_memory': 256,  # Default memory: 256 MB
    'runtime_cpu': 0.125,  # 0.125 vCPU
    'max_workers': 1000,
    'worker_processes': 1,
    'docker_server': 'docker.io'
}

DEFAULT_GROUP = "codeengine.cloud.ibm.com"
DEFAULT_VERSION = "v1beta1"

FH_ZIP_LOCATION = os.path.join(os.getcwd(), 'lithops_codeengine.zip')

VALID_CPU_VALUES = [0.125, 0.25, 0.5, 1, 2, 4, 6, 8]
VALID_MEMORY_VALUES = [256, 512, 1024, 2048, 4096, 8192, 12288, 16384, 24576, 32768]
VALID_REGIONS = ['us-south', 'us-east', 'ca-tor', 'eu-de', 'eu-gb', 'jp-osa', 'jp-tok', 'br-sao', 'au-syd']

CLUSTER_URL = 'https://proxy.{}.codeengine.cloud.ibm.com'

REQ_PARAMS = ('namespace',)

DOCKERFILE_DEFAULT = """
RUN apt-get update && apt-get install -y \
        zip \
        && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade --ignore-installed setuptools six pip \
    && pip install --upgrade --no-cache-dir --ignore-installed \
        gunicorn \
        pika \
        flask \
        gevent \
        ibm-cos-sdk \
        ibm-vpc \
        redis \
        requests \
        PyYAML \
        kubernetes \
        numpy \
        cloudpickle \
        ps-mem \
        tblib

ENV PORT 8080
ENV CONCURRENCY 1
ENV TIMEOUT 600
ENV PYTHONUNBUFFERED TRUE

# Copy Lithops proxy and lib to the container image.
ENV APP_HOME /lithops
WORKDIR $APP_HOME

COPY lithops_codeengine.zip .
RUN unzip lithops_codeengine.zip && rm lithops_codeengine.zip

CMD exec gunicorn --bind :$PORT --workers $CONCURRENCY --timeout $TIMEOUT lithopsentry:proxy
"""

JOBDEF_DEFAULT = """
apiVersion: codeengine.cloud.ibm.com/v1beta1
kind: JobDefinition
metadata:
  name: lithops-runtime-name
  labels:
    type: lithops-runtime
    version: lithops_vX.X.X
spec:
  arraySpec: '0'
  maxExecutionTime: 600
  retryLimit: 3
  template:
    containers:
    - image: "<INPUT>"
      name: "<INPUT>"
      command:
      - "/usr/local/bin/python"
      args:
      - "/lithops/lithopsentry.py"
      - "$(ACTION)"
      - "$(PAYLOAD)"
      env:
      - name: ACTION
        value: ''
      - name: PAYLOAD
        valueFrom:
          configMapKeyRef:
             key: 'lithops.payload'
             name : NAME
      resources:
        requests:
          cpu: '1'
          memory: 128Mi
    imagePullSecrets:
      - name: lithops-regcred
"""


JOBRUN_DEFAULT = """
apiVersion: codeengine.cloud.ibm.com/v1beta1
kind: JobRun
metadata:
  name: "<INPUT>"
spec:
  jobDefinitionRef: "<REF>"
  jobDefinitionSpec:
    arraySpec: '1'
    maxExecutionTime: 600
    retryLimit: 2
    template:
      containers:
      - name: "<INPUT>"
        env:
        - name: ACTION
          value: ''
        - name: PAYLOAD
          valueFrom:
            configMapKeyRef:
              key: 'lithops.payload'
              name : ''
        resources:
          requests:
            cpu: '1'
            memory: 128Mi
"""


def load_config(config_data):

    if 'ibm' not in config_data or config_data['ibm'] is None:
        raise Exception("'ibm' section is mandatory in the configuration")

    if 'iam_api_key' not in config_data['ibm']:
        raise Exception("'iam_api_key' parameter is mandatory under the 'ibm' section of the configuration")

    temp = copy.deepcopy(config_data['code_engine'])
    config_data['code_engine'].update(config_data['ibm'])
    config_data['code_engine'].update(temp)

    for param in REQ_PARAMS:
        if param not in config_data['code_engine']:
            msg = f'"{param}" is mandatory in the "code_engine" section of the configuration'
            raise Exception(msg)

    if 'region' not in config_data['code_engine']:
        msg = "'region' parameter is mandatory under the 'ibm' or 'code_engine' section of the configuration"
        raise Exception(msg)

    region = config_data['code_engine']['region']
    if region not in VALID_REGIONS:
        raise Exception('{} is an invalid region name. Set one of: '
                        '{}'.format(region, VALID_REGIONS))

    for key in DEFAULT_CONFIG_KEYS:
        if key not in config_data['code_engine']:
            config_data['code_engine'][key] = DEFAULT_CONFIG_KEYS[key]

    runtime_cpu = config_data['code_engine']['runtime_cpu']
    if runtime_cpu not in VALID_CPU_VALUES:
        raise Exception('{} is an invalid runtime cpu value. Set one of: '
                        '{}'.format(runtime_cpu, VALID_CPU_VALUES))

    runtime_memory = config_data['code_engine']['runtime_memory']
    if runtime_memory not in VALID_MEMORY_VALUES:
        raise Exception('{} is an invalid runtime memory value in MB. Set one of: '
                        '{}'.format(runtime_memory, VALID_MEMORY_VALUES))

    if 'runtime' in config_data['code_engine']:
        runtime = config_data['code_engine']['runtime']
        registry = config_data['code_engine']['docker_server']
        if runtime.count('/') == 1 and registry not in runtime:
            config_data['code_engine']['runtime'] = f'{registry}/{runtime}'

    if region and 'region' not in config_data['ibm']:
        config_data['ibm']['region'] = config_data['code_engine']['region']
