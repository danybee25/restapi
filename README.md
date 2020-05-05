# RESTAPI

## Description

- Exposes a POST method that takes a payload as and that returns a json. 

- Manages and logs run-time errors that can be found in the process of running the application. 

## Running project without docker

    python restapi.py

## Launch with docker

- Build the dockerfile

        docker build . -t restapi

- Run the dockerfile

        docker run -it -p 5000:5000  -v /home/ed/Documents/devpersonnel/restapi/restapi.log:/app/restapi.log restapi