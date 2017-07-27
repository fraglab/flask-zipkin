from flask import g, request

import requests
from py_zipkin import zipkin
from py_zipkin.util import generate_random_64bit_string


class Zipkin:
    def __init__(self, app=None):
        self.app = app
        self._disable = False
        self._ignored_endpoints = set()
        self._sample_rate = 100
        if app is not None:
            self.init_app(app)
        self._transport_handler = None
        self._transport_exception_handler = None

    def default_exception_handler(self, ex):
        pass

    def default_handler(self, encoded_span):
        try:
            body = str.encode('\x0c\x00\x00\x00\x01') + encoded_span
            return requests.post(
                self.app.config.get('ZIPKIN_DSN'),
                data=body,
                headers={'Content-Type': 'application/x-thrift'},
                timeout=1,
            )
        except Exception as e:
            if self._transport_exception_handler:
                self._transport_exception_handler(e)
            else:
                self.default_exception_handler(e)

    def transport_handler(self, callback):
        self._transport_handler = callback
        return callback

    def transport_exception_handler(self, callback):
        self._transport_exception_handler = callback
        return callback

    def init_app(self, app):
        self.app = app

        app.before_request(self._before_request)
        app.after_request(self._after_request)

        self._disable = app.config.get('ZIPKIN_DISABLE', app.config.get('TESTING', False))
        self._sample_rate = app.config.get('ZIPKIN_SAMPLE_RATE', 100)
        self._ignored_endpoints.update(app.config.get('ZIPKIN_IGNORED_ENDPOINTS', []))

        return self

    def _before_request(self):
        if self._disable or request.endpoint in self._ignored_endpoints:
            return

        headers = request.headers
        trace_id = headers.get('X-B3-TraceId') or generate_random_64bit_string()
        parent_span_id = headers.get('X-B3-Parentspanid')
        is_sampled = str(headers.get('X-B3-Sampled') or '0') == '1'
        flags = headers.get('X-B3-Flags')

        zipkin_attrs = zipkin.ZipkinAttrs(
            trace_id=trace_id,
            span_id=generate_random_64bit_string(),
            parent_span_id=parent_span_id,
            flags=flags,
            is_sampled=is_sampled,
        )

        handler = self._transport_handler or self.default_handler

        span = zipkin.zipkin_span(
            service_name=self.app.name,
            span_name='{0}.{1}'.format(request.endpoint, request.method),
            transport_handler=handler,
            sample_rate=self._sample_rate,
            zipkin_attrs=zipkin_attrs
        )
        g.zipkin_span = span
        g.zipkin_span.start()

    def _after_request(self, response):
        if not self._disable and hasattr(g, 'zipkin_span'):
            g.zipkin_span.stop()
        return response

    def create_http_headers_for_new_span(self):
        if self._disable:
            return dict()
        return zipkin.create_http_headers_for_new_span()

    @staticmethod
    def logging(**kwargs):
        if hasattr(g, 'zipkin_span') and g.zipkin_span and g.zipkin_span.logging_context:
            g.zipkin_span.logging_context.binary_annotations_dict.update(
                kwargs)
