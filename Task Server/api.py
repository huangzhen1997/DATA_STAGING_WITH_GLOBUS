from task_server import app, redis_store,celery, bp, socketio
import requests
import random,string
from flask import (abort, flash, redirect, render_template, request,
                   session, url_for, current_app) 

from flask_socketio import send, emit, SocketIO

import globus_sdk
from globus_sdk import (TransferClient, TransferAPIError,
                        TransferData, RefreshTokenAuthorizer, LocalGlobusConnectPersonal)

from globus_sdk import TransferClient, LocalGlobusConnectPersonal

import subprocess

import json

import sys

import time

import dill

from celery import Celery

import os

import random

from celery.exceptions import Reject

import uuid

import randomcolor




@celery.task(bind=True)
def pre_job(self,tokens,my_id,task_color):
  
    auth_client = dill.loads(redis_store.get('auth_client'))

    task_id = my_id

    print('task id is' + task_id)        
    
    validate = auth_client.oauth2_validate_token(tokens['transfer.api.globus.org']['access_token'])
    
    output=validate['active']

    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      The transfer access token now '+ ('is' if output else 'not') + ' active after user login.','task_id':task_id,'step':'1', 'task_color':task_color}))

    auth_client.oauth2_revoke_token(tokens['transfer.api.globus.org']['access_token'])
    
    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Now revoking the transfer access token to simulate token expiration due to long queue wait','task_id':task_id,'step':'1','task_color':task_color}))

    validate = auth_client.oauth2_validate_token(tokens['transfer.api.globus.org']['access_token'])

    output=validate['active']

    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      The transfer access token is now  '+ ('' if output else 'in') + 'active.','task_id':task_id,'step':'1','task_color':task_color}))


@bp.route('/messenger', methods=['POST'])
def messenger():

    task_color = request.get_json().get('task_color')

    if(request.get_json().get('key_message')):
        result=request.get_json()['key_message']
        task_id = request.get_json().get('task_id')
        
        
        auth_client = dill.loads(redis_store.get('auth_client'))
        validate = auth_client.oauth2_validate_token(result)
        
        output=validate['active']
        
        redis_store.set('to_expire',result)
        
        if(output):
           
            socketio.emit('message', {'log':'['+(task_id if task_id else '')+']       The transfer access token now is active after using refresh_token', 'task_id':task_id,'step':request.get_json()['step'], 'task_color':task_color}) 
        else:
            
            socketio.emit('message', {'log':'['+(task_id if task_id else '')+']       The transfer access token now is still inactive','step':request.get_json()['step'],'task_color':task_color}) 
    else:
        
        socketio.emit('message', {'log':request.get_json()['message'],'step':request.get_json()['step'],'task_color':task_color})  


    

    return '200'


@celery.task(bind=True)
def do_job(self,tokens, task_color,stage_in_source,stage_in_dest,stage_out_dest,stage_in_source_path,stage_in_dest_path,stage_out_dest_path):

    def post_refresh_message(token_data):
        print("I got called")
        requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'key_message':token_data.by_resource_server['transfer.api.globus.org']['access_token'], 'task_id':task_id,'step':'1','task_color':task_color}))


    #socketio.emit('message_log', {'message_body':'Testing for emit'})

    auth_client = dill.loads(redis_store.get('auth_client'))

    #send json message with key special_message that include new access token
    #requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'key_message':token_data.by_resource_server['transfer.api.globus.org']['access_token'], 'task_id':task_id}
    authorizer = globus_sdk.RefreshTokenAuthorizer(tokens['transfer.api.globus.org']['refresh_token'], auth_client,tokens['transfer.api.globus.org']['access_token'], expires_at=tokens['transfer.api.globus.org']['expires_at_seconds'],on_refresh=post_refresh_message)

    #stage_in_source = stage_in_source
    stage_in_destination= stage_in_dest
    stage_out_destination = stage_out_dest
    
    #stage_in_source_path = redis_store.get('stage_in_source_path').decode('utf-8')
    stage_in_destination_path = stage_in_dest_path
    stage_out_destination_path = stage_out_dest_path
    task_id = do_job.request.id


    tc = TransferClient(authorizer=authorizer)   
   

    #auth_client=load_auth_client()


    data = globus_sdk.TransferData(tc,stage_in_source, stage_in_destination,label="stagein")

    data.add_item(stage_in_source_path, stage_in_destination_path, True)
    
    status = tc.submit_transfer(data)

    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']Queue wait is done, now initiating Stage in....','task_id':task_id,'step':'2','task_color':task_color}))

    tc.task_wait(status["task_id"])#task id of the stage_in


    result_in=tc.get_task(status["task_id"])
    #print("The response for task is :")
    #print(result_in)

    complete_status = result_in['status']
    print("The complete status is :")
    print(complete_status)

    if complete_status == "SUCCEEDED":
        requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Stage In succeeded', 'task_id':task_id,'step':'2','task_color':task_color}))

    else:
        requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Stage In failed, canceling the job..... ','task_id':task_id,'step':'2','task_color':task_color}))
        # stop and delete the job
        raise Reject("Stage in Failed",requeue=False)

   

    

    #print to the log that job informations, with id, running the fake job
    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']Running the job','task_id':task_id,'step':'3','task_color':task_color}))
    
    time.sleep(3)

    #fetching new token
    #validate now active 


    #fake job is done
    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']Job is done','task_id':task_id,'step':'3','task_color':task_color}))


    requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Initiating Stage out.... ','task_id':task_id,'step':'4','task_color':task_color}))

    
    #tc = TransferClient(authorizer=authorizer)   

    data = globus_sdk.TransferData(tc, stage_in_destination, stage_out_destination,label="stageout")

    data.add_item(stage_in_destination_path, stage_out_destination_path, True)

    #hopefully refresh token lambda called here or after here supposed to log refreshed ok
    status = tc.submit_transfer(data)

    
    tc.task_wait(status["task_id"])


    result_in=tc.get_task(status["task_id"])

    complete_status = result_in['status']

    if complete_status == "SUCCEEDED":
        requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Stage Out succeeded ','task_id':task_id,'step':'4','task_color':task_color}))

    else:
        requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'['+task_id+']      Stage Out failed, canceling the job.....','task_id':task_id,'step':'4','task_color':task_color}))
        raise Reject("Stage out Failed",requeue=False)



@bp.route('/authcallback', methods=['GET'])
def authcallback():
    
    def test_func(token_data):
        print('this is a test')
    
    """Handles the interaction with Globus Auth."""
    # If we're coming back from Globus Auth in an error state, the error
    # will be in the "error" query string parameter.
    if 'error' in request.args:
        print('error')
        return redirect(url_for('task_server.transfer'))

    # Set up our Globus Auth/OAuth2 state
    redirect_uri = url_for('task_server.authcallback', _external=True) 

    client = globus_sdk.ConfidentialAppAuthClient(
        app.config['TS_CLIENT_ID'], app.config['TS_CLIENT_SECRET'])
    client.oauth2_start_flow(redirect_uri, refresh_tokens=True) #let globus know where to go back to

    # If there's no "code" query string parameter, we're in this route
    # starting a Globus Auth login flow.
    if 'code' not in request.args:
        additional_authorize_params = (
            {'signup': 1} if request.args.get('signup') else {})


        auth_uri = client.oauth2_get_authorize_url(
            additional_params=additional_authorize_params)

        return redirect(auth_uri, code=307)
    else:
        # If we do have a "code" param, we're coming back from Globus Auth
        # and can start the process of exchanging an auth code for a token.
        

        #requests.post('http://localhost:8081/api/messenger', headers={'content-type': 'application/json'},data=json.dumps({'message':'User logged in....'}))

        code = request.args.get('code')
        tokens = client.oauth2_exchange_code_for_tokens(code)
        id_token = tokens.decode_id_token(client)
    
        
        session.update( 
            tokens=tokens.by_resource_server,
            is_authenticated=True,
            name=id_token.get('name', ''),
            email=id_token.get('email', ''),
            institution=id_token.get('institution', ''),
            primary_username=id_token.get('preferred_username'),
            primary_identity=id_token.get('sub'),
        )

        tokens = session['tokens']
        

        stage_in_source = redis_store.get('stage_in_source').decode('utf-8')
        stage_in_destination = redis_store.get('stage_in_destination').decode('utf-8')
        stage_out_destination = redis_store.get('stage_out_destination').decode('utf-8')
        new_token=None
        
        authorizer = globus_sdk.RefreshTokenAuthorizer(tokens['transfer.api.globus.org']['refresh_token'],globus_sdk.ConfidentialAppAuthClient(app.config['TS_CLIENT_ID'], app.config['TS_CLIENT_SECRET']),tokens['transfer.api.globus.org']['access_token'],expires_at=1,on_refresh=test_func)
        
        
        #authorizer = globus_sdk.AccessTokenAuthorizer(tokens['transfer.api.globus.org']['access_token'])
        tc = TransferClient(authorizer=authorizer) 



        a = tc.endpoint_autoactivate(stage_in_source, if_expires_in=3600)
        b = tc.endpoint_autoactivate(stage_in_destination, if_expires_in=3600)
        c = tc.endpoint_autoactivate(stage_out_destination, if_expires_in=3600)
        if a["code"] == "AutoActivationFailed" or b["code"] == "AutoActivationFailed" or c["code"] == "AutoActivationFailed":
            stage_in_source_response = tc.get_endpoint(stage_in_source)
            stage_in_destination_response = tc.get_endpoint(stage_in_destination)
            stage_out_destination_response = tc.get_endpoint(stage_out_destination)

            e1name = stage_in_source_response["display_name"]
            e2name = stage_in_destination_response["display_name"]
            e3name = stage_out_destination_response["display_name"]
            
            return redirect("http://localhost:8080/activate?e1id="+ (stage_in_source if a["code"] == "AutoActivationFailed" else "")+("&e1name="+e1name if a["code"] == "AutoActivationFailed" else "")+"&e2id="+ (stage_in_destination if b["code"] == "AutoActivationFailed" else "")+("&e2name="+e2name if a["code"] == "AutoActivationFailed" else "" )+"&e3id="+(stage_out_destination if c["code"] == "AutoActivationFailed" else "")+"e3id&e3name="+(e3name if c["code"] == "AutoActivationFailed" else ""))
    



        # read from db here 

        sis=redis_store.get('stage_in_source').decode('utf-8')
        sid=redis_store.get('stage_in_destination').decode('utf-8') #...
        sod=redis_store.get('stage_out_destination').decode('utf-8')#those names...........
        siop= redis_store.get('stage_in_source_path').decode('utf-8')
        sidp = redis_store.get('stage_in_destination_path').decode('utf-8')
        sodp = redis_store.get('stage_out_destination_path').decode('utf-8')

        
        return redirect(url_for('task_server.transfer', stage_in_source=sis,stage_in_dest=sid,stage_out_dest=sod,stage_in_source_path=siop,stage_in_dest_path=sidp,stage_out_dest_path=sodp))

@bp.route('/submitjobspecs',methods=["POST"])
def submitjob():
    
    form = request.form


    stage_in_src = form.get('stage_in_source').split('||')
    stage_in_dest = form.get('stage_in_destination').split('||')
    stage_out_dest = form.get('stage_out_destination').split('||')
    

    # endpoint uuid's
    redis_store.set('stage_in_source', stage_in_src[0])
    redis_store.set('stage_out_destination',stage_out_dest[0])
    redis_store.set('stage_in_destination',stage_in_dest[0])

    #paths
    redis_store.set('stage_in_source_path', stage_in_src[1])
    redis_store.set('stage_out_destination_path',stage_out_dest[1])
    redis_store.set('stage_in_destination_path',stage_in_dest[1])

    return '200'

@bp.route('/transfer',methods=["GET"])
def transfer():








    #read from authcallback
    stage_in_source = request.args.get('stage_in_source')
    stage_in_dest= request.args.get('stage_in_dest')
    stage_out_dest= request.args.get('stage_out_dest')
    stage_in_source_path= request.args.get('stage_in_source_path')
    stage_in_dest_path = request.args.get('stage_in_dest_path')
    stage_out_dest_path= request.args.get('stage_out_dest_path')

    tokens=session['tokens']

    redis_store.set('auth_client',dill.dumps(load_auth_client()))     
    
    #redis_store.set('authorizer',dill.dumps(authorizer))        
    countdowntime = random.randint(5,10)

    new_id = str(uuid.uuid1())


    task_color = randomcolor.RandomColor().generate(hue="random", luminosity="light")[0]


    other = (pre_job.apply_async(args=[session['tokens'],new_id,task_color] ,countdown=float(countdowntime-3))).id
    

    task_id = (do_job.apply_async(args=[session['tokens'],task_color],kwargs={'stage_in_source':stage_in_source, 'stage_in_dest':stage_in_dest, 'stage_out_dest':stage_out_dest, 'stage_in_source_path':stage_in_source_path, 'stage_in_dest_path':stage_in_dest_path,'stage_out_dest_path':stage_out_dest_path}, countdown=float(countdowntime),task_id=new_id)).id


    print("test")

    return redirect('http://localhost:8080/status?'+"taskid="+task_id+"&wait="+str(countdowntime)+"&taskcolor="+task_color[1:])


def load_auth_client():
    """Create a Globus Auth client from config info"""
    return globus_sdk.ConfidentialAppAuthClient(
        app.config['TS_CLIENT_ID'], app.config['TS_CLIENT_SECRET'])
   

#ddb59aef-6d04-11e5-ba46-22000b92c6ec||/~/Twitter/

#097b8756-83fd-11e8-9536-0a6d4e044368||/~/Desktop/Testing/Twitter

#ddb59af0-6d04-11e5-ba46-22000b92c6ec||/~/Twitter

#celery worker -A task_server.celery --loglevel=INFO

#celery flower -A task_server.celery

#./redis-server ../redis.conf

#source tutorial-env/bin/activate