from setuptools import setup


setup(
    name='fl-flask-zipkin',
    version='0.0.5',
    url='',
    license='BSD',
    author='killpanda',
    author_email='angus@killpanda.de',
    description='An zipkin extension for Flask based on py_zipkin.',
    py_modules=['flask_zipkin'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'py_zipkin>=0.4.0',
        'requests>=2.11.1',
        ]
)
