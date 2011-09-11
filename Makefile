.PHONY: db run smtpd

db:
	rm -f db/muspy.db
	sqlite3 db/muspy.db < db/muspy.sql

run:
	./manage.py runserver

smtpd:
	python -m smtpd -n -c DebuggingServer localhost:1025
