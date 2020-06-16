# Globus with REST API Data Staging

# Environment :


* Recommended environment is Python 3.6 
* Other package to download for pythons are: 
    ## flower: 
    >pip install flower

    ## celery:
    >pip install celery

    ## Redis Database:
    1. >$ wget http://download.redis.io/releases/redis-4.0.11.tar.gz

    2. >$ tar xzf redis-4.0.11.tar.gz

    3. >$ cd redis-4.0.11
    4. >$ make


# Running :
1. To run the project, users have to first run two servers seperately

* Inside Job Client folder: run run_jobclient.py 

* the other one is task_server.py in Task Server folder.

* Then there are two more components which will be working with our REST API: Redis Database, Flower, and Celery job scheduler. Installing instructions are above:

* You should install flower and celery under Task Server folder

> Celery :  $  celery worker -A task_server.celery --loglevel=INFO       

> Flower:  $ celery flower -A task_server.celery


    
> Then start the Redis Database by : $ ./redis-server ../redis.conf

## Then you are good to go.


* To submit the job, you will go to your browser and type http://localhost:8080

* You will be redirected to login to your Globus account to give the consensus to Job Client

* Once your done that the Jinja template file will be loaded and you can then type your staging url

    > Url:  Globus Endpoint ID + || + File Directory

    
    #####  "ddb59aef-6d04-11e5-ba46-22000b92c6ec||/~/Twitter/"  represents ddb59aef-6d04-11e5-ba46-22000b92c6ec, one of my Globus endpoint, and /~/Twitter/ is the file's path I want to staging

## Login once, no more user intervention

We used Refresh Token to get the new access token if the old acces token expired, so the user will only be asked to authenticated for once, before stage in starts.


## Feel free to shoot an email if there are any questions:


* Zhen Huang, zhuang38@hawk.iit.edu

* Blake Ehrenbeck, behrenbe@hawk.iit.edu