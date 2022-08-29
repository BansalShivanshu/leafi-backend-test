# Leafihome backend programming test

For this challenge we'll be recreating a pub / sub system using HTTP requests. **Feel free to use whatever langauges or frameworks you wish.**

Publisher Server Requirements
Setting up a subscription
<pre><code>
POST /subscribe/{TOPIC}
BODY { url: "http://localhost:8000/event"}
</code></pre>

The above code would create a subscription for all events of {TOPIC} and forward data to <code>http://localhost:8000/event </code>
Publishing an event
<pre><code>
POST /publish/{TOPIC}
BODY { "message": "hello"}
</code></pre>

The above code would publish on whatever is passed in the body (as JSON) to the supplied topic in the URL. This endpoint should trigger a forwarding of the data in the body to all of the currently subscribed URL's for that topic.

Testing it all out Publishing an event
<pre>
<code>$ ./start-server.sh </code>
<code>$ curl -X POST -d '{ "url": "http://localhost:8000/event"}' http://localhost:8000/subscribe/topic1</code>
<code>$ curl -X POST -H "Content-Type: application/json" -d '{"message": "hello"}' http://localhost:8000/publish/topic1</code>
</pre>     
The above code would set up a subscription between topic1 and <code> http://localhost:8000/event </code>.
When the event is published in line 3, it would send both the topic and body as JSON to http://localhost:8000

The <code>/event</code> endpoint is just used to print the data and verify everything is working.

![alt text](/images/pubsub-diagram.png)
