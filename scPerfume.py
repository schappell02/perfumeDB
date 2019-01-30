from bs4 import BeautifulSoup
import urllib2
import re
import copy
import sqlite3
import pickle



def getReviewURL(startURL='https://www.bpal.org/forum/3-reviews/',savePath=None):

    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(startURL,headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page,'html.parser')

    list_nex = []
    for tmp in soup.findAll('a',attrs={'href':re.compile('^https://www.bpal.org/forum')}):
        tlink = tmp.get('href')
        if not tlink.startswith('https://www.bpal.org/forum/47-') and not tlink.startswith('https://www.bpal.org/forum/3-') and tlink not in list_nex:
            list_nex.append(tlink)

    list_rev = []
    for tmp in list_nex:
        req = urllib2.Request(tmp,headers=hdr)
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page,'html.parser')
        for link in soup.findAll('a',attrs={'href':re.compile('^https://www.bpal.org/')}):
            tlink = link.get('href')
            if tlink.startswith('https://www.bpal.org/forum/') and 'sortby' not in tlink and tlink not in list_nex and not tlink.startswith('https://www.bpal.org/forum/47-') and not tlink.startswith('https://www.bpal.org/forum/3-') and not tlink.endswith('.xml/'):
                list_nex.append(tlink)
                
            elif tlink.startswith('https://www.bpal.org/topic/') and tlink not in list_rev and not tlink.endswith('Comment') and '/?page=' not in tlink:
                list_rev.append(tlink)

    if savePath != None:
        with open(savePath,'wb') as fp:
            pickle.dump(list_rev,fp)
    else:
        return list_rev




def getScentInfo(scent_url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib2.Request(scent_url,headers=hdr)
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page,'html.parser')
    
        ret_title = soup.find('meta',attrs={'property':'og:title'})['content']
        tmp_array = re.findall(r'.+? -',soup.title.text)
        ret_colle = tmp_array[1][1:-2]
        try:
            ret_tags = soup.find('meta',attrs={'name':'keywords'})['content']
        except TypeError:
            ret_tags = ''
        try:
            tmp_str = soup.select('div[style*="background-color:transparent"]')[0].find_all('strong')[-1].text
        except AttributeError:
            tmp_str = soup.select('div[style*="background-color:transparent"]')[0].text
        except IndexError:
            tmp_str = ''
        try:
            ret_descr = re.findall(r':.+',tmp_str)[0][2:]
        except IndexError:
            ret_descr = tmp_str
    
        return ret_title, ret_colle, ret_tags, ret_descr 

    except HTTPError:
        return '','','',''


