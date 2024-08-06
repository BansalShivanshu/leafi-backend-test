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
1. Activate the virtual environment, if not already: `source venv/bin/activate`
1. Create new tables in DynamoDB and add table names to your env variables. follow the structure mentioned in [section](#database).
1. Create a new IAM Role in your AWS Account with the followin policies:
    1. `IAMUserChangePassword`
    1. `AmazonDynamoDBFullAccess`
    - Download the CSV in a secure location and configure your AWS CLI with the proper credentials.
1. Follow AWS CLI setup guide from this [guide](https://medium.com/@amiri.mccain/install-aws-cli-and-configure-credentials-and-config-files-on-a-mac-cda81cf64052)
1. Start the server using `./start-server.sh` or `make run-server`

#### Testing Instructions
1. One way to test would be by executing all the unit and integration tests implemented. You can do this by the following command: `make run-test`
1. Another way is playing around with the server itself. Following are the steps you can take. *Make sure the server is up and [running](#running-steps) before proceeding*.
    - Start off by testing the `subscribers` endpoint. Sample request:
    ```.zsh
    curl -X GET http://localhost:8000/subscribers/topic1
    ```
    This should return a 404 NOT FOUND Error saying Topic either does not exist or has no subscribed endpoints.
1. Let's create some subscriptions to this topic now.
    ```.zsh
    curl -X POST -H "Content-Type: application/json" -d '{ "url": "http://localhost:8000/event"}' http://localhost:8000/subscribe/topic1
    ```
    - This will create a new subscription between topic1 and the endpoint. Note that headers are a must in this request because the server accepts data in json format. If no headers are provided, server will return a `415 Media Not Supported Error`.
1. Now execute [second step](#testing-instructions) again. This will return the subscribers to this topic. Feel free to add more topics and subscriptions.
1. Note, invalid urls and topics will return a `Bad Request` error from the server. More edge cases are tested in unit tests found in `test/test_main.py`

#### Development and Contribution
- Use `run-format` command to make sure coding style remains consistent throughout the codebase.

#### Design
This section will discuss design choices made and implementation details as the project progresees.

*Note*: There is *no data persistence* at this time, i.e. if the server is exited, all estabilished subscriptions and messages will be lost.

*Note*: No pre-processing will be done with the messages. At this point of time, the system is *not responsible* for *message validation* and *sanitization*. All messages are delivered in an *AS-IS* condition.

- Endpoints: Following are the implementations of server endpoints
    - `localhost:8000/subscribers/{topic}`: This endpoint returns a list of subscribed urls to a given topic. If no such topic exists, it will return a http not found error. This endpoint is for debugging purposes only.
    - `localhost:8000/subscribe/{topic}`: This endpoint is responsible for establishing a subscription between a topic and url. URLs are validated before a subscription is created. Client is notified accordingly.
    - `localhost:8000/publish/{topic}`: This endpoint is responsible for pushing out messages to the subscribers of a given topic. Returns a list of subscribers that were not able to receive the message in real time. 
        - This is performed in a thread safe manner using `Message Broker`. Read more in section below.
    - `localhost:8000/event`:
        - `POST`: Endpoint follows a **pub-sub model**. Receives and displays pushed messages in real time.
        - `GET`: Endpoint follows a **polling model**. Retrieves all messages pushed while system was offline/unavailable.
    - `localhost:8000/toggle_post_event`: Endpoint allows toggling POST method on /event to mimic a real world scenario of subscriber being offline vs online.
- `SubscriptionManager`: This class is responsible for handling all subscriptions established.
    - `subscribe()`: returns true if mapping is adder or the endpoint already exists. This is done so that we only catch real failures of subscription creation.
    - Whitespaces are trimmed from Topics and Endpoints to ensure system integrity. _User might add spaces incorrectly and not realize_
    - Whitespaces in an endpoint are not filled with `%20` characters because this system does not actually send messages to an endpoint and urls are pre-urlified by curl and browsers.
    - At ths time no method exists to remove subscriptions. This is a design choice as is not required for POC and no real usage of this feature at the moment. This feature will be added once databases are involved helping create a real world product. This will also allow us to keep track of all previous subscribers of any topic. With a scalable product, this will allow us to get deeper insights and analytics on user behaviour, product usage. It will also help with security and legal compliance.
- `MessageBroker`: This class is responsible for handling message communication between publishers and subscribers.
    - Class is thread safe as the system allows for multiple publishers to perform actions at the same time.
    - Responsible for maintaining messages in memory that could not be sent successfully. (non-persistent data at this time).
    - Allows subscribers to poll for messages received when they were unavailable.
    - Responsible for real time publishing to subscribers.
        - **This requires a contract between us and the subscribers to:**
            - Subscriber url allows POST requests.
            - Subscriber endpoint sends relavent message and status codes back to the server while receiving messages.
            - _Check `/event` POST method implementation in `main` as an example._
            - ***Question: What is a good way of enforcing this contract?***
- `Validation.isValidUrl()`: This method is implemented to validate incoming URLs when creating new subscriptions. We're using a library called [Validators](https://validators.readthedocs.io/en/latest/#) and Regex patterns to achieve the goal.
    - From some research, this is quite a comprehensive url validator but only validates true urls. It also urls with IP addresses but fails with `localhosts`. Thus we implemented a regex patter as well.

Databases are not being used at this time for data persistence and log retention. These features will be added at a later time once a basic POC is complete.

#### Database
1. `v2.0` adds database to the service to allow for data persistence. Let's take a look at what the message data might look like in a table:
    ```
    timestamp | subscriber | message | is_received
    -------------------------------------------------
    utc.iso() |  "/event"  | { json } |    False
    ```
    This format avoids list creation, allowing for faster queries and sorting based on timestamps, or status of message being received.
1. Followin are some pros and cons being considered during this implmentation:
    - RDS (Postgres)
        - Pros:
            1. **ACID compliant**: This is very crucial for a messaging system such as this. Especially to ensure atomicity of operations, consistency with concurrency and larger scale (globally).
            1. Hgihly performant with joins and queries, and allows for a ridgit strucutre of the data.
        - Cons:
            1. **Scaling**: SQL databases typically scale up which can be slow and cost-ineffective.
    - DynamoDB (NoSQL)
        - Pros:
            1. Flexible structure as NoSQL doesn't demand a pre-defined table schema. But strucutre must be maintained in code.
            1. **Highly Scalable and Cost Effective**: DynamoDB easily scales out as the system grows while remaining cost effective.
            1. DynamoDB transactions are ACID compliant IN A REGION AND ACCROSS ONE OR TWO TABLES. Read more [here](https://aws.amazon.com/dynamodb/features/#:~:text=Yes%2C%20Amazon%20DynamoDB%20transactions%20are,single%20AWS%20account%20and%20region.)
        - Cons:
            1. **Eventful Consistency**: At large scale, dynamoDB does become eventfully consistent. This can be bad for a system such as this because knowing the state of a message is critical in deciding if it should be queued to send.
                - Although DynamoDB offers guarenteed consistency reads (when requested explicitly), it can cost more and have an increased delay with a growing system.
1. **Conclusion**: If the data, specifically the message body, lacks a pre-defined structure then DynamoDB is a good choice as it is cost effective and scalable. These are crucial for any large scale system. This coupled with its ability to offer ACID principles (at a smaller scale) is quite a strong choice. Thus, this project implements DynamoDB for message handling.

**Note**: For a system intended to be used for a service such as **NOVA** by leafi, DynamoDB could be a better choice as the devices are localized do not frequent multiple concurrent transactions.

**Note**: Current database for message management is implemented with DynamoDB, intending for a system such as NOVA. Ideally this must be done with IaC with AWS CDK but given time boundaries, this is being skipped. Following are the table names:
1. `pub-sub-messages`: current prod environment
1. `pub-sub-messages-test`: current dev/testing environment

**DynamoDB Strcture**:
- **subscriber (String)**: This is the subscriber url, `http://localhost:8000/event` for example.
- **timestamp (String)**: This is the timestamp generated at the time of receiving the publish request. It follows the UTC ISO Format. example: `2024-08-04T12:00:00+00:00`


#### Next Steps
1. Implement a true server to allow for real time pub-sub model. Can be accomplished using cloud services.
    - This can be accomplished by using EC2 for server hosting, or lambdas for `/publish` and `/subscribe` events. 
    - In a large scale system we would want this to be regionalized. 
    - Both have pros and cons, especially in terms of scalability, security, availability, concurrency, and costs incurred by us.
    - For cloud POC start with lambdas.
1. Persist data in a centralized database. Ideally by regions, but given the small scope of this application at this time, we only need one centralized database.
    - Maintain state - if a message is sent successfully or not. This adds challanges such for handling errors, concurrency, and packet/data losses.
1. Maintain logs
    - Adds log retention for a certain amount of time
    - Helps maintain a well documented use of the service
    - Allows setting up alarms and pages in case of failures
    - Can be beneficial in setting up dashboards and being regulatorily compliant.
1. Add rate limiting 
    - Highly system dependent. Some possible implementations could be as follows:
        - Limit the number of messages that can be sent to a topic per minute. This considers clients being bombarded with messages and helps prevent potential `D/DOS attacks`. Should be configured by the subscriber themselves - ***what is the acceptable rate of messages for you?***
        - Limit message queue backlog for unavailable subscribers. This ensures efficient resource use, helps prevents our system from abuse and attacks, high costs, and scalability issues.
        - For Rate Limiting POC, start with IP bans and timeouts.
1. Add authentication - this prevents a bad actor to subscribe someone without their knowledge.
    - Some ways of achieving this would be
        - JWT tokens
        - User accounts
1. Allow message purging. This is useful for subscribers that were not able to receive messages. Consider a real world scenario where an application comes online and fetches X messages. This will cause them to perform all the operations that were pushed while offline.
    - Depends on the subscriber and the system they're trying to build. For a critical system that must perform all actions requested - irrespective of server state - we do not want purging. This could be a very sensative/crucial implementation but must be handled carefully. Eg: Life critical systems in hospitals, financial transaction machines, etc..
    - But for a system such as a music player or NOVA by Leafi, we would not want to fulfill requests received while offline.
    - Highly client dependent, but a crusial functionality to offer.
    - This functionality must be implemented with authentication and security.
