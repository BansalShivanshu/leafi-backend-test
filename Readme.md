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

#### Development and Contribution
- Use `run-format` command to make sure coding style remains consistent throughout the codebase.

#### Design
This section will discuss design choices made and implementation details as the project progresees.

*Note*: There is *no data persistence* at this time, i.e. if the server is exited, all estabilished subscriptions and messages will be lost.

*Note*: No pre-processing will be done with the messages. At this point of time, the system is *not responsible* for *message validation* and *sanitization*. All messages are delivered in an *AS-IS* condition.

- Endpoints: Following are the implementations of server endpoints
    - `localhost:8000/subscribers/{topic}`: This endpoint returns a list of subscribed urls to a given topic. If no such topic exists, it will return a http not found error. This endpoint is for debugging purposes only.
    - `localhost:8000/subscribe/{topic}`: This endpoint is responsible for establishing a subscription between a topic and url. URLs are validated before a subscription is created. Client is notified accordingly.
- `SubscriptionManager`: This class is responsible for handling all subscriptions established.
    - `subscribe()`: returns true if mapping is adder or the endpoint already exists. This is done so that we only catch real failures of subscription creation.
    - Whitespaces are trimmed from Topics and Endpoints to ensure system integrity. _User might add spaces incorrectly and not realize_
    - Whitespaces in an endpoint are not filled with `%20` characters because this system does not actually send messages to an endpoint and urls are pre-urlified by curl and browsers.
- `Validation.isValidUrl()`: This method is implemented to validate incoming URLs when creating new subscriptions. We're using a library called [Validators](https://validators.readthedocs.io/en/latest/#) and Regex patterns to achieve the goal.
    - From some research, this is quite a comprehensive url validator but only validates true urls. It also urls with IP addresses but fails with `localhosts`. Thus we implemented a regex patter as well.
