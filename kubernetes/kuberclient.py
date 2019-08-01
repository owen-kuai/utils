"""该文件是captain中自己实现直接调用kubernetes的接口使用的kubeclient可以借鉴参考"""
import json
import logging
import os
import time
from pprint import pprint
from urllib import request

import jinja2
import yaml
from kubernetes.client.rest import (
    ApiException,
)

from kubernetes import (
    client,
    config,
)
from kubernetes.client import Configuration




Template = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KUBE_HOST = os.getenv('KUBE_HOST')
KUBE_CONFIG_FILE = os.getenv('KUBE_CONFIG_FILE')
NAMESPACE = os.getenv('NAMESPACE')



class KubeClient(object):
    def __init__(self, namespace="default", module_name_prefix="", log=None):
        # dynamic load config file
        load_kubernetes_config()

        self.namespace = namespace
        self.module_name_prefix = module_name_prefix
        self.log = log if log is not None else logging.getLogger(__name__)

    def create_or_replace_configmap(self, config_name):
        """
        创建或替换config-map
        :param config_name: 模块名
        :return:
        """
        config_body = self.body_from_templates("config-map", config_name)
        if config_body is None:
            return
        need_create = False

        dcs_config_name = self.module_name_prefix + config_name
        v1 = client.CoreV1Api()
        try:
            # check configmap exist
            v1.read_namespaced_config_map(dcs_config_name, self.namespace)
        except ApiException as e:
            if e.status != 404:
                self.log.error(e)
            # configmap not exist
            need_create = True

        if need_create is True:
            ret = v1.create_namespaced_config_map(self.namespace, config_body)
            self.log.info("Create {} ConfigMap".format(config_name))
        else:
            ret = v1.replace_namespaced_config_map(dcs_config_name, self.namespace, config_body)
            self.log.info("Replace {} ConfigMap".format(config_name))

        return ret

    def create_or_replace_service(self, service_name):
        """
        创建或替换service
        :param service_name:
        :return:
        """
        service_body = self.body_from_templates("service", service_name)
        if service_body is None:
            return
        need_create = False

        dcs_service_name = self.module_name_prefix + service_name
        v1 = client.CoreV1Api()
        try:
            # check service exist
            rsp = v1.read_namespaced_service(dcs_service_name, self.namespace, _request_timeout=30)
            self.log.debug(rsp)
        except ApiException as e:
            if e.status != 404:
                self.log.error(e)
            # service not exist
            need_create = True

        if need_create is True:
            try:
                ret = v1.create_namespaced_service(self.namespace, service_body, _request_timeout=30)
                self.log.info("Create {} Service".format(service_name))
                self.log.debug(ret)
            except ApiException as e:
                self.log.error(e)
            return
        else:
            # TODO: IMPLEMENT THIS (if you can replace a service)
            # skip
            # ret = v1.replace_namespaced_service(dcs_service_name, g.namespace, service_body)
            # self.log.info("Replace {} Service".format(service_name))
            return

    def create_or_replace_deployment(self, deployment_name):
        deployment_body = self.body_from_templates("deployment", deployment_name)
        need_create = False

        dcs_deployment_name = self.module_name_prefix + deployment_name
        v1ext = client.ExtensionsV1beta1Api()
        try:
            # check deployment exist
            v1ext.read_namespaced_deployment(dcs_deployment_name, self.namespace)
            # 等待 Kubernetes 作出反应
            time.sleep(1)
        except ApiException as e:
            if e.status != 404:
                self.log.error(e)
            # not exist
            need_create = True

        if need_create is True:
            ret = v1ext.create_namespaced_deployment(self.namespace, deployment_body)
            return ret
        else:
            v1ext.replace_namespaced_deployment(dcs_deployment_name, self.namespace, deployment_body)
            # 等待 Kubernetes 作出反应
            time.sleep(1)
            ret = v1ext.read_namespaced_deployment(dcs_deployment_name, self.namespace)
            if ret.status.available_replicas is not None:
                self.log.info("Deployment Config unchanged. Skip install {} module".format(deployment_name))
                # or continue
                return None
            return ret

    def create_or_replace_daemonset(self, daemonset_name):
        daemonset_body = self.body_from_templates("daemonset", daemonset_name)
        need_create = False

        dcs_daemonset_name = self.module_name_prefix + daemonset_name
        v1ext = client.ExtensionsV1beta1Api()
        try:
            # check daemonset exist
            v1ext.read_namespaced_daemon_set(dcs_daemonset_name, self.namespace)
            # 等待 Kubernetes 作出反应
            time.sleep(1)
        except ApiException as e:
            if e.status != 404:
                self.log.error(e)
            # not exist
            need_create = True

        if need_create is True:
            ret = v1ext.create_namespaced_daemon_set(self.namespace, daemonset_body)
            return ret
        else:
            v1ext.replace_namespaced_daemon_set(dcs_daemonset_name, self.namespace, daemonset_body)
            # 等待 Kubernetes 作出反应
            time.sleep(1)
            ret = v1ext.read_namespaced_daemon_set(dcs_daemonset_name, self.namespace)
            if ret.status.number_available is not None:
                self.log.info("Daemonset Config unchanged. Skip install {} module".format(daemonset_name))
                # or continue
                return None
            return ret

    def list_deployment(self):
        v1ext = client.ExtensionsV1beta1Api()
        return v1ext.list_namespaced_deployment(namespace=self.namespace)

    def list_daemonset(self):
        v1ext = client.ExtensionsV1beta1Api()
        return v1ext.list_namespaced_daemon_set(namespace=self.namespace)

    def pod_container_name_from_deployment_labels(self, dict_labels):
        # 只取一个 pod
        labels = self.dict_to_args(dict_labels)
        pod_labels = self.pod_labels_from_rs_labels(labels, self.namespace)
        if pod_labels is None:
            self.log.critical("Can not find pod by labels: {}".format(dict_labels))
            return None, None
        pod_labels = self.dict_to_args(pod_labels)
        self.log.debug("Pod Labels: {}".format(pod_labels))
        pod_name, container_names = self.pod_names_from_pod_labels(pod_labels, self.namespace)[0]
        return pod_name, container_names

    def body_from_templates(self, kind, module_name):
        """
        读取部署的yaml文件
        :param kind: 部署类型 deployment/config-map/daemonset
        :param module_name: 模块名
        :return: yaml.load(yaml文件）
        """
        def file_content():
            with open(file_path, 'r') as f:
                return f.read()

        file_path = TEMPLATES_PATH + "{}/{}-{}.yaml".format(kind, module_name, kind)
        try:
            rabbitmq_url = get_rabbit_mq_url()
        except Exception as e:
            self.log.warning("get rabbitmq url faild :{}".format(e.args))
            rabbitmq_url = ""
        try:
            body = file_content()
        except IOError:
            return None
        else:
            if kind == "deployment" or kind == "config-map" or kind == "daemonset":
                dict_item = get_service_dict_config(module_name)
                dict_item["image"] = get_module_image(module_name)
                # 为dict注入mq环境变量
                dict_item['rabbitmq_url'] = rabbitmq_url
                # self.log.debug("#####{module_name}=dict:{dict}".format(module_name=module_name, dict=dict_item))
                if module_name == "dashboard-login" or module_name == "dashboard-vue":
                    dict_item["deploy_at"] = "deploy_at_{}".format(str(time.time()))
                resolve_update_config_dict(dict_item)
                template = Template.from_string(body)
                body = template.render(dict_item=dict_item, path_join=os.path.join)
                # ###############################################################################################
                # dockerplay_dump_filename = os.path.join(SCRIPT_DIR, '../compose_templates/dockerplay3.json')
                # message1 = "*********************************{}*******************************************".format(module_name)
                #
                # open(dockerplay_dump_filename, 'a').write(message1)
                # open(dockerplay_dump_filename, 'a').write(json.dumps(dict_item, indent=4))
                # message2 = "################################{}body####################".format(module_name)
                # open(dockerplay_dump_filename, 'a').write(message2)
                # open(dockerplay_dump_filename, 'a').write(json.dumps(body, indent=4))
                # open(dockerplay_dump_filename, 'a').write("\n\n")
                # ################################################################################################
                self.log.debug("Kind: {}, Module Name: {}".format(kind, module_name))
                self.log.debug(body)
            return yaml.load(body)

    @staticmethod
    def dict_to_args(dictionary: dict):
        label_list = []
        # kubernetes api-server may return None if value not exist
        if dictionary is not None:
            for k, v in dictionary.items():
                label_list.append("{}={}".format(k, v))
        return ",".join(label_list)

    @staticmethod
    def pod_names_from_pod_labels(pod_labels, namespace="default"):
        """
        :param pod_labels:
        :param namespace:
        :return: pod names & container names
        """
        v1 = client.CoreV1Api()
        r = v1.list_namespaced_pod(label_selector=pod_labels, namespace=namespace)
        result = []
        for pod in r.items:
            # ignore terminating pod
            # if pod.status.phase == "Terminating":
            #    continue
            container_names = []
            pod_info = (pod.metadata.name, container_names)
            for container in pod.spec.containers:
                container_names.append(container.name)

            result.append(pod_info)

        return result

    @staticmethod
    def pod_labels_from_rs_labels(rs_labels, namespace="default"):
        # 依赖 Replica Set 里面的 pod-template-hash: "595729186"
        v1ext = client.ExtensionsV1beta1Api()
        r = v1ext.list_namespaced_replica_set(label_selector=rs_labels, namespace=namespace)
        for pod in r.items:
            # ignore old Replicas Set
            if pod.status.replicas == 0:
                continue
            return pod.metadata.labels


def load_kubernetes_config():
    """
    dynamic load config file
    :return:
    """
    # use kube config default location while there are no ENVIRONMENTS about kubernetes config
    try:
        if KUBE_HOST is not None:
            from kubernetes.client import Configuration

            configuration = Configuration()
            configuration.host = KUBE_HOST
            configuration.verify_ssl = False

            Configuration.set_default(configuration)
            return

        config.load_kube_config()
        if KUBE_CONFIG_FILE is not None:
            config.load_kube_config(KUBE_CONFIG_FILE)
    except FileNotFoundError as e:
        raise Exception(str(e), 500)


def check_kubernetes_connection():
    load_kubernetes_config()
    # current configuration
    # configuration = Configuration()
    try:
        v1 = client.CoreV1Api()
        v1.list_namespaced_pod(NAMESPACE)
    except Exception as e:
        raise Exception("Connection failed, {}".format(str(e)), 400)

    return True

#     return _check_kubernetes_connection(configuration.host)
#
#
# def _check_kubernetes_connection(address, timeout=1):
#     from socket import timeout as timeout_error
#     from urllib.error import URLError
#     try:
#         request.urlopen(address, timeout=timeout)
#     except ValueError as e:
#         print("invalid url")
#         raise Exception(KubernetesConfigError.error_id, str(e), 500)
#     except timeout_error as e:
#         print("http connection: timed out, address: ", address)
#         raise Exception(KubernetesConfigError.error_id, "http connection: timed out, address: ", 500)
#     except URLError:
#         raise Exception(KubernetesConfigError.error_id, "Connection refused, {}".format(address), 500)
#     else:
#         return True

