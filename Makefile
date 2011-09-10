.PHONY: db run schema smtpd

db:
	rm -f db/muspy.db
	sqlite3 db/muspy.db < db/muspy.sql

run:
	./manage.py runserver

schema:
	sqlite3 db/muspy.db ".schema" > db/muspy.sql

smtpd:
	python -m smtpd -n -c DebuggingServer localhost:1025