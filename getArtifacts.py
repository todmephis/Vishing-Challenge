import boto3
import json
import time
from tqdm import tqdm
from threading import Thread, Event
region = 'us-east-2'

def get_aws_credentials(identity_pool_id):
   # Configurar el cliente de Cognito Identity
   identity_client = boto3.client('cognito-identity', region_name=region)
   # Obtener un ID de identidad para un usuario no autenticado
   response = identity_client.get_id(
       IdentityPoolId=identity_pool_id
   )
   identity_id = response['IdentityId']
   # Obtener credenciales temporales para el usuario no autenticado
   response = identity_client.get_credentials_for_identity(
       IdentityId=identity_id
   )
   return response['Credentials']
def invoke_lambda(function_name, credentials):
    try:
        # Configurar el cliente de Lambda con las credenciales temporales
        lambda_client = boto3.client(
            'lambda',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region
        )
        # Invocar la función Lambda
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse'
        )
        # Leer y retornar la respuesta de Lambda
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        if response['StatusCode'] == 200:
            data = json.loads(response_payload['body'])
            return data['secrets'], data['scenarios']
        else:
            print(f"Error: {response_payload}")
            return None, None
    except Exception as e:
        print(f"Excepción durante la invocación de Lambda: {e}")
        return None, None
def update_progress_bar(pbar, stop_event):
   while not stop_event.is_set():
       time.sleep(0.1)
       pbar.update(1)
def getScriptArtifacts(identity_pool_id, function_name):
    # Obtener credenciales de AWS desde el Identity Pool
    credentials = get_aws_credentials(identity_pool_id)
    # Configurar y empezar la barra de progreso
    pbar = tqdm(total=100, desc="Downloading script artifacts...")
    stop_event = Event()
    # Iniciar un hilo para actualizar la barra de progreso
    progress_thread = Thread(target=update_progress_bar, args=(pbar, stop_event))
    progress_thread.start()
    # Obtener las API keys y el archivo JSON desde Lambda
    try:
        api_keys, scenarios = invoke_lambda(function_name, credentials)
    finally:
        stop_event.set()
        # Esperar a que el hilo de progreso termine
        progress_thread.join()
        pbar.close()
    if api_keys and scenarios:
    # Usar las API keys y el archivo JSON en tu script
        return api_keys, scenarios
        #print("API keys y JSON obtenidos exitosamente")
        #print("API keys:", api_keys)
        #print("JSON:", scenarios)
    else:
        print("Error retrieving script artifacts")
        print("Bye...")
        exit(1)