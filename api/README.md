# muspy API documentation

This is a draft specification of the muspy API.

Use `http://muspy.com/api/<resource>`. Unless otherwise noted, all requests must
be authenticated using HTTP basic authentication.

## Resources

* artist
  * GET: artist info, no auth
    * mbid

* artists
  * GET: list of all artists (mbid, name, sort_name, disambiguation)
  * PUT: add a new artist, return the artist info or the list of matching artists
    * mbid, or
    * name
  * DELETE: unfollow artists
    * list of mbids

* release
  * GET: release group info (artist, mbid, name, type, date), no auth

* releases
  * GET: list of release groups, sorted by release date
    * limit, max 100
    * offset
    * artist: optional artist mbid, if set filter by this artist. Will also work
      with no auth, in this case user's release type filters won't apply.

* user
  * GET: return user info and settings
  * POST: create and return a new user, no auth
    * email
    * password
    * activate: 1 to send an activation email
  * PUT: update user info and settings
  * DELETE: delete the user and all their data
