# muspy

[muspy](http://muspy.com) is an album release notification service.

## Development

To set up development environment you need to install these dependencies:

* On FreeBSD: `portmaster databases/sqlite3 graphics/py-imaging www/nginx www/py-django www/py-django-piston`
* On Debian: `aptitude install sqlite3 python-imaging nginx python-django python-django-piston`

Edit your main `nginx.conf`:

    http {
        ...
        include /path/to/muspy/nginx.conf;
    }

Update the project location in `muspy/nginx.conf` and restart nginx.

Add this line to your `/etc/hosts`:

    127.0.0.1  muspy.dev

Go to the project directory and run `make db` to create an empty database.

Type `make run` and go to <http://muspy.dev/>. If static files don't load make
sure nginx has rx permissions for the `muspy/static` directory.
