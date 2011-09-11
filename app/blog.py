articles = {
    'about': {'title': 'About Us'},
    'contact': {'title': 'Contact'},
    'faq': {'title': 'Frequently Asked Questions'},
    'first-post': {'date': '2008-10-25', 'title': 'First Post'},
    'starring-releases': {'date': '2008-10-26', 'title': 'Starring Releases'},
    'import-from-last.fm': {'date': '2008-10-31', 'title': 'Importing Artists From Last.fm'},
    'filter-albums': {'date': '2008-11-15', 'title': 'Filter Albums By Type'},
}

_posts = []
def get_posts():
    global _posts
    if _posts:
        return _posts

    for slug in articles:
        post = articles[slug].copy()
        if not 'date' in post:
            continue
        post['slug'] = slug
        post['template_name'] = 'articles/%s-%s.html' % (post['date'], slug)
        post['updated'] = post['date'] + 'T00:00:00Z';
        _posts.append(post)
    _posts.sort(key=lambda post: post['date'], reverse=True)
    return _posts
