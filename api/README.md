# muspy API documentation

A draft specification of the muspy API.

Use `http://muspy.com/api/<resource>`. Unless otherwise noted, all requests must
be authenticated using HTTP basic authentication.

## Resources

* artist
    * GET: artist info, no auth
        * mbid

* artists
    * GET: list of all artists for the user (mbid, name, sort_name,
      disambiguation)
    * PUT: follow a new artist, return the artist info or the list of artists if
      multiple artists match the name
        * mbid, or
        * name
    * DELETE: unfollow artists
        * mbid: comma-separated list of mbids

* release
    * GET: release group info (artist, mbid, name, type, date), no auth
        * mbid

* releases
    * GET: list of release groups, sorted by release date. Will also work with
      no auth, in this case user's release type filters won't apply.
        * limit, max 100
        * offset
        * artist: optional artist mbid, if set filter by this artist.

* user
    * GET: return user info and settings
    * POST: create and return a new user, no auth
        * email
        * password
        * activate: 1 to send an activation email
    * PUT: update user info and settings
    * DELETE: delete the user and all their data
