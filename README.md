# flask-zipkin

a flask zipkin extesion based on py_zipkin.

## Installation

```bash
pip install flask_zipkin
```

## usage

you can simply use it as other flask extensions.

```python
from flask_zipkin import Zipkin

zipkin = Zipkin(sample_rate=10)
zipkin.init_app(app)
```

## Advance Usage

you could gen a header to pass it to other services, the downstream service will recieve this header.

```
@bp.route('/')
def hello():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    r = requests.get('http://localhost:5001', headers=headers)
    return r.text
```



`flask_zipkin` will use http transport by default. You could define a transport, like:

```python
@zipkin.transport_handler
def default_handler(self, encoded_span):
    body = str.encode('\x0c\x00\x00\x00\x01') + encoded_span
    return requests.post(
		'your transport dsn',
        data=body,
        headers={'Content-Type': 'application/x-thrift'},
)
```


`flask_zipkin` eats all transport exception by default. You could define an exception handler, like:

```python
@zipkin.transport_exception_handler
def default_ex_handler(self, ex):
    raise ex
```

and also, you could exempt some views, like:

```python
@zipkin.exempt
@bp.route('/')
def hello():
    return 'hello world'
```

add key, value for your tracing record, like:

```python

zipkin.logging(id=1, user_id=2)

```



## app configs

`ZIPKIN_DISABLE`  disable zipkin tracking if value is `True`

`ZIPKIN_DSN`  http transport dsn: such as `http://localhost:9411/api/v1/spans`

`ZIPKIN_SAMPLE_RATE` traced requests percentage from 0 to 100

`ZIPKIN_IGNORED_ENDPOINTS` list of endpoints that should not be traced, e.g. `["static"]`
