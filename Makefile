.PHONY: schema run

run:
	./manage.py runserver

schema:
	sqlite3 db/muspy.db ".schema" > db/muspy.sql
