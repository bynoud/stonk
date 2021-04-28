
import requests, bs4
from bs4 import BeautifulSoup

r = requests.get('http://f319.com')
soup = BeautifulSoup(r.text, 'html.parser')
nav = soup.select('div.pageNavLinkGroup div.PageNav')
lastPage = int(nav[0]['data-last'])

def _getSoup(url):
    r = requests.get('http://f319.com/%s'%url)
    if r.status_code != 200:
        raise Exception('Get "%s" return status "%s"' % (url, r.status_code))
    return bs4.BeautifulSoup(r.text)

_DB = {
    'lastTime': 0,
    'ignorePostId': 'thread-1134567 thread-13691 thread-31472'.split(),
    'posts': {},
}

class Post:
    def __init__(self, postEle):
        self.pid = postEle['id']
        self.updateTime = int(postEle.select('.lastPostInfo .DateTime')[0]['data-time'])
        self.title = item.select('.title a')[0].text
        self.link = item.select('.title a')[0]['href']
        self.comment = int(item.select('.stats .major')[0].text.strip().replace('.',''))
        self.view = int(item.select('.stats .minor')[0].text.strip().replace('.',''))


class F319:
    def __init__(self):
        self._lastTime = 0
        self._ignorePostId = 'thread-1134567 thread-13691 thread-31472'.split()
        self._posts = {}

    def getPost(self, pid) -> Post:
        return None if pid not in self._posts else self._posts[pid]

    def getUpdatedPosts(self):
        soup = _getSoup('')
        items = soup.select('ol.discussionListItems li')
        for item in items:
            itemId = item['id']
            if itemId in self._ignorePostId:
                continue

            updateTime = int(item.select('.lastPostInfo .DateTime')[0]['data-time'])
            post = self.getPost(itemId)
            if post is None:
                post = Post(item)
                self._posts[post.pid] = post


#------------ List page
# disc = soup.select('div.mainContent div.discussionList')
items = soup.select('ol.discussionListItems li')
# ID: item['id']
# title: item.select('.title a')[0].text
# link: item.select('.title a')[0]['href'] -> threads/noi-qui-dien-dan-f319-com-topic-giai-quyet-thac-mac-va-yeu-cau.1134567/
# comment cnt: int(item.select('.stats .major')[0].text.strip().replace('.',''))
# view cnt: int(item.select('.stats .minor')[0].text.strip().replace('.',''))
# last Updater: item.select('.lastPostInfo .username')[0].text
# last update time: int(item.select('.lastPostInfo .DateTime')[0]['data-time'])

# ignore these ID (just general info, but very long thread): thread-1134567 thread-13691 thread-31472

#---------- detail Page
r = requests.get('http://f319.com/threads/hst-fl-lieu-co-con-hap-dan.1605349/')
post = BeautifulSoup(r.text, 'html.parser')
int(post.select('.pageNavLinkGroup .PageNav')[0]['data-last'])

mess = post.select('#messageList li')
mes = mess[0]
# id: mes['id']
# date: mes.select('.datePermalink')[0].text -> '17/04/2021, 11:07'
# likes: len(mes.select('.LikeText .username')) + int(mes.select('.LikeText .OverlayTrigger')[0].text.split()[0]) (if existed)
# Text: ''.join([x for x in mes.select('.messageContent .messageText')[0] if isinstance(x, bs4.element.NavigableString)])
