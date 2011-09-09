.PHONY: db run schema

db:
	rm -f db/muspy.db
	sqlite3 db/muspy.db < db/muspy.sql

run:
	./manage.py runserver

schema:
	sqlite3 db/muspy.db ".schema" > db/muspy.sql
