# Run code
uwsgi --master --single-interpreter --protocol=http --workers 4 --gevent 100 --socket 0.0.0.0:9198 --module patched:app
