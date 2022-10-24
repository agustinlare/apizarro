from os import name
from get_config import get_config
from k8s_resources import *
from ws_fx import *
import logging, json
import yaml
import re

logging.basicConfig(format='%(asctime)pips|%(levelname)s|%(message)s', level=logging.ERROR)
logging.captureWarnings(True)

# Projects
def get_project_list(cluster):
    resp = []
    dyn_client, v1_projects = project_obj(cluster)
    project_list = v1_projects.get()

    if len(project_list.items):
        for p in project_list.items: resp.append(p.metadata.name)
    else:
        resp = "No project were found"

    return resp

def delete_project_ambiente(ambiente, project):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        dyn_client, v1_projects = project_obj(a)

        try:
            ans = dyn_client.delete(v1_projects, name=project)
            resp.append({"cluster": a, "status": ans.status})
        except Exception as e:
            raise e

    return resp

# Pods - get
def get_pods_list(cluster, project):
    resp = []
    dyn_client, v1_pods = pods_obj(cluster)
    raw_pods = dyn_client.get(v1_pods, namespace=project)

    if len(raw_pods.items) > 0:
        for p in raw_pods.items: resp.append(p.metadata.name)
    else:
        resp = "No pods were found."

    return resp

def get_pods_label_cluster(cluster, project, label):
    resp = []
    dyn_client, v1_pods = pods_obj(cluster)
    raw_pods = dyn_client.get(v1_pods, namespace=project, label_selector=label)

    if len(raw_pods.items) > 0:
        for p in raw_pods.items:
            resp.append(p.metadata.name)
    else:
        resp = "No pods were found."

    return {'cluste': cluster, 'pods': resp}

def get_pods_label_ambiente(ambiente, project, label):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        resp.append(get_pods_label_cluster(a, project, label))

    return resp

# Pods - delete
def delete_pods_name(cluster, project, pod):
    dyn_client, v1_pods = pods_obj(cluster)
    ans = dyn_client.delete(v1_pods, namespace=project, name=pod)

    return {'cluster': cluster, 'pods': ans.metadata.name }

def delete_pods_label_cluster(cluster, project, label):
    resp = []
    dyn_client, v1_pods = pods_obj(cluster)
    ans = dyn_client.delete(v1_pods, namespace=project, label_selector=label)

    if len(ans.items) > 0:
        for i in ans.items: 
            resp.append(i.metadata.name)
    else:
        resp = "No pods were found."
    
    return {'cluster': cluster, "pods": resp}

def delete_pods_label_ambiente(ambiente, project, label):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        resp.append(delete_pods_label_cluster(a, project, label))

    return resp

# Websockets functions
def get_logs_legacy(cluster, project, pod, container):
    resp = pod_logs(get_config()[cluster],project,pod,container)
    
    return resp

def put_user_index(ambiente, user):
    resp = []
    project = "openshift-logging"
    label = "component=elasticsearch"
    container = "elasticsearch"

    for a in get_config()['ambientes'][ambiente]:
        cluster = get_config()[a]
        pods = get_pods_label_cluster(a, project, label)

        assert len(pods) != 0, "No elasticsearch pods available was found"

        index_list = pods_exec(cluster,project,pods[0],"elasticsearch","es_util --query=_cat/indices")
        index_list = index_list.split('\n',-1)
        logging.info("ES index fetched and counted " + str(len(index_list)))

        for index in index_list:
            if user.lower() in index.lower():
                index_user = index.split(' ')
                
                for i in index_user:
                    if user.lower() in i:
                        logging.info("ES user index to delete " + user)
                        index_delete = pods_exec(cluster,project,pods[0],container,"es_util --query=" + i + " -XDELETE")
                        if '\x01' in index_delete:
                            resp.append({"index": i, "message": json.loads(index_delete.replace("\x01",""))})

    return resp

# Cronjobs - get, si se quieren exponer aca estan, pero no me parecieron super utiles ya que este es un dato statico.
def get_cronjob_cluster(cluster, project):
    resp = []
    dyn_client, v1beta1_cronjob = cronjobs_obj(cluster)
    raw_cronjobs = dyn_client.get(v1beta1_cronjob, namespace=project)

    for c in raw_cronjobs.items:
        resp.append(c.metadata.name)

    return resp

def get_cronjob_ambiente(ambiente, project):
    resp = []
    for a in get_config['ambientes'][ambiente]:
        resp.append(get_cronjob_cluster(a, project))

    return resp

# Cronjobs - put
def toggle_cronjob_cluster(cluster, project, cronjob, func):
    enable = """{
        "spec": {
            "suspend" : false
        }
    }"""

    disable = """{
        "spec": {
            "suspend" : true
        }
    }"""

    if func == 'enable':
        body = enable
    else:
        body = disable

    dyn_client, v1beta1_cronjob = cronjobs_obj(cluster)
    resp = dyn_client.patch(v1beta1_cronjob, body=json.loads(body), namespace=project, name=cronjob)

    return { "cronjob": cronjob, "suspend": json.loads(body)['spec']['suspend']}

def toggle_cronjob_ambiente(ambiente, project, cronjob, func):
    resp = []
    
    for a in get_config()['ambientes'][ambiente]:
        resp.append(toggle_cronjob_cluster(a, project, cronjob, func))

    return resp

# Cronjobs - delete
def delete_cronjob_cluster(cluster, project, cronjob):
    dyn_client, v1beta1_cronjob = cronjobs_obj(cluster)
    try: 
        resp = dyn_client.delete(v1beta1_cronjob, namespace=project, name=cronjob)
    except Exception as e:
        logging.error({ "status": e.status, "statusCode": e.status, "message": e.reason })
        raise e

    return resp

def delete_cronjob_ambiente(ambiente, project, cronjob):
    resp = []
    for a in get_config['ambientes'][ambiente]:
        resp.append(delete_cronjob_cluster(a, project, cronjob))

    return resp

# Hpa - get 
def get_hpa_cluster(cluster, project):
    resp = []
    dyn_client, v1_hpa = hpa_obj(cluster)
    raw_hpa = dyn_client.get(v1_hpa, namespace=project)

    for h in raw_hpa.items:
        resp.append(h.metadata.name)

    return {'cluster': cluster, 'hpa': resp}

def get_hpa_ambiente(ambiente, project):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        resp.append(get_hpa_cluster(a, project))

    return resp

# Hpa - delete
def delete_hpa_cluster(cluster, project, hpa):
    dyn_client, v1_hpa = hpa_obj(cluster)
    try:
        resp = dyn_client.replace(v1_hpa, namespace=project, name=hpa)
    except Exception as e:
        raise e

    return {'cluster': cluster, 'hpa': resp.details.name }

def delete_hpa_ambiente(ambiente, project, hpa):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        resp.append(delete_hpa_cluster(a, project, hpa))

    return resp

def edit_hpa_cluster(cluster, project, hpa, file):
    dyn_client, v1_hpa = hpa_obj(cluster)
    try:
        body = yaml.load(file.read())
        dyn_client.patch(v1_hpa, body=body, namespace=project, name=hpa)
    except Exception as e:
        raise e

    return {'cluster': cluster, 'hpa': body }

def edit_hpa_ambiente(ambiente, project, hpa, file):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        resp.append(edit_hpa_cluster(a, project, hpa, file))

    return resp

def duplicar_quota(ambiente, project):
    resp = []

    for a in get_config()['ambientes'][ambiente]:
        dyn_client, v1_quota = quota_obj(a)
        raw_quota = dyn_client.get(v1_quota, namespace=project)

        if len(raw_quota.items) == 1:
            name = raw_quota.items[0].metadata.name
            quota = dyn_client.get(v1_quota, namespace=project, name=name)
            
            if not 'paas.apizarro/redbutton' in quota.metadata.labels.keys():
                cpu = int(raw_quota.items[0]['spec']['hard']['limits.cpu'])
                for i in re.findall(r'\d+', raw_quota.items[0]['spec']['hard']['limits.memory']): memory = int(i)

                body = {'metadata': {'labels': {'paas.apizarro/redbutton': 'true'}},'spec': {'hard': {'limits.cpu': cpu * 2, 'limits.memory': str(memory * 2) + 'Gi'}}}

                try:
                    resp = dyn_client.patch(v1_quota, body=body, namespace=project, name=name)
                except Exception as e:
                    raise e
                    
            else:
                return "This quota it's already double it's origintal size."
        else:
            resp = "Number of quotas not compliance " + str(len(raw_quota.items))

        resp.append({'cluster': a, 'project': project, 'quota': body })

    return resp

# Validate permision - Esta para usar cuando se pueda validar con el token el usuario que envia esto.
def can_you_do_this(ambiente, project, user):
    allow = False 

    for a in get_config()['ambientes'][ambiente]:
        dyn_client, v1_rbac = rolebinding_obj(a)
        rbac_raw = dyn_client.get(v1_rbac, namespace=project)

        for r in rbac_raw.items:
            rb_name = r.metadata.name

            if user.lower() in rb_name:
                return True
            
            elif 'view' in rb_name:
                subjects = r.subjects

                for s in subjects:
                    if user.lower() == s.name.lower():
                        return True

    return allow

def new_ruta_corta(ambiente, project, service, nombre):
    resp = []
    for a in get_config()['ambientes'][ambiente]:
        dyn_client, v1_service = service_obj(a)
        raw_service = dyn_client.get(v1_service, namespace=project, name=service)
        port = raw_service.spec.ports[0].targetPort

        dyn_client, v1_route = route_obj(a)
        route_name = service + '-corta'
        host = nombre + '.apps.' + get_config()[a]['prefix'] + '.ar.'

        body = {
            "apiVersion": "route.openshift.io/v1",
            "kind": "Route",
            "metadata": {
                "name": route_name,
                "namespace": project
            },
            "spec": {
                "host": host,
                "port": {
                    "targetPort": port
                },
                "tls": {
                    "insecureEdgeTerminationPolicy": "Redirect",
                    "termination": "edge"
                },
                "to": {
                    "kind": "Service",
                    "name": service,
                    "weight": 100
                },
                "wildcardPolicy": "None"
            }
        }

        raw_route = dyn_client.create(v1_route, namespace=project, body=body)
        resp.append({'cluster': a, 'route': host})

    return resp