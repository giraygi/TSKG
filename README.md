# TSKG
- Set `TOKEN` by `export TOKEN=xxxxxxxx` to be able to extract data from matomo. Configure matomo statistics data with further parameters in the file.
- Choose the most frequently used ontologies based on their minimum number of actions in the given dates by `export MIN_ACTIONS=5000`. The default value is 5000.
- Choose the date to extract the most frequently used ontologies by `export DATE=last30`. The notation is based on Matomo API. The default value is last30 .
- Run the application by `docker compose up -d`
- Assign super user by `docker compose exec qlever-ui python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@admin.com','password')"`
- Run the UI of the SPARQL endpoint from: http://localhost:8176/ts and execute the following query to test `SELECT * WHERE { ?s ?p ?o } LIMIT 10`
- You can test the backend directly with a query like: curl "http://localhost:7001/?query=SELECT+*+WHERE+%7B+?s+?p+?o+%7D+LIMIT+10"
