from kubernetes import config
from openshift.dynamic import DynamicClient
from get_config import get_config
import os 

kubeConfig = """
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: __ENDPOINT__
  name: api-__PREFIX__-ar-:6443
contexts:
- context:
    cluster: api-__PREFIX__-ar-:6443
    namespace: default
    user: pizarroapi
  name: default/api-__PREFIX__-ar-:6443/pizarroapi
current-context: default/api-__PREFIX__-ar-:6443/pizarroapi
kind: Config
preferences: {}
users:
- name: pizarroapi
  user:
    token: __TOKEN__
"""

def login(cluster):
    obj_config = get_config()[cluster]

    newKube = kubeConfig.replace("__ENDPOINT__",obj_config['endpoint'])
    newKube = newKube.replace("__PREFIX__",obj_config['prefix'])
    newKube = newKube.replace("__TOKEN__",obj_config['token'])

    if os.path.exists("config"):
        os.remove("config")
    
    a = open("config","w+")
    a.write(newKube)
    a.close()

    k8s_client = config.new_client_from_config("config")
    resp = DynamicClient(k8s_client)

    return resp

def project_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='project.openshift.io/v1', kind='Project')

def pods_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='v1', kind='Pod')

def cronjobs_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='batch/v1beta1', kind='CronJob')

def hpa_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='autoscaling/v1', kind='HorizontalPodAutoscaler')

def quota_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='v1', kind='ResourceQuota')

def rolebinding_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client,dyn_client.resources.get(api_version='rbac.authorization.k8s.io/v1', kind='RoleBinding')

def route_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='route.openshift.io/v1', kind='Route')

def service_obj(cluster):
    dyn_client = login(cluster)
    return dyn_client, dyn_client.resources.get(api_version='v1', kind='Service')