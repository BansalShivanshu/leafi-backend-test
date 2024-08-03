# Leafihome backend programming test

For this challenge we'll be recreating a pub / sub system using HTTP requests. **Feel free to use whatever langauges or frameworks you wish.**

### Publisher Server Requirements

#### Setting up a subscription
```
POST /subscribe/{TOPIC}
BODY { url: "http://localhost:8000/event"}
```

The above code would create a subscription for all events of {TOPIC} and forward data to `http://localhost:8000/event`

#### Publishing an event
```
POST /publish/{TOPIC}
BODY { "message": "hello"}
```

The above code would publish on whatever is passed in the body (as JSON) to the supplied topic in the URL. This endpoint should trigger a forwarding of the data in the body to all of the currently subscribed URL's for that topic.

Testing it all out Publishing an event
```
$ ./start-server.sh
$ curl -X POST -d '{ "url": "http://localhost:8000/event"}' http://localhost:8000/subscribe/topic1
$ curl -X POST -H "Content-Type: application/json" -d '{"message": "hello"}' http://localhost:8000/publish/topic1
```

The above code would set up a subscription between topic1 and `http://localhost:8000/event`
When the event is published in line 3, it would send both the topic and body as JSON to `http://localhost:8000`

The `/event` endpoint is just used to print the data and verify everything is working.

![alt text](/images/pubsub-diagram.png)


### Project Workflow
Please note that the following steps are setup to run on a linux based environment. Running on a Windows system would require small tweeks in `start-server.sh` and `Makefile`'s `run-install`.

#### Running Steps
1. Run the installer using `make run-install`
1. Start the server using `./start-server.sh`

#### Development
- Use `run-format` command to make sure coding style remains consistent throughout the codebase.
