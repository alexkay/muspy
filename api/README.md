# muspy API documentation

A draft specification of the muspy API.

Use `http://muspy.com/api/1/<resource>`. Unless otherwise noted, requests must
be authenticated using HTTP basic authentication.

## Resources

* artist/<mbid>
    * GET: artist info, no auth

* artists/<userid>[/<mbid>]
    * GET: list of all artists for the user (mbid, name, sort_name,
      disambiguation)
    * PUT: follow a new artist, return the artist info or the list of artists if
      multiple artists match the name
        * mbid, or
        * name
    * DELETE: unfollow an artist, <mbid> is required

* release/<mbid>
    * GET: release group info (artist, mbid, name, type, date), no auth

* releases[/<userid>]
    * GET: list of release groups, sorted by release date. If <userid> is not
      supplied, the request does not have to be authenticated. In this case, the
      call will return release groups starting from today for all artists and
      the user's release type filters won't apply.
        * limit, max 100
        * offset
        * artist: optional artist mbid, if set filter by this artist.

* user[/<userid>]
    * GET: return user info and settings, <userid> is optional, auth is not.
    * POST: create and return a new user, no auth
        * email
        * password
        * activate: 1 to send an activation email
    * PUT: update user info and settings
    * DELETE: delete the user and all their data
