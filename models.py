######### MODELO PIZARRO ##########
# Listas
ambiente_lista = []
for i in get_config()['ambientes'].keys():
    ambiente_lista.append(i)

ambiente = zarro.model('ambiente', {'ambiente': fields.String(description='Ambien de ejecucion', example='qa', enum=ambiente_lista, required=True)})

cluster_lista = []
for i in ambiente_lista:
    for c in get_config()['ambientes'][i]:
        cluster_lista.append(c)

cluster = zarro.model('cluster', {'cluster': fields.String(description='Cluster de ejecucion', example='qaaz1', enum=cluster_lista, required=True)})

# Strings
project = zarro.model('project', {'project': fields.String(description='Nombre del Proyecto (tener en cuenta prefijo "dev-", "stg-")', example='stg-accounts-api')})
label = zarro.model('label', {'label': fields.String(description='Label unico de la aplicacion', example='app=accounts-iatx')})
name = zarro.model('name', {'name': fields.String(description='Nombre unico del objeto (pod, project, cronjob) .metadata.name', example='accounts-api-fas8da')})
user = zarro.model('user', {'user': fields.String(description='Usuario de dominio, como te logueas a tu PC', example='A309788')})
container = zarro.model('container', {'container': fields.String(description='Nombre del container del pod  .metadata.spec.container[].name', example='accounts-api')})
tags = zarro.model('tags', {'key': fields.String, 'value': fields.String})
size = zarro.model('size', {'size': fields.String(description='Tamaño de la account a solicitar', enum=sgConfig['size'], required=True)})
email = zarro.model('email', {'email': fields.String(description='Email de notificacion', example='alavarello@pepe.com.ar', required=True)})
cmdb = zarro.model('cmdb', {'cmdb': fields.String(description='Codigo CMDB de la aplicacion', example='ocp')})
aplicacion = zarro.model('aplicacion', {'aplicacion': fields.String(description='Indicador custom de la aplicacion', example='jmeter', required=True)})
bucket = zarro.model('bucket', {'bucket': fields.String(description='Nombre del bucket', example='desa-ocp-jmeter', required=True)})
##################################
# MODELOS
del_pods_label = zarro.inherit('Borrado de pods por label', ambiente, project, label)
del_pods_name = zarro.inherit('Borrado de pods por nombre', cluster, project, name)
del_project = zarro.inherit('Borrado de projecto en Openshift', ambiente, name)
##################################