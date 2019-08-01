"""简介： pykube是一个写好的封装的kube的库，如果自己想用可以基于这个在封装成自己对应要使用的类"""


import os
import operator
import pykube
import time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    a = None
    b = None
    while True:
        kube_file = os.path.join(SCRIPT_DIR, "config")
        api = pykube.HTTPClient(pykube.KubeConfig.from_file(kube_file))
        pods = pykube.ConfigMap.objects(api).filter(namespace="default")
        for cm in pods:
            if a is None:
                a = cm.metadata
            else:
                b = cm.metadata
            times = time.time()
            if a and b and a != b:
                print('configmap has changed!', times)
            else:
                print("kuaikuai", times)

            time.sleep(0.5)

