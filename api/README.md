# muspy API documentation

A draft specification of the muspy API.

Use `http://muspy.com/api/1/<resource>`. Unless otherwise noted, requests must
be authenticated using HTTP basic authentication.

Default output format is json, you can change it to xml by adding `?format=xml`
to the request URL. POST/PUT parameters should be sent as form data.

## Resources

* `artist/<mbid>`
    * GET: artist info, no auth

* `artists/<userid>[/<mbid>]`
    * GET: list of all artists for the user (mbid, name, sort_name,
      disambiguation)
    * PUT: follow a new artist, return the artist info
        * mbid
    * DELETE: unfollow an artist, `<mbid>` is required

* `release/<mbid>`
    * GET: release group info (artist, mbid, name, type, date), no auth

* `releases[/<userid>]`
    * GET: list of release groups, sorted by release date. If `<userid>` is not
      supplied, the call will return release groups starting from today for all
      artists and the user's release type filters won't apply. No auth.
        * limit: max 100
        * offset
        * mbid: optional artist mbid, if set filter by this artist.

* `user[/<userid>]`
    * GET: return user info and settings, `<userid>` is optional, auth is not.
    * POST: create and return a new user, no auth
        * email
        * password
        * activate: 1 to send an activation email
    * PUT: update user info and settings
    * DELETE: delete the user and all their data

The API is quite new and will probably change in the coming weeks. I suggest
that you [subscribe][0] to [the blog][1] where such changes will be announced.

If you are going to use the API for commercial purposes (e.g. selling CDs or ads
on the pages where the main content is pulled from the muspy API) I expect a 50%
revenue share. Alternatively, you can donate these money to [MusicBrainz][2],
[Django][3] or [FreeBSD][4]. If you are a [free software][5] project, feel free
to use the API as you see fit.

[0]: http://versia.com/category/muspy/feed/atom/
[1]: http://versia.com/category/muspy/
[2]: http://metabrainz.org/donate/
[3]: https://www.djangoproject.com/foundation/donate/
[4]: http://www.freebsdfoundation.org/donate/
[5]: http://www.gnu.org/philosophy/free-sw.html
