from jobclient import app
import json
import requests
from flask import (redirect, render_template, request, url_for)
import uuid


@app.route('/',methods=['GET'])
def index():
    return redirect(url_for('home'))

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.jinja2')

@app.route('/activate',methods=['GET'])
def activate():
    endpoints = []
    
    if request.args.get('e1id'):
        endpoints.append((request.args.get('e1id'), request.args.get('e1name')))
    if request.args.get('e2id'):
        endpoints.append((request.args.get('e2id'), request.args.get('e2name')))
    if request.args.get('e3id'):
        endpoints.append((request.args.get('e3id'), request.args.get('e3name')))
    
    return render_template('activate.jinja2',endpoints=endpoints)

@app.route('/submitTransfer',methods=['POST'])
def submitTransfer():
   
    data = {
        'stage_in_source':request.form['stage_in_source'],
        'stage_out_destination':request.form['stage_out_destination'],
        'stage_in_destination':request.form['stage_in_destination']
    } 

    requests.post("http://localhost:8081/api/submitjobspecs",data=data)

    return '200'



@app.route('/status',methods=['GET'])
def check_status():
    
    temp=request.args.get("taskid")
    wait = request.args.get("wait")
    taskcolor = request.args.get("taskcolor")
    print('taskid is')
    print(taskcolor)
    return render_template('status.jinja2',taskid=temp,wait=wait,taskcolor=taskcolor)
